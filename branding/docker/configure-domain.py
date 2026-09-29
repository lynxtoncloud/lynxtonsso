#!/usr/bin/env python3
"""Configure the SSO HTTPS entry in the existing Docker Desktop ingress."""

import argparse
from pathlib import Path
import secrets
import subprocess
import tempfile

DIRECTORY = Path(__file__).resolve().parent
DEFAULT_CA = DIRECTORY.parents[2] / "LynxPilot/.local/k8s"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ca-cert", type=Path, default=DEFAULT_CA / "generated/local-ca.crt")
    parser.add_argument("--ca-key", type=Path, default=DEFAULT_CA / "secrets/local-ca.key")
    args = parser.parse_args()
    if not args.ca_cert.is_file() or not args.ca_key.is_file():
        parser.error("Provide the existing trusted local CA certificate and key")
    kubectl = ["kubectl", "--context", "docker-desktop"]
    run(*kubectl, "get", "service", "ingress-nginx-controller", "-n", "ingress-nginx",
        stdout=subprocess.DEVNULL)
    directory = DIRECTORY / ".local/tls"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    certificate, key = directory / "tls.crt", directory / "tls.key"
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        staging = Path(temporary)
        config = staging / "extensions.cnf"
        config.write_text("subjectAltName=DNS:login.lynxtoncloud.com\nextendedKeyUsage=serverAuth\n")
        run("openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(staging / "tls.key"), "-out", str(staging / "tls.csr"),
            "-subj", "/CN=login.lynxtoncloud.com", stderr=subprocess.DEVNULL)
        run("openssl", "x509", "-req", "-in", str(staging / "tls.csr"),
            "-CA", str(args.ca_cert), "-CAkey", str(args.ca_key),
            "-set_serial", "0x" + secrets.token_hex(16), "-days", "365", "-sha256",
            "-extfile", str(config), "-out", str(staging / "tls.crt"),
            stderr=subprocess.DEVNULL)
        run("openssl", "verify", "-CAfile", str(args.ca_cert), str(staging / "tls.crt"))
        (staging / "tls.key").chmod(0o600)
        (staging / "tls.key").replace(key)
        (staging / "tls.crt").replace(certificate)
    namespace = run(*kubectl, "create", "namespace", "lynxtonsso", "--dry-run=client",
                    "-o", "json", capture_output=True).stdout
    run(*kubectl, "apply", "-f", "-", input=namespace)
    secret = run(*kubectl, "-n", "lynxtonsso", "create", "secret", "tls", "lynxtonsso-local-tls",
                 "--cert", str(certificate), "--key", str(key), "--dry-run=client",
                 "-o", "json", capture_output=True).stdout
    run(*kubectl, "apply", "-f", "-", input=secret)
    run(*kubectl, "apply", "-f", str(DIRECTORY / "ingress.yaml"))
    print("本地 HTTPS 入口已配置：https://login.lynxtoncloud.com")
    print("需将 login.lynxtoncloud.com 在本机 hosts 解析为 127.0.0.1；不修改公网 DNS。")


if __name__ == "__main__":
    main()
