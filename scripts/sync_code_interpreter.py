"""Regenerate code-interpreter/ (the boxfab-code-interpreter package) from the pinned E2B commit.

Called by scripts/sync_upstream.py with the same checkout as the core SDK, so all packages are
always generated from one upstream commit:

    packages/code-interpreter-python/e2b_code_interpreter -> code-interpreter/boxfab_code_interpreter
    packages/code-interpreter-python/tests                -> code-interpreter/tests, pytest.ini
    packages/code-interpreter-python/README.md            -> code-interpreter/README.md (sections 3-4)

Generated paths are never edited by hand. Every rule asserts how often it matched, so when
upstream moves code the sync fails instead of shipping an upstream default.
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "code-interpreter"
DOMAIN = "boxfab.io"
DOCS_URL = "https://boxfab.dev/docs"

# Environment variables read by the package and its tests (the core SDK reads the rest).
ENV_VARS = ["API_KEY", "DOMAIN", "DEBUG", "API_URL", "SANDBOX_URL", "TESTS_TEMPLATE"]
ENV_RX = re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b")

EXACT = [
    # client class BoxFab; the upstream names stay importable as aliases.
    (
        "boxfab_code_interpreter/client.py",
        "from boxfab import ApiParams, E2BClientParams\n",
        "from boxfab import ApiParams, BoxFabClientParams, E2BClientParams\n",
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        "from boxfab import E2B as CoreE2B\n",
        "from boxfab import BoxFab as CoreBoxFab\n",
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        "core = CoreE2B(**api_params)",
        "core = CoreBoxFab(**api_params)",
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        '__all__ = ["E2B", "E2BClientParams"]',
        '__all__ = ["BoxFab", "BoxFabClientParams", "E2B", "E2BClientParams"]',
        1,
    ),
    ("boxfab_code_interpreter/client.py", "class E2B:", "class BoxFab:", 1),
    (
        "boxfab_code_interpreter/client.py",
        "    E2B client with an explicitly bound connection configuration.",
        "    BoxFab client with an explicitly bound connection configuration.",
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        "    from boxfab_code_interpreter import E2B\n",
        "    from boxfab_code_interpreter import BoxFab\n",
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        'client = E2B(api_key="e2b_...", domain="e2b.dev")',
        f'client = BoxFab(api_key="e2b_...", domain="{DOMAIN}")',
        1,
    ),
    (
        "boxfab_code_interpreter/client.py",
        "**opts: Unpack[E2BClientParams]",
        "**opts: Unpack[BoxFabClientParams]",
        1,
    ),
    (
        "boxfab_code_interpreter/__init__.py",
        "from .client import E2B, E2BClientParams",
        "from .client import BoxFab, BoxFabClientParams, E2B, E2BClientParams",
        1,
    ),
    # the product name in the class docstrings
    (
        "boxfab_code_interpreter/code_interpreter_sync.py",
        "    E2B cloud sandbox is a secure and isolated cloud environment.",
        "    BoxFab cloud sandbox is a secure and isolated cloud environment.",
        1,
    ),
    (
        "boxfab_code_interpreter/code_interpreter_async.py",
        "    E2B cloud sandbox is a secure and isolated cloud environment.",
        "    BoxFab cloud sandbox is a secure and isolated cloud environment.",
        1,
    ),
    # docstring links to the documentation
    (
        "boxfab_code_interpreter/code_interpreter_sync.py",
        "Check docs [here](https://e2b.dev/docs).",
        f"Check docs [here]({DOCS_URL}).",
        1,
    ),
    (
        "boxfab_code_interpreter/code_interpreter_async.py",
        "Check docs [here](https://e2b.dev/docs).",
        f"Check docs [here]({DOCS_URL}).",
        1,
    ),
]

CLIENT_ALIAS = """

# Upstream name, kept so code written for the upstream package ports by changing only the import.
E2B = BoxFab
"""

README_START = "### 3. Execute code with code interpreter inside Sandbox\n"
README_END = "### 5. Check docs\n"
README_RULES = [
    (r"\be2b_code_interpreter\b", "boxfab_code_interpreter", 2),
    (r"create an `E2B` client", "create a `BoxFab` client", 1),
    (
        r"from boxfab_code_interpreter import E2B\n",
        "from boxfab_code_interpreter import BoxFab\n",
        1,
    ),
    (
        r'client = E2B\(api_key="e2b_\*\*\*", domain="e2b\.dev"\)',
        f'client = BoxFab(api_key="e2b_***", domain="{DOMAIN}")',
        1,
    ),
]

# What must not remain in generated code. The `e2b_` API-key prefix is protocol, not branding;
# the `E2b-Sandbox-Port` header is wire protocol too.
FORBIDDEN = [
    (re.compile(r"\b(from|import) e2b\b(?!_)"), "e2b import"),
    (re.compile(r"\be2b_code_interpreter\b"), "upstream package name"),
    (re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b"), "E2B_* variable"),
    (re.compile(r"e2b\.dev|e2b\.app"), "E2B domain"),
]


def apply_exact(rules):
    for rel, old, new, expected in rules:
        p = OUT / rel
        text = p.read_text()
        n = text.count(old)
        if n != expected:
            sys.exit(
                f"code-interpreter/{rel}: expected {expected} x {old[:70]!r}, found {n}"
            )
        p.write_text(text.replace(old, new))


def sync(src: Path):
    """Generate code-interpreter/ from `src`, an E2B monorepo checkout at the pinned commit."""
    up = src / "packages/code-interpreter-python"
    if not (up / "e2b_code_interpreter").is_dir():
        sys.exit(f"{up}/e2b_code_interpreter not found")
    for d in ("boxfab_code_interpreter", "tests"):
        shutil.rmtree(OUT / d, ignore_errors=True)
    shutil.copytree(
        up / "e2b_code_interpreter",
        OUT / "boxfab_code_interpreter",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        up / "tests", OUT / "tests", ignore=shutil.ignore_patterns("__pycache__")
    )
    shutil.copy2(up / "pytest.ini", OUT / "pytest.ini")
    shutil.copy2(up / "CHANGELOG.md", OUT / "CHANGELOG-E2B.md")
    # MIT like the core; the package ships the repository's LICENSE, which must carry upstream's
    # copyright line and permission text.
    up_lic = (up / "LICENSE").read_text()
    ours = (ROOT / "LICENSE").read_text()
    for line in (ln for ln in up_lic.splitlines() if ln.startswith("Copyright")):
        if line not in ours.splitlines():
            sys.exit(
                f"LICENSE lacks the code interpreter's upstream copyright line: {line}"
            )
    if not ours.rstrip().endswith(
        up_lic[up_lic.index("Permission is hereby granted") :].rstrip()
    ):
        sys.exit("LICENSE permission text differs from the code interpreter's")
    shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")

    counts = {"imports": 0, "env": 0}
    paths = [
        *OUT.joinpath("boxfab_code_interpreter").rglob("*.py"),
        *OUT.joinpath("tests").rglob("*.py"),
        OUT / "pytest.ini",
    ]
    for p in sorted(paths):
        text = p.read_text()
        new, n1 = re.subn(r"\be2b_code_interpreter\b", "boxfab_code_interpreter", text)
        new, n2 = re.subn(r"\bfrom e2b(?=[ .])", "from boxfab", new)
        new, n3 = re.subn(
            r"^(\s*)import e2b$", r"\1import boxfab", new, flags=re.MULTILINE
        )
        new, n4 = ENV_RX.subn(r"BOXFAB_\1", new)
        counts["imports"] += n1 + n2 + n3
        counts["env"] += n4
        if new != text:
            p.write_text(new)
    expect = EXPECT_COUNTS
    if counts != expect:
        sys.exit(f"code-interpreter renames: {counts}, expected {expect}")
    apply_exact(EXACT)
    client = OUT / "boxfab_code_interpreter/client.py"
    client.write_text(client.read_text().rstrip("\n") + "\n" + CLIENT_ALIAS)

    text = (up / "README.md").read_text()
    if text.count(README_START) != 1 or text.count(README_END) != 1:
        sys.exit("code-interpreter-python/README.md: section headings changed upstream")
    body = text[text.index(README_START) : text.index(README_END)]
    for rx, repl, count in README_RULES:
        body, n = re.subn(rx, repl, body)
        if n != count:
            sys.exit(f"code-interpreter README {rx!r}: {n} matches, expected {count}")
    left = [
        ln
        for ln in body.splitlines()
        if re.search(r"e2b_code_interpreter|e2b\.dev|E2B_|\bE2B\b", ln)
    ]
    if left:
        sys.exit(f"code-interpreter README: upstream references left: {left}")
    header = (ROOT / "overlay/code-interpreter/README-header.md").read_text()
    footer = (ROOT / "overlay/code-interpreter/README-footer.md").read_text()
    (OUT / "README.md").write_text(header + body.rstrip("\n") + "\n" + footer)

    problems = []
    for p in OUT.joinpath("boxfab_code_interpreter").rglob("*.py"):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            for rx, what in FORBIDDEN:
                if rx.search(line):
                    problems.append(
                        f"{p.relative_to(ROOT)}:{i}: {what}: {line.strip()}"
                    )
    if problems:
        sys.exit("code-interpreter audit failed:\n  " + "\n  ".join(problems))
    print(f"code-interpreter: {counts}", file=sys.stderr)


EXPECT_COUNTS = {
    "imports": 54,
    "env": 9,
}  # at the pinned commit; a change means upstream moved
