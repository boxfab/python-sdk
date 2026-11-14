#!/usr/bin/env python3
"""Check that a release tag is `v<version>` for the version in pyproject.toml.

    python scripts/check_release_tag.py v0.1.0a1                            # boxfab
    python scripts/check_release_tag.py --project desktop desktop-v0.1.0a1  # boxfab-desktop

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


def check(tag: str, version: str, prefix: str = "v") -> str | None:
    if not VERSION_RE.fullmatch(version):
        return (
            f"pyproject version {version!r} is not a canonical PEP 440 public version"
        )
    if not tag.startswith(prefix):
        return f"tag {tag!r} must start with {prefix!r}"
    if tag[len(prefix) :] != version:
        return f"tag {tag!r} does not match pyproject version {version!r} (expected '{prefix}{version}')"
    return None


def main() -> int:
    args = sys.argv[1:]
    project_dir, prefix = ROOT, "v"
    if args[:1] == ["--project"] and len(args) == 3:
        project_dir, prefix, args = ROOT / args[1], f"{args[1]}-v", args[2:]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    version = tomllib.loads((project_dir / "pyproject.toml").read_text())["project"][
        "version"
    ]
    err = check(args[0], version, prefix)
    if err:
        print(f"release tag check failed: {err}", file=sys.stderr)
        return 1
    print(f"release tag {args[0]} matches version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
