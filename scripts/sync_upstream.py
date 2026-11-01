#!/usr/bin/env python3
"""Regenerate boxfab/ and tests/ from an upstream E2B Python SDK release.

    python scripts/sync_upstream.py                    # clone the pinned tag from UPSTREAM.md
    python scripts/sync_upstream.py --src <checkout>   # use an existing E2B monorepo checkout

The output is fully derived: never hand-edit boxfab/ or tests/; change a rule here instead and
re-run. Every rule asserts how often it matched, so when upstream moves code around the sync
fails loudly instead of silently shipping an e2b default.

What the rules do (see UPSTREAM.md for the reasoning):
  1. package e2b -> boxfab (directory, imports, module paths in strings)
  2. every E2B_* environment variable the SDK reads -> BOXFAB_* (no E2B_* fallback at all)
  3. default domain e2b.app -> DEFAULT_DOMAIN below
  4. distribution metadata and User-Agent -> boxfab
  5. client class E2B -> BoxFab (E2B kept as an alias for drop-in porting)
Shell variables used inside sandboxes (E2B_HEREDOC_*, E2B_EXIT) and the list of E2B-hosted
sandbox domains (sandbox_domains.py) are deliberately left alone.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_REPO = "https://github.com/e2b-dev/E2B.git"
SDK_SUBDIR = "packages/python-sdk"

DEFAULT_DOMAIN = "sandd.contextfab.io"
DASHBOARD_URL = "https://dashboard.sandd.contextfab.io"

# Environment variables the SDK reads. Renamed everywhere (code, docstrings, tests).
ENV_VARS = [
    "API_KEY",
    "DOMAIN",
    "DEBUG",
    "API_URL",
    "SANDBOX_URL",
    "ACCESS_TOKEN",
    "HTTP_VERSION",
    "CONNECTION_RETRIES",
    "KEEPALIVE_EXPIRY",
    "MAX_KEEPALIVE_CONNECTIONS",
    "MAX_CONNECTIONS",
    "VOLUME_API_URL",
]
# E2B_* names that are not SDK configuration (shell variables inside the sandbox).
KNOWN_NON_CONFIG = re.compile(r"\bE2B_(HEREDOC_[A-Z0-9_]*|EXIT)\b")

# (file relative to the output tree, old, new, expected count)
EXACT = [
    (
        "boxfab/api/metadata.py",
        'metadata.version("e2b")',
        'metadata.version("boxfab")',
        2,
    ),
    ("boxfab/api/metadata.py", '"publisher": "e2b"', '"publisher": "boxfab"', 1),
    ("boxfab/connection_config.py", 'or "e2b.app"', f'or "{DEFAULT_DOMAIN}"', 1),
    ("boxfab/volume/connection_config.py", 'or "e2b.app"', f'or "{DEFAULT_DOMAIN}"', 1),
    (
        "boxfab/volume/connection_config.py",
        "`BOXFAB_DOMAIN` or `e2b.app`",
        f"`BOXFAB_DOMAIN` or `{DEFAULT_DOMAIN}`",
        1,
    ),
    (
        "boxfab/connection_config.py",
        'f"e2b-python-sdk/{package_version}"',
        'f"boxfab-python-sdk/{package_version}"',
        1,
    ),
    (
        "boxfab/volume/connection_config.py",
        'f"e2b-python-sdk/{package_version}"',
        'f"boxfab-python-sdk/{package_version}"',
        1,
    ),
    (
        "boxfab/api/__init__.py",
        "please visit the API Keys tab at https://e2b.dev/dashboard?tab=keys to get your API key. ",
        f"get one from your BoxFab administrator (keys are shown at {DASHBOARD_URL}). ",
        1,
    ),
    # Client class: BoxFab is the name, E2B stays importable as an alias.
    ("boxfab/client.py", "class E2BClientParams(", "class BoxFabClientParams(", 1),
    ("boxfab/client.py", "class E2B:", "class BoxFab:", 1),
    ("boxfab/client.py", "Unpack[E2BClientParams]", "Unpack[BoxFabClientParams]", 1),
    ("boxfab/client.py", "from boxfab import E2B\n", "from boxfab import BoxFab\n", 1),
    (
        "boxfab/client.py",
        'client = E2B(api_key="e2b_...", domain="e2b.dev")',
        f'client = BoxFab(api_key="e2b_...", domain="{DEFAULT_DOMAIN}")',
        1,
    ),
    (
        "boxfab/__init__.py",
        "from .client import E2B, E2BClientParams",
        "from .client import BoxFab, BoxFabClientParams, E2B, E2BClientParams",
        1,
    ),
    (
        "boxfab/__init__.py",
        '    "E2B",\n',
        '    "BoxFab",\n    "BoxFabClientParams",\n    "E2B",\n',
        1,
    ),
]

# Upstream tests whose expectations encode E2B's defaults; adjusted to ours.
TEST_EXACT = [
    (
        "tests/test_connection_config.py",
        'config.api_url == "https://api.e2b.app"',
        f'config.api_url == "https://api.{DEFAULT_DOMAIN}"',
        1,
    ),
    (
        "tests/test_volume_connection_config.py",
        'config.api_url == "https://api.e2b.app"',
        f'config.api_url == "https://api.{DEFAULT_DOMAIN}"',
        1,
    ),
    (
        "tests/test_connection_config.py",
        '.startswith("e2b-python-sdk/")',
        '.startswith("boxfab-python-sdk/")',
        1,
    ),
]


def run(*cmd, **kw):
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True, **kw)


def pinned_ref() -> str:
    text = (ROOT / "UPSTREAM.md").read_text()
    m = re.search(r"^- Commit: `([0-9a-f]{40})`", text, re.M)
    if not m:
        sys.exit("UPSTREAM.md has no '- Commit: `<sha>`' line")
    return m.group(1)


def fetch(ref: str, dest: Path) -> Path:
    run(
        "git",
        "clone",
        "-q",
        "--filter=blob:none",
        "--no-checkout",
        UPSTREAM_REPO,
        str(dest),
    )
    run("git", "-C", str(dest), "checkout", "-q", ref)
    return dest


def module_names(pkg: Path):
    # Upstream uses namespace packages (several subpackages have no __init__.py).
    names = [
        p.stem if p.is_file() else p.name
        for p in pkg.iterdir()
        if (p.is_file() and p.suffix == ".py")
        or (p.is_dir() and p.name != "__pycache__")
    ]
    return sorted(n for n in names if n != "__init__")


def rewrite(path: Path, mods):
    text = path.read_text()
    orig = text
    mod_alt = "|".join(map(re.escape, mods))
    text = re.sub(rf"\be2b(?=\.(?:{mod_alt})\b)", "boxfab", text)
    text = re.sub(r"\bfrom e2b import\b", "from boxfab import", text)
    text = re.sub(r"^(\s*)import e2b$", r"\1import boxfab", text, flags=re.M)
    text = re.sub(r"\bimport e2b as\b", "import boxfab as", text)
    for name in ENV_VARS:
        text = re.sub(rf"\bE2B_{name}\b", f"BOXFAB_{name}", text)
    if text != orig:
        path.write_text(text)


def apply_exact(rules, required: bool):
    for rel, old, new, expected in rules:
        p = ROOT / rel
        if not p.exists():
            if required:
                sys.exit(f"rule target missing: {rel}")
            continue
        text = p.read_text()
        n = text.count(old)
        if expected is not None and n != expected:
            sys.exit(f"{rel}: expected {expected} x {old!r}, found {n}")
        if n == 0 and required:
            sys.exit(f"{rel}: {old!r} not found")
        p.write_text(text.replace(old, new))


CLIENT_ALIAS = """

# Upstream names, kept so code written for e2b ports by changing only the import.
E2B = BoxFab
E2BClientParams = BoxFabClientParams
"""


def audit():
    problems = []
    for p in list((ROOT / "boxfab").rglob("*.py")):
        text = p.read_text()
        rel = p.relative_to(ROOT)
        for m in re.finditer(r"\bE2B_[A-Z0-9_]+\b", text):
            if not KNOWN_NON_CONFIG.fullmatch(m.group(0)):
                problems.append(f"{rel}: unrenamed {m.group(0)}")
        if re.search(r"\b(from|import) e2b\b(?!_)", text):
            problems.append(f"{rel}: e2b import left")
        if re.search(r"""os\.(getenv|environ)[^\n]*["']E2B""", text):
            problems.append(f"{rel}: reads an E2B_* variable")
    if problems:
        sys.exit("audit failed:\n  " + "\n  ".join(problems))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--src", type=Path, help="existing E2B monorepo checkout (at the pinned commit)"
    )
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        src = args.src or fetch(pinned_ref(), Path(tmp) / "E2B")
        sdk = src / SDK_SUBDIR
        if not (sdk / "e2b").is_dir():
            sys.exit(f"{sdk}/e2b not found")

        for d in ("boxfab", "tests"):
            shutil.rmtree(ROOT / d, ignore_errors=True)
        shutil.copytree(
            sdk / "e2b", ROOT / "boxfab", ignore=shutil.ignore_patterns("__pycache__")
        )
        shutil.copytree(
            sdk / "tests", ROOT / "tests", ignore=shutil.ignore_patterns("__pycache__")
        )
        shutil.copy2(sdk / "pytest.ini", ROOT / "pytest.ini")
        shutil.copy2(sdk / "LICENSE", ROOT / "LICENSE-E2B")
        shutil.copy2(sdk / "CHANGELOG.md", ROOT / "CHANGELOG-E2B.md")

    mods = module_names(ROOT / "boxfab")
    for p in (
        list((ROOT / "boxfab").rglob("*.py"))
        + list((ROOT / "tests").rglob("*.py"))
        + [ROOT / "pytest.ini"]
    ):
        rewrite(p, mods)
    apply_exact(EXACT, required=True)
    client = ROOT / "boxfab" / "client.py"
    client.write_text(client.read_text().rstrip("\n") + "\n" + CLIENT_ALIAS)
    apply_exact(TEST_EXACT, required=True)
    audit()
    print("sync OK", file=sys.stderr)


if __name__ == "__main__":
    main()
