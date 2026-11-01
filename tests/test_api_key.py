import pytest

from boxfab import ConnectionConfig
from boxfab.api import ApiClient
from boxfab.exceptions import AuthenticationException


def test_api_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("BOXFAB_API_KEY", raising=False)
    config = ConnectionConfig()
    with pytest.raises(AuthenticationException, match=r"API key is required"):
        ApiClient(config)
