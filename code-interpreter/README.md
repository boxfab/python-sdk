# BoxFab Code Interpreter (Python)

Run AI-generated code in isolated [BoxFab](https://boxfab.io) sandboxes, Jupyter-style:
Python, JavaScript, TypeScript, R, Java and Bash, with results such as text, tables and charts
returned as data.

## Getting started

### 1. Install the SDK

```bash
pip install boxfab-code-interpreter
```

### 2. Get a BoxFab API key

Get a key from the [BoxFab dashboard](https://dashboard.boxfab.io) and set it as `BOXFAB_API_KEY`.
The SDK reads only `BOXFAB_*` variables.

### 3. Execute code with code interpreter inside Sandbox

```py
from boxfab_code_interpreter import Sandbox

with Sandbox.create() as sandbox:
    sandbox.run_code("x = 1")
    execution = sandbox.run_code("x+=1; x")
    print(execution.text)  # outputs 2
```

### 4. Bind the configuration to a client

The top-level `Sandbox` and `AsyncSandbox` exports read their configuration from the environment variables. To use an explicit configuration — e.g. several API keys or domains in one process — create a `BoxFab` client and use the resource classes it exposes:

```py
from boxfab_code_interpreter import BoxFab

client = BoxFab(api_key="e2b_***", domain="boxfab.io")

with client.Sandbox.create() as sandbox:
    execution = sandbox.run_code("x = 1; x += 1; x")

# The async variant is exposed as well.
async_sandbox = await client.AsyncSandbox.create()

# The core resources are bound to the client's configuration as well.
volume = client.Volume.create("my-volume")
exists = client.Template.exists("my-template")
secret = client.Secret.create("openai-api-key", "sk-***")

# The classes can be assigned and used like the top-level ones.
Sandbox = client.Sandbox
paginator = Sandbox.list()
```

Per-call params still take precedence over the client's params, and clients are isolated from each other and from the env-configured top-level exports.

## Under the hood

Sandboxes are created from the `code-interpreter-v1` template, which BoxFab provides to every team:
a Jupyter server with common data-science packages. BoxFab sandboxes are
[Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the open-source
[E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This package is derived from the
open-source E2B Code Interpreter SDK;
[UPSTREAM.md](https://github.com/boxfab/python-sdk/blob/main/UPSTREAM.md) lists every change.

**Using the E2B Code Interpreter SDKs.** BoxFab serves the same API and provides the
`code-interpreter-v1` template, so the E2B Code Interpreter SDKs work with it as well. Set both
variables, the domain first:

```bash
export E2B_DOMAIN=boxfab.io
export E2B_API_KEY="<your BoxFab API key>"
```

Without `E2B_DOMAIN`, the E2B SDKs send requests, including the key, to E2B's own service.

Tested against BoxFab with `e2b-code-interpreter` 2.11.6 (Python) and `@e2b/code-interpreter` 2.9.0
(JavaScript).

## License

MIT, as the E2B Code Interpreter SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
