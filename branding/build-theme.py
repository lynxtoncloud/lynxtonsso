#!/usr/bin/env python3
"""Package only the LynxtonCloud theme; no Keycloak/React rebuild required."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=root / "branding/target/lynxton-theme.jar"
    )
    args = parser.parse_args()
    theme = root / "themes/src/main/resources/theme/lynxton"
    files = sorted(path for path in theme.rglob("*") if path.is_file())
    kinds = ("login", "account", "admin", "common")
    if not files or any(not (theme / kind / "theme.properties").is_file() for kind in kinds):
        parser.error("LynxtonCloud theme sources are missing or incomplete")
    output = args.output.resolve()
    if output.is_relative_to(theme):
        parser.error("Output must be outside the theme source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"themes": [{"name": "lynxton", "types": list(kinds)}]}

    def write(archive, name, data):
        entry = ZipInfo(name, date_time=(2026, 9, 29, 0, 0, 0))
        entry.compress_type = ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, data)

    with ZipFile(output, "w") as archive:
        write(archive, "META-INF/keycloak-themes.json", json.dumps(manifest, indent=2) + "\n")
        for path in files:
            name = "theme/lynxton/" + path.relative_to(theme).as_posix()
            data = path.read_bytes()
            write(archive, name, data)
            # Older servers use region-based Chinese bundles; keep one source.
            if path.name == "messages_zh_Hans.properties":
                write(archive, name.replace("messages_zh_Hans", "messages_zh_CN"), data)
    print(f"Packaged {len(files)} theme files: {output}")


if __name__ == "__main__":
    main()
