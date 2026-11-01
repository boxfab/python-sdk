"""BoxFab-specific guarantees on top of upstream's tests (which live in tests/ and are generated)."""

import importlib.metadata
import pathlib
import re

import pytest

import boxfab
from boxfab import ConnectionConfig, VolumeConnectionConfig

DEFAULT_DOMAIN = "sandd.contextfab.io"
PKG = pathlib.Path(boxfab.__file__).parent


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    import os

    for k in list(os.environ):
        if k.startswith(("E2B_", "BOXFAB_")):
            monkeypatch.delenv(k)


def test_distribution_metadata():
    assert importlib.metadata.version("boxfab") == boxfab.api.metadata.package_version
    assert boxfab.api.metadata.default_headers["publisher"] == "boxfab"


def test_default_domain_is_boxfab():
    c = ConnectionConfig()
    assert c.domain == DEFAULT_DOMAIN
    assert c.api_url == f"https://api.{DEFAULT_DOMAIN}"
    assert VolumeConnectionConfig().api_url == f"https://api.{DEFAULT_DOMAIN}"
    assert c.headers["User-Agent"].startswith("boxfab-python-sdk/")


def test_boxfab_env_vars_are_read(monkeypatch):
    monkeypatch.setenv("BOXFAB_API_KEY", "e2b_" + "1" * 40)
    monkeypatch.setenv("BOXFAB_DOMAIN", "example.test")
    c = ConnectionConfig()
    assert c.api_key == "e2b_" + "1" * 40
    assert c.domain == "example.test"
    assert c.api_url == "https://api.example.test"


def test_e2b_env_vars_are_ignored(monkeypatch):
    monkeypatch.setenv("E2B_API_KEY", "e2b_" + "2" * 40)
    monkeypatch.setenv("E2B_DOMAIN", "e2b.app")
    monkeypatch.setenv("E2B_API_URL", "https://api.e2b.app")
    monkeypatch.setenv("E2B_SANDBOX_URL", "https://sandbox.e2b.app")
    monkeypatch.setenv("E2B_ACCESS_TOKEN", "tok")
    c = ConnectionConfig()
    assert c.api_key is None
    assert c.domain == DEFAULT_DOMAIN
    assert c.api_url == f"https://api.{DEFAULT_DOMAIN}"
    assert (
        c.get_sandbox_url("abc", DEFAULT_DOMAIN)
        == f"https://49983-abc.{DEFAULT_DOMAIN}"
    )
    v = VolumeConnectionConfig()
    assert v.api_url == f"https://api.{DEFAULT_DOMAIN}"


def test_our_domain_uses_per_sandbox_hosts():
    # Our client-proxy routes by host name; the shared sandbox.<domain> path is E2B-only.
    c = ConnectionConfig()
    assert (
        c.get_sandbox_url("abc", DEFAULT_DOMAIN)
        == f"https://49983-abc.{DEFAULT_DOMAIN}"
    )
    assert c.get_host("abc", DEFAULT_DOMAIN, 8080) == f"8080-abc.{DEFAULT_DOMAIN}"


def test_missing_key_message_is_boxfab():
    from boxfab.api import ApiClient

    with pytest.raises(boxfab.AuthenticationException) as ei:
        ApiClient(ConnectionConfig())
    msg = str(ei.value)
    assert "BOXFAB_API_KEY" in msg
    assert "E2B_API_KEY" not in msg
    assert "e2b.dev" not in msg


def test_client_names():
    assert boxfab.BoxFab is boxfab.E2B
    c = boxfab.BoxFab(api_key="e2b_" + "3" * 40, domain="example.test")
    assert c.Sandbox._bound_api_params["domain"] == "example.test"


def test_source_never_reads_e2b_variables():
    offenders = []
    for p in PKG.rglob("*.py"):
        text = p.read_text()
        for m in re.finditer(r"\bE2B_[A-Z0-9_]+\b", text):
            if not re.fullmatch(r"E2B_(HEREDOC_[A-Z0-9_]*|EXIT)", m.group(0)):
                offenders.append(f"{p.relative_to(PKG)}: {m.group(0)}")
    assert offenders == []
