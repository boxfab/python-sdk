# Changelog (boxfab-desktop)

Upstream E2B Desktop SDK changes are in `CHANGELOG-E2B.md`.

## 0.1.0a1 (unreleased)

- First alpha, generated from the E2B Desktop SDK `e2b-desktop` 2.7.2 (E2B monorepo commit
  `3a904178b2f1`, the commit the core `boxfab` package is generated from).
- Distribution and import name `boxfab-desktop` / `boxfab_desktop`; client class `BoxFab`
  (`E2B` kept as an alias). Configuration only through `BOXFAB_*` environment variables.
- Live tests take the template from `BOXFAB_DESKTOP_TEMPLATE` (default: the SDK's `desktop`).
