"""Compatibility tests for FastMCP v2/v3 Context state APIs."""

import pytest

from langsmith_mcp_server.common import helpers


class DummyClient:
    def __init__(self, api_key: str, api_url: str | None = None):
        self.api_key = api_key
        self.api_url = api_url


class SyncContext:
    """FastMCP v2-like context with sync state methods."""

    def __init__(self):
        self._state = {}
        self.request_context = None

    def get_state(self, key: str):
        return self._state.get(key)

    def set_state(self, key: str, value):
        self._state[key] = value


class AsyncContext:
    """FastMCP v3-like context with async state methods."""

    def __init__(self):
        self._state = {}
        self.request_context = None

    async def get_state(self, key: str):
        return self._state.get(key)

    async def set_state(self, key: str, value):
        self._state[key] = value


@pytest.mark.asyncio
async def test_get_client_from_context_supports_sync_state_api(monkeypatch):
    """Should work with FastMCP v2-style sync state APIs."""
    ctx = SyncContext()

    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_pt_sync_key")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://example.com/")

    captured = {}

    def fake_client_factory(api_key, workspace_id=None, endpoint=None):
        captured["api_key"] = api_key
        captured["workspace_id"] = workspace_id
        captured["endpoint"] = endpoint
        return DummyClient(api_key=api_key, api_url=endpoint)

    monkeypatch.setattr(helpers, "get_langsmith_client_from_api_key", fake_client_factory)

    client = await helpers.get_client_from_context(ctx)

    assert isinstance(client, DummyClient)
    assert captured["api_key"] == "lsv2_pt_sync_key"
    assert captured["endpoint"] == "https://example.com/"


@pytest.mark.asyncio
async def test_get_client_from_context_supports_async_state_api(monkeypatch):
    """Should work with FastMCP v3-style async state APIs."""
    ctx = AsyncContext()

    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_pt_async_key")
    monkeypatch.delenv("LANGSMITH_ENDPOINT", raising=False)

    captured = {}

    def fake_client_factory(api_key, workspace_id=None, endpoint=None):
        captured["api_key"] = api_key
        captured["workspace_id"] = workspace_id
        captured["endpoint"] = endpoint
        return DummyClient(api_key=api_key, api_url=endpoint)

    monkeypatch.setattr(helpers, "get_langsmith_client_from_api_key", fake_client_factory)

    client = await helpers.get_client_from_context(ctx)

    assert isinstance(client, DummyClient)
    assert captured["api_key"] == "lsv2_pt_async_key"
    assert captured["endpoint"] is None


@pytest.mark.asyncio
async def test_get_api_key_and_endpoint_from_context_sync_and_async(monkeypatch):
    """API key/endpoint helper should work for both context styles without raising."""
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_pt_shared")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com/")

    def fake_client_factory(api_key, workspace_id=None, endpoint=None):
        return DummyClient(api_key=api_key, api_url=endpoint)

    monkeypatch.setattr(helpers, "get_langsmith_client_from_api_key", fake_client_factory)

    sync_ctx = SyncContext()
    async_ctx = AsyncContext()

    sync_result = await helpers.get_api_key_and_endpoint_from_context(sync_ctx)
    async_result = await helpers.get_api_key_and_endpoint_from_context(async_ctx)

    assert sync_result == ("None", "https://api.smith.langchain.com")
    assert async_result == ("None", "https://api.smith.langchain.com")
