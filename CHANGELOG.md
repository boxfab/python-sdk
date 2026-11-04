# Changelog

Upstream E2B changes are in `CHANGELOG-E2B.md`.

## 0.1.0a2 (2026-11-03)

- Default domain `boxfab.io` (was `sandd.contextfab.io`, which keeps working until it is retired);
  the missing-key message points to `https://dashboard.boxfab.io`.
- Docstrings and comments name BoxFab instead of E2B; documentation links point to
  `https://boxfab.dev/docs`.
- README and package metadata: shorter, BoxFab-focused; attribution in the License section,
  `LICENSE` and `UPSTREAM.md`.

## 0.1.0a1 (2026-11-01)

- First alpha, generated from E2B Python SDK 2.62.0 (commit `3a904178b2f1`), see `UPSTREAM.md`.
- Distribution and import name `boxfab`; client class `BoxFab` (`E2B` kept as an alias).
- Configuration only through `BOXFAB_*` environment variables (`BOXFAB_API_KEY`,
  `BOXFAB_DOMAIN`, ...); `E2B_*` variables are not read.
- Default domain `sandd.contextfab.io` (BoxFab's current deployment).
- Release pipeline: Trusted Publishing from GitHub Releases, CI on the exact release commit,
  distribution checks (`scripts/check_dist.py`); see `RELEASING.md`.
