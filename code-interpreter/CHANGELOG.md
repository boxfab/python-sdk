# Changelog (boxfab-code-interpreter)

Upstream E2B Code Interpreter SDK changes are in `CHANGELOG-E2B.md`.

## 0.1.0a2 (2026-11-16)

- Default domain `us-west.boxfab.dev`, BoxFab's first region, through `boxfab` 0.1.0a4 (the core
  package sets it); the previous default `boxfab.io` does not serve the API. The README, the doc
  examples and the `E2B_DOMAIN` instructions use `us-west.boxfab.dev`.
- Dashboard links point to `https://dashboard.us-west.boxfab.io`, docs links to `https://boxfab.io/docs`.

## 0.1.0a1 (2026-11-14)

- First alpha, generated from the E2B Code Interpreter SDK `e2b-code-interpreter` 2.11.6 (E2B
  monorepo commit `3a904178b2f1`, the commit the core `boxfab` package is generated from).
- Distribution and import name `boxfab-code-interpreter` / `boxfab_code_interpreter`; client class
  `BoxFab` (`E2B` kept as an alias). Configuration only through `BOXFAB_*` environment variables.
- Default template `code-interpreter-v1`, provided by BoxFab to every team.
