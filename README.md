# Boxfab Python SDK

Python SDK for [Boxfab](https://github.com/boxfab), an agent execution cloud: start isolated
Firecracker sandboxes, run commands, move files, and reach services running inside them.

> **Alpha.** `0.1.0a1` is the first release. The API follows the E2B SDK it is derived from and
> may still change.

The Boxfab Python SDK is derived from the open-source
[E2B Python SDK](https://github.com/e2b-dev/E2B/tree/main/packages/python-sdk) and includes
modifications for Boxfab's sandbox infrastructure. Boxfab is an independent project and is not
affiliated with or endorsed by E2B. See [UPSTREAM.md](UPSTREAM.md) for the exact source revision
and what was changed.

## Install

Python 3.11 or newer.

```bash
pip install boxfab
```

## Authenticate

Get an API key from your Boxfab administrator and export it:

```bash
export BOXFAB_API_KEY="e2b_..."
```

(Keys keep the `e2b_` prefix of the underlying protocol.) You can also pass `api_key=` to any
call. The SDK reads only `BOXFAB_*` variables; `E2B_*` variables are ignored, so a Boxfab
program never picks up an E2B key and never talks to E2B's service by accident.

## Quick start

```python
from boxfab import Sandbox

with Sandbox.create() as sandbox:          # killed when the block exits
    result = sandbox.commands.run("echo Hello from Boxfab")
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
from boxfab import Boxfab

client = Boxfab(api_key="e2b_...", domain="sandd.contextfab.io")
sandbox = client.Sandbox.create()
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `BOXFAB_API_KEY` | none | API key |
| `BOXFAB_DOMAIN` | `sandd.contextfab.io` | Boxfab domain; the API is `https://api.<domain>`, sandbox ports are `https://<port>-<id>.<domain>` |
| `BOXFAB_DEBUG` | `false` | plain HTTP to a local development stack |
| `BOXFAB_HTTP_VERSION`, `BOXFAB_CONNECTION_RETRIES`, `BOXFAB_MAX_CONNECTIONS`, `BOXFAB_MAX_KEEPALIVE_CONNECTIONS`, `BOXFAB_KEEPALIVE_EXPIRY` | as upstream | transport tuning |

Every call also accepts `api_key=`, `domain=`, `request_timeout=` and the other connection
parameters directly.

**About the domain.** The alpha runs on Boxfab's current deployment at `sandd.contextfab.io`.
This is a temporary name; a Boxfab-branded domain will become the default in a later release,
and `BOXFAB_DOMAIN` lets you switch without upgrading.

## Known limitations

- Verified against the live service: sandbox create/connect/list/kill, commands (stdout,
  stderr, exit codes, timeouts, background processes), files (read, write, list, remove,
  signed upload/download URLs), port URLs, pause/resume, timeouts and info, async with
  concurrency. Other upstream features (template builds, volumes, secrets, MCP, IAM tokens,
  network rules, git helpers, PTY, filesystem watch) are included but not yet verified on
  Boxfab; volumes, secrets and MCP depend on services the deployment may not run.
- E2B add-on packages (`e2b-code-interpreter`, `e2b-desktop`) build on the `e2b` package and do
  not use `boxfab`.
- Docstrings still say "E2B" in places; behaviour is as documented here.

## Development

```bash
uv sync
uv run pytest tests tests_boxfab -n 8                     # unit tests (offline)
SDK=boxfab BOXFAB_API_KEY=... uv run pytest integration   # live tests, create a few sandboxes
uv build
```

`boxfab/` and `tests/` are generated from upstream by `scripts/sync_upstream.py`; change the
rules there, not the generated files. See [UPSTREAM.md](UPSTREAM.md).

## License

MIT. See [LICENSE](LICENSE) and, for the upstream E2B SDK, [LICENSE-E2B](LICENSE-E2B).

Boxfab is a product of ContextFab, Inc.
