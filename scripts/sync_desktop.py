"""Regenerate desktop/ (the boxfab-desktop package) from the pinned E2B monorepo commit.

Called by scripts/sync_upstream.py with the same checkout as the core SDK, so both packages are
always generated from one upstream commit:

    packages/desktop-python/e2b_desktop -> desktop/boxfab_desktop
    packages/desktop-python/tests       -> desktop/tests, desktop/pytest.ini
    packages/desktop-python/README.md   -> desktop/README.md (from "### 3. Create Desktop Sandbox")

Generated paths are never edited by hand. Every rule asserts how often it matched, so when
upstream moves code the sync fails instead of shipping an upstream default.
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "desktop"
DOMAIN = "boxfab.io"
TEMPLATE_URL = "https://github.com/boxfab/desktop/tree/main/template"

# Environment variables read by the desktop SDK and its tests (the core SDK reads the rest).
ENV_VARS = ["API_KEY", "DOMAIN", "DEBUG", "API_URL", "SANDBOX_URL"]
ENV_RX = re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b")

EXACT = [
    # client class BoxFab; the upstream names stay importable as aliases.
    (
        "boxfab_desktop/client.py",
        "from boxfab import ApiParams, E2BClientParams\n",
        "from boxfab import ApiParams, BoxFabClientParams, E2BClientParams\n",
        1,
    ),
    (
        "boxfab_desktop/client.py",
        "from boxfab import E2B as CoreE2B\n",
        "from boxfab import BoxFab as CoreBoxFab\n",
        1,
    ),
    (
        "boxfab_desktop/client.py",
        "core = CoreE2B(**api_params)",
        "core = CoreBoxFab(**api_params)",
        1,
    ),
    (
        "boxfab_desktop/client.py",
        '__all__ = ["E2B", "E2BClientParams"]',
        '__all__ = ["BoxFab", "BoxFabClientParams", "E2B", "E2BClientParams"]',
        1,
    ),
    ("boxfab_desktop/client.py", "class E2B:", "class BoxFab:", 1),
    (
        "boxfab_desktop/client.py",
        "    E2B client with an explicitly bound connection configuration.",
        "    BoxFab client with an explicitly bound connection configuration.",
        1,
    ),
    (
        "boxfab_desktop/client.py",
        "    from boxfab_desktop import E2B\n",
        "    from boxfab_desktop import BoxFab\n",
        1,
    ),
    (
        "boxfab_desktop/client.py",
        'client = E2B(api_key="e2b_...", domain="e2b.dev")',
        f'client = BoxFab(api_key="e2b_...", domain="{DOMAIN}")',
        1,
    ),
    (
        "boxfab_desktop/client.py",
        "**opts: Unpack[E2BClientParams]",
        "**opts: Unpack[BoxFabClientParams]",
        1,
    ),
    (
        "boxfab_desktop/__init__.py",
        "from .client import E2B, E2BClientParams",
        "from .client import BoxFab, BoxFabClientParams, E2B, E2BClientParams",
        1,
    ),
    # live tests: the template can be overridden (BOXFAB_DESKTOP_TEMPLATE, default `desktop`).
    (
        "tests/conftest.py",
        "sandbox = Sandbox.create(timeout=timeout)",
        'sandbox = Sandbox.create(\n        template=os.getenv("BOXFAB_DESKTOP_TEMPLATE"), timeout=timeout\n    )',
        1,
    ),
]

CLIENT_ALIAS = """

# Upstream name, kept so code written for the upstream package ports by changing only the import.
E2B = BoxFab
"""

README_RULES = [
    (r"\be2b_desktop\b", "boxfab_desktop", 13),
    (r"create an `E2B` client", "create a `BoxFab` client", 1),
    (r"from boxfab_desktop import E2B\n", "from boxfab_desktop import BoxFab\n", 1),
    (
        r'client = E2B\(api_key="e2b_\*\*\*", domain="e2b\.dev"\)',
        f'client = BoxFab(api_key="e2b_***", domain="{DOMAIN}")',
        1,
    ),
    (
        r"Check out the sandbox template's code \[here\]\(https://github\.com/e2b-dev/desktop/tree/main/template\)\.",
        f"BoxFab's template is in [boxfab/desktop]({TEMPLATE_URL}), generated from "
        "[e2b-dev/desktop](https://github.com/e2b-dev/desktop/tree/main/template).",
        1,
    ),
]
README_START = "### 3. Create Desktop Sandbox\n"

# What must not remain in generated code. The `e2b_` API-key prefix is protocol, not branding.
FORBIDDEN = [
    (re.compile(r"\b(from|import) e2b\b(?!_)"), "e2b import"),
    (re.compile(r"\be2b_desktop\b"), "upstream package name"),
    (re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b"), "E2B_* variable"),
    (re.compile(r"e2b\.dev|e2b\.app"), "E2B domain"),
]


def apply_exact(rules):
    for rel, old, new, expected in rules:
        p = OUT / rel
        text = p.read_text()
        n = text.count(old)
        if n != expected:
            sys.exit(f"desktop/{rel}: expected {expected} x {old[:70]!r}, found {n}")
        p.write_text(text.replace(old, new))


def sync(src: Path):
    """Generate desktop/ from `src`, an E2B monorepo checkout at the pinned commit."""
    up = src / "packages/desktop-python"
    if not (up / "e2b_desktop").is_dir():
        sys.exit(f"{up}/e2b_desktop not found")
    for d in ("boxfab_desktop", "tests"):
        shutil.rmtree(OUT / d, ignore_errors=True)
    shutil.copytree(
        up / "e2b_desktop",
        OUT / "boxfab_desktop",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        up / "tests", OUT / "tests", ignore=shutil.ignore_patterns("__pycache__")
    )
    shutil.copy2(up / "pytest.ini", OUT / "pytest.ini")
    shutil.copy2(up / "CHANGELOG.md", OUT / "CHANGELOG-E2B.md")
    # The desktop package is MIT like the core; it ships the repository's LICENSE (packaging
    # cannot reach files above desktop/), which must carry upstream's copyright line.
    up_lic = (up / "LICENSE").read_text()
    ours = (ROOT / "LICENSE").read_text()
    for line in (ln for ln in up_lic.splitlines() if ln.startswith("Copyright")):
        if line not in ours.splitlines():
            sys.exit(
                f"LICENSE lacks the desktop package's upstream copyright line: {line}"
            )
    if not ours.endswith(up_lic[up_lic.index("Permission is hereby granted") :]):
        sys.exit("LICENSE permission text differs from the desktop package's")
    shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")

    counts = {"imports": 0, "env": 0}
    paths = [
        *OUT.joinpath("boxfab_desktop").rglob("*.py"),
        *OUT.joinpath("tests").rglob("*.py"),
        OUT / "pytest.ini",
    ]
    for p in sorted(paths):
        text = p.read_text()
        new, n1 = re.subn(r"\be2b_desktop\b", "boxfab_desktop", text)
        new, n2 = re.subn(r"\bfrom e2b(?=[ .])", "from boxfab", new)
        new, n3 = re.subn(r"^(\s*)import e2b$", r"\1import boxfab", new, flags=re.M)
        new, n4 = ENV_RX.subn(r"BOXFAB_\1", new)
        counts["imports"] += n1 + n2 + n3
        counts["env"] += n4
        if new != text:
            p.write_text(new)
    expect = {"imports": 15, "env": 7}
    if counts != expect:
        sys.exit(f"desktop renames: {counts}, expected {expect}")
    apply_exact(EXACT)
    client = OUT / "boxfab_desktop/client.py"
    client.write_text(client.read_text().rstrip("\n") + "\n" + CLIENT_ALIAS)

    text = (up / "README.md").read_text()
    if text.count(README_START) != 1:
        sys.exit("desktop-python/README.md: section 3 heading changed upstream")
    body = text[text.index(README_START) :]
    for rx, repl, count in README_RULES:
        body, n = re.subn(rx, repl, body)
        if n != count:
            sys.exit(f"desktop README {rx!r}: {n} matches, expected {count}")
    left = [
        ln for ln in body.splitlines() if re.search(r"e2b_desktop|e2b\.dev|E2B_", ln)
    ]
    if left:
        sys.exit(f"desktop README: upstream references left: {left}")
    header = (ROOT / "overlay/desktop/README-header.md").read_text()
    footer = (ROOT / "overlay/desktop/README-footer.md").read_text()
    (OUT / "README.md").write_text(header + body.rstrip("\n") + "\n" + footer)

    problems = []
    for p in OUT.joinpath("boxfab_desktop").rglob("*.py"):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            for rx, what in FORBIDDEN:
                if rx.search(line):
                    problems.append(
                        f"{p.relative_to(ROOT)}:{i}: {what}: {line.strip()}"
                    )
    if problems:
        sys.exit("desktop audit failed:\n  " + "\n  ".join(problems))
    print(f"desktop: {counts}", file=sys.stderr)
