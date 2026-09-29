#!/usr/bin/env python3
"""Build the local theme and start an isolated Docker Compose test environment."""

import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[1]
ENV_FILE = DIRECTORY / ".env"


def prepare_environment():
    # Reuse passwords after restart so the persistent database remains accessible.
    if not ENV_FILE.exists():
        values = {"SSO_PORT": "58080", "SSO_PUBLIC_URL": "https://login.lynxtoncloud.com"}
        for name in ("SSO_ADMIN_PASSWORD", "SSO_TEST_PASSWORD", "SSO_DB_PASSWORD"):
            values[name] = secrets.token_urlsafe(24)
        with open(ENV_FILE, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in values.items()))
    return dict(
        line.split("=", 1)
        for line in ENV_FILE.read_text().splitlines()
        if line and not line.startswith("#")
    )


def main():
    values = prepare_environment()
    public = os.environ.get("SSO_PUBLIC_URL", values.get("SSO_PUBLIC_URL", "https://login.lynxtoncloud.com")).rstrip("/")
    url = urlsplit(public)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment or url.path:
        raise SystemExit("SSO_PUBLIC_URL 必须是不含路径和凭据的 HTTP(S) 入口地址")
    if url.hostname == "login.lynxtoncloud.com":
        try:
            addresses = socket.getaddrinfo(url.hostname, url.port or 443)
            local = all(ipaddress.ip_address(item[4][0]).is_loopback for item in addresses)
        except socket.gaierror:
            local = False
        if not local:
            raise SystemExit("请先在 hosts 中配置 127.0.0.1 login.lynxtoncloud.com；服务尚未变更。")
    imports = DIRECTORY / ".local/import"
    imports.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DIRECTORY / "lynxton-preview-realm.json", imports / "lynxton-preview-realm.json")
    subprocess.run([sys.executable, str(ROOT / "branding/build-theme.py")], check=True)
    compose = [
        "docker", "compose", "--env-file", str(ENV_FILE),
        "-f", str(DIRECTORY / "compose.yaml"),
    ]
    subprocess.run(compose + ["up", "-d", "--wait", "postgres"], check=True)
    # Recreate only Keycloak to load a freshly built image, preserving the database.
    subprocess.run(compose + [
        "up", "-d", "--build", "--wait", "--wait-timeout", "240",
        "--no-deps", "--force-recreate", "keycloak",
    ], check=True)
    port = os.environ.get("SSO_PORT", values.get("SSO_PORT", "58080"))
    base = f"http://localhost:{port}"
    password = os.environ.get("SSO_ADMIN_PASSWORD", values["SSO_ADMIN_PASSWORD"])
    request = Request(
        base + "/realms/master/protocol/openid-connect/token",
        data=urlencode({
            "grant_type": "password", "client_id": "admin-cli",
            "username": "admin", "password": password,
        }).encode(),
    )
    with urlopen(request, timeout=15) as response:
        token = json.load(response)["access_token"]
    request = Request(
        base + "/admin/realms/master", method="PUT",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        data=json.dumps({
            "loginTheme": "lynxton", "accountTheme": "lynxton", "adminTheme": "lynxton",
            "internationalizationEnabled": True,
            "supportedLocales": ["en", "zh-CN"], "defaultLocale": "zh-CN",
            "displayName": "灵通云 · 本地管理",
            "displayNameHtml": "",
        }).encode(),
    )
    with urlopen(request, timeout=15):
        pass
    print(f"账户中心：{public}/realms/lynxton-preview/account/")
    print(f"管理控制台：{public}/admin/master/console/")
    print(f"测试用户 test-user / 管理员 admin；本机密码文件：{ENV_FILE}")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, HTTPError) as error:
        raise SystemExit(f"启动或初始化失败：{error}；请检查 Compose 日志。") from None
