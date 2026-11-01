#!/usr/bin/env python3
"""Check that a release tag is `v<version>` for the version in pyproject.toml.

    python scripts/check_release_tag.py v0.1.0a1

Accepts PEP 440 public versions in canonical form, including pre-releases (a/b/rc), post and
dev releases, e.g. v0.1.0a1, v1.2.3, v1.2.3rc2. Exits non-zero with a reason otherwise.
"""

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Canonical PEP 440 public version (no epoch, no local part).
VERSION_RE = re.compile(
    r"(0|[1-9]\d*)(\.(0|[1-9]\d*))*((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?"
)


def check(tag: str, version: str) -> str | None:
    if not VERSION_RE.fullmatch(version):
        return (
            f"pyproject version {version!r} is not a canonical PEP 440 public version"
        )
    if not tag.startswith("v"):
        return f"tag {tag!r} must start with 'v'"
    if tag[1:] != version:
        return f"tag {tag!r} does not match pyproject version {version!r} (expected 'v{version}')"
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    err = check(sys.argv[1], version)
    if err:
        print(f"release tag check failed: {err}", file=sys.stderr)
        return 1
    print(f"release tag {sys.argv[1]} matches version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
