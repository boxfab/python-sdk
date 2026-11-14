# Changelog

Upstream E2B changes are in `CHANGELOG-E2B.md`.

## Unreleased

- New package `boxfab-desktop` in `desktop/` (virtual Linux desktop for computer-use agents),
  generated in the same sync run as `boxfab`; released separately with `desktop-v*` tags through
  `publish-desktop.yml`. CI job `desktop`; live tests job `live-desktop`.
- README: the "Using the E2B SDKs and CLI" paragraph lists the E2B versions tested against
  BoxFab (Python, JavaScript, CLI) and notes that `e2b auth login` signs in to E2B's service.

## 0.1.0a3 (2026-11-13)

- One `LICENSE` file: the MIT text with the upstream copyright line (FOUNDRYLABS, INC.) and
  ContextFab's; `LICENSE-E2B` is merged into it.
- README: "Under the hood" section (Firecracker, the E2B open-source infrastructure and SDK, and how
  to use the E2B SDKs with BoxFab).
- Live tests also run the suite with the E2B SDK (`e2b` 2.62.0) against BoxFab (`live.yml`, job
  `live-e2b`).
- Releases 0.1.0a1 and 0.1.0a2 have no git tags in this repository; their code is at commits
  `908b46d` and `3110a4c`.

## 0.1.0a2 (2026-11-03)

- Default domain `boxfab.io` (was `sandd.contextfab.io`, which keeps working until it is retired);
  the missing-key message points to `https://dashboard.boxfab.io`.
- Docstrings and comments name BoxFab instead of E2B; documentation links point to
  `https://boxfab.dev/docs`.
- README and package metadata shortened; the upstream credit (E2B Python SDK, MIT) is in the
  README's License section, `LICENSE` and `UPSTREAM.md`.

## 0.1.0a1 (2026-11-01)

- First alpha, generated from E2B Python SDK 2.62.0 (commit `3a904178b2f1`), see `UPSTREAM.md`.
- Distribution and import name `boxfab`; client class `BoxFab` (`E2B` kept as an alias).
- Configuration only through `BOXFAB_*` environment variables (`BOXFAB_API_KEY`,
  `BOXFAB_DOMAIN`, ...); `E2B_*` variables are not read.
- Default domain `sandd.contextfab.io` (BoxFab's current deployment).
- Release pipeline: Trusted Publishing from GitHub Releases, CI on the exact release commit,
  distribution checks (`scripts/check_dist.py`); see `RELEASING.md`.
