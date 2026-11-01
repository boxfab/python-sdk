# Releasing

PyPI is reached only through `.github/workflows/publish.yml`, which runs when a GitHub Release
is **published** (pre-releases included; saving a draft does nothing). There is no PyPI token
anywhere: the upload uses PyPI Trusted Publishing (OIDC).

## What protects a release

| Control | Where |
|---|---|
| `main` changes only via squash-merged pull requests whose CI passed (6 required checks); no force pushes or deletion | ruleset `Protect main` |
| only repository admins can create `v*` tags | ruleset `Release tags: creation` |
| `v*` tags cannot be moved or deleted by anyone | ruleset `Release tags: immutable` (no bypass) |
| a published release's tag and assets cannot change | repository setting: immutable releases |
| tag must be `v<version in pyproject.toml>`; the tagged commit must be on `main` | `publish.yml` job `verify` |
| full CI on the exact tagged commit; the distributions are built and checked there once | `publish.yml` job `ci` (calls `ci.yml`) |
| `twine check --strict`, name/version/license metadata, license files, file layout, secret and internal-address scan, clean-venv import | `ci.yml` job `build` + `scripts/check_dist.py` |
| those exact files are uploaded; only this job has `id-token: write` | `publish.yml` job `publish` |
| deploys only from `v*` tags | environment `pypi` |
| one publication at a time, never cancelled | `concurrency: pypi-publish` |
| actions pinned to commit SHAs; only GitHub-owned, `astral-sh/setup-uv`, `pypa/gh-action-pypi-publish` allowed | workflow files + repository Actions settings |

While the repository is private, GitHub Team cannot require an environment reviewer, so the
human approval is the act of publishing the GitHub Release. After the repository is public, add
a required reviewer to the `pypi` environment.

## One-time setup (owner)

1. PyPI → Account settings → Publishing → *Add a new pending publisher*
   (https://pypi.org/manage/account/publishing/), GitHub tab:
   - PyPI Project Name: `boxfab`
   - Owner: `boxfab`
   - Repository name: `python-sdk`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

   A pending publisher does not reserve the name; the first successful upload does.
2. PyPI account has 2FA enabled.
3. Optional: repository secret `DIST_EXTRA_DENY` (Settings → Secrets and variables → Actions)
   holding a regex of site-specific names the distribution check must reject (internal host
   names, tailnet name, ...). Without it the generic checks still run.

## Releasing a version

1. On a branch: set `version` in `pyproject.toml`, add the `CHANGELOG.md` entry, run
   `uv lock`, open a PR, wait for green CI, squash-merge.
2. Locally, on the merged `main`:
   ```bash
   git switch main && git pull
   uv build && uvx twine check --strict dist/* && python scripts/check_dist.py dist
   python scripts/check_release_tag.py v$(python -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
   ```
   Optional: run the live suite (Actions → *Live tests* → Run workflow, on `main`).
3. Check the PyPI pending publisher fields against the list above, letter by letter. A mistake
   there fails the upload, and a re-run of the failed job in the same workflow run is the fix;
   a tag can never be moved or reused.
4. GitHub → Releases → *Draft a new release*
   (https://github.com/boxfab/python-sdk/releases/new):
   - Choose a tag: type `v<version>` (e.g. `v0.1.0a1`), *Create new tag on publish*
   - Target: `main`
   - Title: `v<version>`; notes from `CHANGELOG.md`
   - For a/b/rc versions tick *Set as a pre-release*
   - *Publish release*
5. Watch Actions → *Publish to PyPI*: `verify` → `ci / …` → `publish`. Then check
   https://pypi.org/project/boxfab/ and, in a clean venv, `pip install boxfab==<version>` and
   `python examples/hello_sandbox.py` with `BOXFAB_API_KEY` set.

## If it fails

- `verify` failed: the tag does not match the version or the commit is not on `main`. Nothing
  was uploaded. The tag cannot be deleted; bump the version (e.g. `0.1.0a2`) and release again.
- `ci` failed: fix on `main` via PR, bump the version, release again.
- `publish` failed on authentication: correct the PyPI trusted-publisher fields, then *Re-run
  failed jobs* on the same run (the same files are uploaded).
- PyPI never accepts the same version twice, even after a deletion.
