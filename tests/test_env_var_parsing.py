"""Numeric E2B_* env vars are parsed at import time; an empty-string value
(e.g. `BOXFAB_KEEPALIVE_EXPIRY=` in a dotenv file) must fall back to the default
instead of raising ValueError when the module is imported."""

import importlib

import boxfab.api

_ENV_VARS = (
    "BOXFAB_KEEPALIVE_EXPIRY",
    "BOXFAB_MAX_KEEPALIVE_CONNECTIONS",
    "BOXFAB_CONNECTION_RETRIES",
    "BOXFAB_MAX_CONNECTIONS",
)


def _reload():
    return importlib.reload(boxfab.api)


def test_empty_env_vars_fall_back_to_defaults(monkeypatch):
    for var in _ENV_VARS:
        monkeypatch.setenv(var, "")
    try:
        api = _reload()
        assert api.pool_idle_timeout == 300
        assert api.pool_max_idle_per_host == 20
        assert api.connection_retries == 3
        assert api.max_connections == 200
    finally:
        monkeypatch.undo()
        _reload()


def test_set_env_vars_are_honored(monkeypatch):
    monkeypatch.setenv("BOXFAB_KEEPALIVE_EXPIRY", "42")
    monkeypatch.setenv("BOXFAB_CONNECTION_RETRIES", "5")
    monkeypatch.setenv("BOXFAB_MAX_CONNECTIONS", "8")
    try:
        api = _reload()
        assert api.pool_idle_timeout == 42
        assert api.connection_retries == 5
        assert api.max_connections == 8
    finally:
        monkeypatch.undo()
        _reload()
