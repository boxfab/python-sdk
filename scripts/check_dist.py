#!/usr/bin/env python3
"""Validate the built distributions before they can be published.

    python scripts/check_dist.py dist/

Checks: exactly one wheel and one sdist named for the pyproject name and version; metadata
name, version and license; the license file present; no files outside the expected layout;
no credentials, private keys or internal infrastructure details in any file. Stdlib only.
"""

import email.parser
import os
import re
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSES = ("LICENSE",)
SDIST_TOP = {
    "boxfab",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "pyproject.toml.orig",
    "PKG-INFO",
}

# Placeholder keys used by upstream tests and docs look like e2b_000…; real keys are random hex.
SECRET_PATTERNS = {
    "API key": re.compile(rb"\be2b_(?!0{40}\b)[0-9a-f]{40}\b"),
    "private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(
        rb"\b(gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,})"
    ),
    "PyPI token": re.compile(rb"\bpypi-AgE[A-Za-z0-9_-]{20,}"),
    "AWS key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "private IPv4 address": re.compile(
        rb"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
    ),
    "Tailscale host name": re.compile(rb"\.ts\.net\b"),
}
# Upstream documentation examples that match a pattern above but are not ours.
ALLOWED_LITERALS = [b"192.168.1.100"]
# Site-specific names (host names, tailnet, ...) are not kept in this public repository. CI passes
# them as a regex in the DIST_EXTRA_DENY repository secret (masked in logs); locally, export it.
EXTRA = os.environ.get("DIST_EXTRA_DENY", "").strip()
if EXTRA:
    SECRET_PATTERNS["site-specific name (DIST_EXTRA_DENY)"] = re.compile(
        EXTRA.encode(), re.I
    )


def fail(errors):
    print("distribution check failed:\n  " + "\n  ".join(errors), file=sys.stderr)
    sys.exit(1)


def scan(name: str, data: bytes, errors):
    for lit in ALLOWED_LITERALS:
        data = data.replace(lit, b"")
    for label, rx in SECRET_PATTERNS.items():
        if rx.search(data):
            errors.append(f"{name}: looks like it contains {label}")


def check_metadata(raw: bytes, where: str, name: str, version: str, errors):
    msg = email.parser.BytesParser().parsebytes(raw)
    if msg["Name"] != name:
        errors.append(f"{where}: Name {msg['Name']!r} != {name!r}")
    if msg["Version"] != version:
        errors.append(f"{where}: Version {msg['Version']!r} != {version!r}")
    if msg["License-Expression"] != "MIT":
        errors.append(
            f"{where}: License-Expression {msg['License-Expression']!r} != 'MIT'"
        )
    if sorted(msg.get_all("License-File") or []) != sorted(LICENSES):
        errors.append(
            f"{where}: License-File {msg.get_all('License-File')} != {list(LICENSES)}"
        )


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    name, version = project["name"], project["version"]
    errors = []

    files = sorted(p.name for p in dist.iterdir() if not p.name.startswith("."))
    want = [f"{name}-{version}-py3-none-any.whl", f"{name}-{version}.tar.gz"]
    if sorted(files) != sorted(want):
        fail([f"{dist}: expected exactly {want}, found {files}"])

    whl = zipfile.ZipFile(dist / want[0])
    info = f"{name}-{version}.dist-info/"
    for n in whl.namelist():
        if not (n.startswith(f"{name}/") or n.startswith(info)):
            errors.append(f"wheel: unexpected file {n}")
        scan(f"wheel:{n}", whl.read(n), errors)
    for lic in LICENSES:
        if f"{info}licenses/{lic}" not in whl.namelist():
            errors.append(f"wheel: missing {info}licenses/{lic}")
    check_metadata(whl.read(f"{info}METADATA"), "wheel METADATA", name, version, errors)

    prefix = f"{name}-{version}/"
    with tarfile.open(dist / want[1]) as sd:
        members = [m for m in sd.getmembers() if m.isfile()]
        names = {m.name for m in members}
        for m in members:
            if not m.name.startswith(prefix):
                errors.append(f"sdist: file outside {prefix}: {m.name}")
                continue
            top = m.name[len(prefix) :].split("/")[0]
            if top not in SDIST_TOP:
                errors.append(f"sdist: unexpected file {m.name}")
            scan(f"sdist:{m.name}", sd.extractfile(m).read(), errors)
        for lic in LICENSES:
            if prefix + lic not in names:
                errors.append(f"sdist: missing {lic}")
        check_metadata(
            sd.extractfile(prefix + "PKG-INFO").read(),
            "sdist PKG-INFO",
            name,
            version,
            errors,
        )

    if errors:
        fail(errors)
    print(
        f"{want[0]} ({len(whl.namelist())} files) and {want[1]} ({len(members)} files): OK"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
