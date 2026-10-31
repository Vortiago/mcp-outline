"""Tests for the middleware that turns GitHub Copilot CLI's empty-string
tool arguments into {}."""

from typing import Any

import pytest
from mcp.server.context import ServerRequestContext

from mcp_outline.patches import coerce_empty_tool_arguments


def _context(method: str, params: Any) -> ServerRequestContext:
    """Build a request context with only the fields the middleware reads."""
    return ServerRequestContext(
        session=None,  # type: ignore[arg-type]
        lifespan_context=None,
        protocol_version="2025-11-25",
        method=method,
        params=params,
    )


async def _arguments_seen_by_handler(method: str, params: Any) -> Any:
    """Run the middleware and return the arguments the handler gets."""

    async def call_next(ctx):
        return ctx.params.get("arguments")

    return await coerce_empty_tool_arguments(
        _context(method, params), call_next
    )


@pytest.mark.anyio
async def test_empty_string_arguments_become_empty_dict():
    """Copilot CLI's "" arguments reach the handler as {}."""
    params = {"name": "list_collections", "arguments": ""}
    assert await _arguments_seen_by_handler("tools/call", params) == {}


@pytest.mark.anyio
@pytest.mark.parametrize("arguments", [{}, {"key": "value"}, None])
async def test_valid_arguments_pass_through(arguments):
    """A dict or a missing value reaches the handler unchanged."""
    params = {"name": "list_collections", "arguments": arguments}
    result = await _arguments_seen_by_handler("tools/call", params)
    assert result == arguments


@pytest.mark.anyio
async def test_other_methods_pass_through():
    """Only tools/call is rewritten."""
    params = {"name": "x", "arguments": ""}
    assert await _arguments_seen_by_handler("prompts/get", params) == ""
