# BoxFab Python SDK

Python SDK for [BoxFab](https://boxfab.dev), an agent execution cloud: start isolated
Firecracker sandboxes, run commands, move files, and reach services running inside them.

> **Alpha.** The API may still change between releases.

## Install

Python 3.11 or newer.

```bash
pip install boxfab
```

## Authenticate

Get an API key from the [BoxFab dashboard](https://dashboard.boxfab.io) or your BoxFab
administrator and export it:

```bash
export BOXFAB_API_KEY="e2b_..."
```

You can also pass `api_key=` to any call. Only `BOXFAB_*` environment variables are read.

## Quick start

```python
from boxfab import Sandbox

with Sandbox.create() as sandbox:          # killed when the block exits
    result = sandbox.commands.run("echo Hello from BoxFab")
    print(result.stdout)
```

`Sandbox.create("base", timeout=600)` picks a template and a lifetime in seconds (default 300).

### Commands

```python
from boxfab import CommandExitException

result = sandbox.commands.run("ls -la /home/user")
print(result.exit_code, result.stdout, result.stderr)

try:
    sandbox.commands.run("exit 3")
except CommandExitException as e:          # non-zero exit codes raise
    print(e.exit_code, e.stderr)

server = sandbox.commands.run("python3 -m http.server 8080", background=True)
print(sandbox.get_host(8080))              # 8080-<sandbox id>.<domain>, served over HTTPS
server.kill()
```

### Files

```python
sandbox.files.write("/home/user/hello.txt", "hi")
print(sandbox.files.read("/home/user/hello.txt"))
print([e.name for e in sandbox.files.list("/home/user")])
data = sandbox.files.read("/home/user/hello.txt", format="bytes")
```

### Reconnect, pause and resume

```python
sandbox_id = sandbox.sandbox_id
sandbox.pause()                            # keeps memory and disk
sandbox = Sandbox.connect(sandbox_id)      # resumes it
sandbox.kill()
```

### Async

```python
import asyncio
from boxfab import AsyncSandbox

async def main():
    sandbox = await AsyncSandbox.create()
    try:
        result = await sandbox.commands.run("uname -a")
        print(result.stdout)
    finally:
        await sandbox.kill()

asyncio.run(main())
```

### Explicit client

```python
from boxfab import BoxFab

client = BoxFab(api_key="e2b_...", domain="boxfab.io")
sandbox = client.Sandbox.create()
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `BOXFAB_API_KEY` | none | API key |
| `BOXFAB_DOMAIN` | `boxfab.io` | BoxFab domain; the API is `https://api.<domain>`, sandbox ports are `https://<port>-<id>.<domain>` |
| `BOXFAB_DEBUG` | `false` | plain HTTP to a local development stack |
| `BOXFAB_HTTP_VERSION`, `BOXFAB_CONNECTION_RETRIES`, `BOXFAB_MAX_CONNECTIONS`, `BOXFAB_MAX_KEEPALIVE_CONNECTIONS`, `BOXFAB_KEEPALIVE_EXPIRY` | as upstream | transport tuning |

Every call also accepts `api_key=`, `domain=`, `request_timeout=` and the other connection
parameters directly.

## Known limitations

- Verified against the live service: sandbox create/connect/list/kill, commands (stdout,
  stderr, exit codes, timeouts, background processes), files (read, write, list, remove,
  signed upload/download URLs), port URLs, pause/resume, timeouts and info, async with
  concurrency. Other upstream features (template builds, volumes, secrets, MCP, IAM tokens,
  network rules, git helpers, PTY, filesystem watch) are included but not yet verified on
  BoxFab; volumes, secrets and MCP depend on services the deployment may not run.
- Add-on packages for code interpreting and desktop sandboxes are not available for `boxfab`
  yet; the `code-interpreter-v1` and `desktop` templates can be used with `Sandbox.create()`.

## Development

```bash
uv sync
uv run pytest tests tests_boxfab -n 8                     # unit tests (offline)
SDK=boxfab BOXFAB_API_KEY=... uv run pytest integration   # live tests, create a few sandboxes
uv build
```

`boxfab/` and `tests/` are generated from upstream by `scripts/sync_upstream.py`; change the
rules there, not the generated files. See [UPSTREAM.md](UPSTREAM.md).
Releases: see [RELEASING.md](RELEASING.md).

## Under the hood

BoxFab sandboxes are [Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the
open-source [E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This SDK is derived from
the open-source E2B Python SDK; [UPSTREAM.md](UPSTREAM.md) lists every change.

**Using the E2B SDKs and CLI.** BoxFab serves the same API, so the E2B SDKs and CLI work with it
as well. Set both variables, the domain first:

```bash
export E2B_DOMAIN=boxfab.io
export E2B_API_KEY="<your BoxFab API key>"
```

Without `E2B_DOMAIN`, the E2B tools send requests, including the key, to E2B's own service. The E2B
CLI's `e2b auth login` signs in to E2B's service; with BoxFab, use `E2B_API_KEY` instead.

Tested against BoxFab with `e2b` 2.62.0 (Python), `e2b` 2.61.0 (JavaScript) and `@e2b/cli` 2.23.0.

## License

MIT, as the E2B Python SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
