"""Live integration tests against a running deployment.

The same file runs against vanilla E2B and against BoxFab, so behaviour can be compared:

    SDK=e2b    E2B_API_KEY=...    E2B_DOMAIN=...    pytest integration
    SDK=boxfab BOXFAB_API_KEY=... BOXFAB_DOMAIN=... pytest integration

Credentials come only from the environment of the SDK under test. Every sandbox a test creates
is killed in the fixture's finalizer, also when the test fails. Concurrency is capped at
MAX_CONCURRENT.
"""

import asyncio
import importlib
import os
import time
import uuid

import httpx
import pytest

SDK_NAME = os.environ.get("SDK", "boxfab")
sdk = importlib.import_module(SDK_NAME)
ENV_PREFIX = "E2B" if SDK_NAME == "e2b" else "BOXFAB"
API_KEY = os.environ.get(f"{ENV_PREFIX}_API_KEY")
TEMPLATE = os.environ.get("LIVE_TEMPLATE", "base")
SANDBOX_TIMEOUT = 180  # seconds a test sandbox may live if cleanup is ever skipped
MAX_CONCURRENT = int(os.environ.get("LIVE_MAX_CONCURRENT", "5"))
RUN_TAG = f"live-{uuid.uuid4().hex[:8]}"

pytestmark = [
    pytest.mark.skipif(not API_KEY, reason=f"{ENV_PREFIX}_API_KEY not set"),
    pytest.mark.timeout(180),
]


@pytest.fixture
def created():
    """Collects sandboxes; kills each one afterwards, whatever the test outcome."""
    boxes = []
    yield boxes
    for sbx in boxes:
        try:
            sbx.kill()
        except Exception:
            pass


def _create(created, **kw):
    sbx = sdk.Sandbox.create(
        TEMPLATE, timeout=SANDBOX_TIMEOUT, metadata={"run": RUN_TAG}, **kw
    )
    created.append(sbx)
    return sbx


def test_lifecycle(created):
    with sdk.Sandbox.create(
        TEMPLATE, timeout=SANDBOX_TIMEOUT, metadata={"run": RUN_TAG}
    ) as sbx:
        created.append(sbx)
        res = sbx.commands.run(f"echo {SDK_NAME}-ok")
        assert res.stdout.strip() == f"{SDK_NAME}-ok"
        assert res.exit_code == 0
        assert sbx.is_running()
        sid = sbx.sandbox_id
    # context exit killed it
    with pytest.raises(sdk.NotFoundException):
        sdk.Sandbox.connect(sid)


def test_stdout_stderr_exit_code(created):
    sbx = _create(created)
    with pytest.raises(sdk.CommandExitException) as ei:
        sbx.commands.run("echo out; echo err 1>&2; exit 3")
    assert ei.value.exit_code == 3
    assert ei.value.stdout.strip() == "out"
    assert ei.value.stderr.strip() == "err"


def test_command_timeout(created):
    sbx = _create(created)
    t0 = time.monotonic()
    with pytest.raises(sdk.TimeoutException):
        sbx.commands.run("sleep 30", timeout=2)
    assert time.monotonic() - t0 < 15


def test_background_command_and_port(created):
    sbx = _create(created)
    sbx.commands.run("python3 -m http.server 8080", background=True)
    url = f"https://{sbx.get_host(8080)}/"
    for _ in range(20):
        try:
            if httpx.get(url, timeout=10).status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    else:
        pytest.fail(f"port 8080 not reachable at {url}")


def test_files(created):
    sbx = _create(created)
    sbx.files.write("/home/user/a/hello.txt", "hello")
    assert sbx.files.read("/home/user/a/hello.txt") == "hello"
    blob = bytes(range(256)) * 64
    sbx.files.write("/home/user/a/blob.bin", blob)
    assert bytes(sbx.files.read("/home/user/a/blob.bin", format="bytes")) == blob
    names = sorted(e.name for e in sbx.files.list("/home/user/a"))
    assert names == ["blob.bin", "hello.txt"]
    assert sbx.files.exists("/home/user/a/hello.txt")
    sbx.files.remove("/home/user/a/hello.txt")
    assert not sbx.files.exists("/home/user/a/hello.txt")
    with pytest.raises(sdk.FileNotFoundException):
        sbx.files.read("/home/user/a/missing")
    # upload/download through the signed URL path
    up = sbx.upload_url("/home/user/up.txt")
    assert (
        httpx.post(up, files={"file": ("up.txt", b"uploaded")}, timeout=30).status_code
        < 300
    )
    assert (
        httpx.get(sbx.download_url("/home/user/up.txt"), timeout=30).content
        == b"uploaded"
    )


def test_connect_and_list(created):
    sbx = _create(created)
    again = sdk.Sandbox.connect(sbx.sandbox_id)
    assert again.commands.run("echo connected").stdout.strip() == "connected"
    ids = [
        s.sandbox_id
        for s in sdk.Sandbox.list(
            query=sdk.SandboxQuery(metadata={"run": RUN_TAG})
        ).next_items()
    ]
    assert sbx.sandbox_id in ids


def test_pause_resume(created):
    sbx = _create(created)
    sbx.files.write("/tmp/marker", "before pause")
    sbx.pause()
    resumed = sdk.Sandbox.connect(sbx.sandbox_id, timeout=SANDBOX_TIMEOUT)
    created.append(resumed)
    assert resumed.files.read("/tmp/marker") == "before pause"


def test_set_timeout_and_info(created):
    sbx = _create(created)
    sbx.set_timeout(120)
    info = sbx.get_info()
    assert info.sandbox_id == sbx.sandbox_id
    assert info.metadata.get("run") == RUN_TAG


def test_invalid_api_key_is_actionable_and_not_echoed():
    bad = f"{API_KEY[:4]}{'0' * 40}" if API_KEY else "x"
    with pytest.raises(sdk.AuthenticationException) as ei:
        sdk.Sandbox.create(TEMPLATE, api_key=bad, timeout=60)
    assert bad not in str(ei.value)
    assert API_KEY not in str(ei.value)


def test_unknown_sandbox_id():
    with pytest.raises(sdk.NotFoundException):
        sdk.Sandbox.connect("doesnotexist0000000000")


def test_unreachable_domain_fails_fast():
    t0 = time.monotonic()
    with pytest.raises(Exception) as ei:
        sdk.Sandbox.create(
            TEMPLATE, domain="unreachable.invalid", timeout=60, request_timeout=5
        )
    assert API_KEY not in str(ei.value)
    assert time.monotonic() - t0 < 60


def test_cleanup_after_exception():
    sid = None
    with pytest.raises(RuntimeError):
        with sdk.Sandbox.create(
            TEMPLATE, timeout=SANDBOX_TIMEOUT, metadata={"run": RUN_TAG}
        ) as sbx:
            sid = sbx.sandbox_id
            raise RuntimeError("boom")
    with pytest.raises(sdk.NotFoundException):
        sdk.Sandbox.connect(sid)


async def test_async_concurrent():
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def one(i):
        async with sem:
            sbx = await sdk.AsyncSandbox.create(
                TEMPLATE, timeout=SANDBOX_TIMEOUT, metadata={"run": RUN_TAG}
            )
            try:
                res = await sbx.commands.run(f"echo n{i}")
                return res.stdout.strip()
            finally:
                await sbx.kill()

    out = await asyncio.gather(*(one(i) for i in range(MAX_CONCURRENT)))
    assert out == [f"n{i}" for i in range(MAX_CONCURRENT)]
