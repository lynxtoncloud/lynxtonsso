#!/usr/bin/env python3
"""Check the actual SSO login pages for legacy branding, without signing in."""

import argparse
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import secrets
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import urlopen


class LoginPage(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.headers = []
        self.header_text = []
        self.branded = False
        self.legacy = False
        self.login_form = False
        self.styles = []
        self.favicons = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        in_header = any(self.headers) or "pf-v5-c-login__header" in classes or attrs.get("id") == "kc-header"
        if tag not in self.VOID:
            self.headers.append(in_header)
        if in_header and "lynxton-brand-logo" in classes:
            self.branded = True
        if "kc-logo-text" in classes:
            self.legacy = True
        if tag in {"img", "svg", "image"} and re.search(
            r"keycloak|kc-logo", " ".join(value or "" for value in attrs.values()), re.I
        ):
            self.legacy = True
        if tag == "form" and attrs.get("id") == "kc-form-login":
            self.login_form = True
        if tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            href = attrs.get("href")
            if href and "stylesheet" in rel:
                self.styles.append(href)
            if href and "icon" in rel:
                self.favicons.append(href)

    def handle_endtag(self, tag):
        if tag not in self.VOID and self.headers:
            self.headers.pop()

    def handle_data(self, data):
        if any(self.headers):
            self.header_text.append(data)


class CheckFailure(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def check(base, context, realm, client, callback):
    origin = urlsplit(base)[:2]

    def fetch(url):
        require(urlsplit(url)[:2] == origin, "resource or endpoint has an unexpected origin")
        with urlopen(url, context=context, timeout=15) as response:
            require(urlsplit(response.url)[:2] == origin, "response redirected to an unexpected origin")
            return response.read(), response.url

    realm_url = base + "/realms/" + realm
    discovery, _ = fetch(realm_url + "/.well-known/openid-configuration")
    config = json.loads(discovery)
    require(config.get("issuer") == realm_url, "discovery issuer does not match the realm")
    endpoint = config.get("authorization_endpoint")
    require(endpoint == realm_url + "/protocol/openid-connect/auth", "discovery authorization endpoint is unexpected")
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    query = urlencode({
        "client_id": client, "redirect_uri": base + callback,
        "response_type": "code", "scope": "openid", "prompt": "login",
        "state": secrets.token_urlsafe(24), "nonce": secrets.token_urlsafe(24),
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    html, page_url = fetch(endpoint + "?" + query)
    page = LoginPage()
    page.feed(html.decode("utf-8"))
    require(page.login_form, "OIDC request did not return a login form")
    require(page.branded, "LynxtonCloud header branding is missing")
    require(not page.legacy, "legacy Keycloak logo element is present")
    require(not re.search(r"keycloak", " ".join(page.header_text), re.I), "legacy Keycloak text is present in the header")
    require(page.favicons, "favicon link is missing")
    sources = Path(__file__).resolve().parents[1] / "themes/src/main/resources/theme/lynxton/common/resources/img"
    for href in page.favicons:
        image, _ = fetch(urljoin(page_url, href))
        require(image == (sources / "favicon.ico").read_bytes(), "favicon does not match the LynxtonCloud asset")
    logo_urls = []
    for href in page.styles:
        if not urlsplit(href).path.endswith("/css/login.css"):
            continue
        css, css_url = fetch(urljoin(page_url, href))
        rule = re.search(r"\.lynxton-brand-logo\s*\{([^}]+)\}", css.decode("utf-8"))
        if rule:
            image = re.search(r"url\([\"']?([^\"')]+)[\"']?\)", rule.group(1))
            if image:
                logo_urls.append(urljoin(css_url, image.group(1)))
    require(logo_urls, "LynxtonCloud logo resource is missing from the login stylesheet")
    for url in logo_urls:
        image, _ = fetch(url)
        require(image == (sources / "logo.png").read_bytes(), "logo does not match the LynxtonCloud asset")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:58080")
    parser.add_argument("--ca-file", type=Path, help="CA certificate for a local HTTPS environment")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment or parsed.username:
        parser.error("--base-url must be an HTTP(S) URL without credentials, query, or fragment")
    context = ssl.create_default_context(cafile=args.ca_file)
    failed = False
    for realm, client, callback in (
        ("master", "security-admin-console", "/admin/master/console/"),
        ("lynxton-preview", "account-console", "/realms/lynxton-preview/account/"),
    ):
        try:
            check(base, context, realm, client, callback)
            print(f"PASS {realm}/{client}: login branding, logo and favicon")
        except CheckFailure as error:
            print(f"FAIL {realm}/{client}: {error}")
            failed = True
        except HTTPError as error:
            print(f"FAIL {realm}/{client}: HTTP {error.code}")
            failed = True
        except URLError:
            print(f"FAIL {realm}/{client}: connection or TLS verification failed")
            failed = True
        except (ValueError, OSError, KeyError):
            print(f"FAIL {realm}/{client}: branding, resource or discovery validation failed")
            failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
