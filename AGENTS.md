# Notes for AI agents and reviewers

## Review guidelines

This repository republishes the open-source E2B Python SDK under the BoxFab name. Most of the code
is copied from upstream by `scripts/sync_upstream.py` (and `scripts/sync_desktop.py`) and then
changed by a fixed set of asserted rewrites (see `UPSTREAM.md`).

- **Generated paths are out of scope for behaviour review:** `boxfab/`, `tests/`, `pytest.ini`,
  `CHANGELOG-E2B.md`, `desktop/boxfab_desktop/`, `desktop/tests/`, `desktop/pytest.ini`,
  `desktop/CHANGELOG-E2B.md`, `desktop/README.md` and `desktop/LICENSE`. Their logic is upstream's;
  bugs in it are not fixed here (known ones are listed in `UPSTREAM.md`). Do not report them.
- **Do review:** the sync scripts and their rules (a rewrite that changes behaviour beyond a rename,
  a rule that can match the wrong text, an audit that can miss an upstream name or variable), the
  repository's own code and tests (`scripts/`, `tests_boxfab/`, `integration/`, `examples/`), the
  workflows in `.github/workflows/` (release safety, permissions, secrets, triggers), packaging
  (`pyproject.toml`, `desktop/pyproject.toml`) and the hand-written docs.
- Report concrete P1/P2 defects with the triggering input and effect; skip style.
