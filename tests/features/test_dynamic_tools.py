"""
Tests for dynamic tool list filtering.

Verifies that the ``OUTLINE_DYNAMIC_TOOL_LIST`` feature correctly
filters tools by probing Outline API endpoints for 401.

**Important**: filtering tests call ``list_tools`` through the
lowlevel MCP handler (``_mcp_server.request_handlers``), which is
the code path real MCP clients hit.  Calling
``mcp.list_tools()`` directly would only exercise the instance
attribute — which can diverge from the registered handler.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import ListToolsRequest

from mcp_outline.features import register_all
from mcp_outline.features.dynamic_tools import (
    TOOL_ENDPOINT_MAP,
    WRITE_TOOL_NAMES,
    get_blocked_tools,
    install_dynamic_tool_list,
)


@pytest.fixture
def fresh_mcp_server():
    """Create a fresh MCP server instance for testing."""
    return FastMCP("Test Server")


async def _list_tools_via_handler(mcp_server):
    """Call list_tools through the lowlevel MCP protocol handler.

    This is the code path real MCP clients use (``tools/list``
    JSON-RPC request).  The handler is registered during
    ``FastMCP.__init__`` and may differ from the instance-level
    ``mcp.list_tools`` attribute that ``install_dynamic_tool_list``
    patches.
    """
    handler = mcp_server._mcp_server.request_handlers[ListToolsRequest]
    server_result = await handler(ListToolsRequest())
    return server_result.root.tools


# ------------------------------------------------------------------
# install_dynamic_tool_list
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_enabled_by_default(fresh_mcp_server):
    """Feature is on when env var is unset — handler re-registered."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OUTLINE_DYNAMIC_TOOL_LIST", None)
        register_all(fresh_mcp_server)

        handler_before = fresh_mcp_server._mcp_server.request_handlers[
            ListToolsRequest
        ]

        install_dynamic_tool_list(fresh_mcp_server)

        handler_after = fresh_mcp_server._mcp_server.request_handlers[
            ListToolsRequest
        ]
        assert handler_after is not handler_before


@pytest.mark.anyio
async def test_explicitly_disabled(fresh_mcp_server):
    """Feature is off when env var is 'false' — handler unchanged."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "false"},
    ):
        register_all(fresh_mcp_server)

        handler_before = fresh_mcp_server._mcp_server.request_handlers[
            ListToolsRequest
        ]

        install_dynamic_tool_list(fresh_mcp_server)

        handler_after = fresh_mcp_server._mcp_server.request_handlers[
            ListToolsRequest
        ]
        assert handler_after is handler_before


@pytest.mark.anyio
async def test_viewer_sees_only_read_tools(fresh_mcp_server):
    """Blocked write tools should not appear in tool list.

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering.get_blocked_tools",
            new_callable=AsyncMock,
            return_value=WRITE_TOOL_NAMES,
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            # Read tools present
            assert "search_documents" in names
            assert "read_document" in names
            assert "list_collections" in names
            assert "export_collection" in names

            # Write tools absent
            assert "create_document" not in names
            assert "update_document" not in names
            assert "delete_document" not in names
            assert "move_document" not in names
            assert "batch_archive_documents" not in names


@pytest.mark.anyio
async def test_member_sees_all_tools(fresh_mcp_server):
    """No blocked tools → all tools visible.

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering.get_blocked_tools",
            new_callable=AsyncMock,
            return_value=set(),
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "create_document" in names
            assert "update_document" in names
            assert "delete_document" in names


@pytest.mark.anyio
async def test_admin_sees_all_tools(fresh_mcp_server):
    """Admin (no blocked tools) should see all tools.

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering.get_blocked_tools",
            new_callable=AsyncMock,
            return_value=set(),
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "create_document" in names
            assert "update_document" in names
            assert "search_documents" in names


@pytest.mark.anyio
async def test_scoped_key_without_write(fresh_mcp_server):
    """Scoped key blocking write endpoints hides write tools.

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering.get_blocked_tools",
            new_callable=AsyncMock,
            return_value=WRITE_TOOL_NAMES,
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "read_document" in names
            assert "create_document" not in names
            assert "update_document" not in names


@pytest.mark.anyio
async def test_graceful_degradation_auth_failure(
    fresh_mcp_server,
):
    """When probing fails, return all tools (fail-open).

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {
            "OUTLINE_DYNAMIC_TOOL_LIST": "true",
            "OUTLINE_API_KEY": "some-key",
        },
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering.get_blocked_tools",
            new_callable=AsyncMock,
            return_value=set(),
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            # All tools should be returned
            assert "create_document" in names
            assert "search_documents" in names


@pytest.mark.anyio
async def test_graceful_degradation_no_api_key(
    fresh_mcp_server,
):
    """When no API key is available, return all tools.

    Uses the lowlevel handler path to match real MCP clients.
    """
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        os.environ.pop("OUTLINE_API_KEY", None)
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools.filtering._get_header_api_key",
            return_value=None,
        ):
            tools = await _list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "create_document" in names
            assert "search_documents" in names


# ------------------------------------------------------------------
# WRITE_TOOL_NAMES completeness
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_write_tool_names_matches_annotations(
    fresh_mcp_server,
):
    """WRITE_TOOL_NAMES must match tools with readOnlyHint=False."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    write_tools_from_annotations = set()
    for tool in tools:
        if (
            tool.annotations is not None
            and tool.annotations.readOnlyHint is False
        ):
            write_tools_from_annotations.add(tool.name)

    assert WRITE_TOOL_NAMES == write_tools_from_annotations, (
        f"WRITE_TOOL_NAMES mismatch.\n"
        f"  In WRITE_TOOL_NAMES but not annotated: "
        f"{WRITE_TOOL_NAMES - write_tools_from_annotations}\n"
        f"  Annotated but not in WRITE_TOOL_NAMES: "
        f"{write_tools_from_annotations - WRITE_TOOL_NAMES}"
    )


# ------------------------------------------------------------------
# TOOL_ENDPOINT_MAP completeness
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_tool_endpoint_map_covers_all_tools(
    fresh_mcp_server,
):
    """Every registered tool must have a TOOL_ENDPOINT_MAP entry."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()
    registered = {t.name for t in tools}

    mapped = set(TOOL_ENDPOINT_MAP.keys())
    missing = registered - mapped
    extra = mapped - registered

    assert not missing, (
        f"Tools registered but missing from TOOL_ENDPOINT_MAP: {missing}"
    )
    assert not extra, f"Tools in TOOL_ENDPOINT_MAP but not registered: {extra}"


# ------------------------------------------------------------------
# _get_blocked_tools
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_blocked_tools_full_access():
    """All probes return non-401 → empty blocked set."""
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.probe_endpoint = AsyncMock(return_value=True)

        result = await get_blocked_tools("test-key", "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_read_only_key():
    """Write probes return 401 → write tool names blocked."""
    # Build the set of write endpoints
    write_endpoints = {TOOL_ENDPOINT_MAP[t] for t in WRITE_TOOL_NAMES}

    async def _probe(endpoint):
        return endpoint not in write_endpoints

    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.probe_endpoint = AsyncMock(side_effect=_probe)

        result = await get_blocked_tools("test-key", "https://example.com/api")
        # All write tools should be blocked
        assert WRITE_TOOL_NAMES <= result


@pytest.mark.anyio
async def test_get_blocked_tools_partial_scope():
    """Only collection endpoints blocked → only collection tools."""
    blocked_endpoints = {
        "collections.create",
        "collections.update",
        "collections.delete",
    }

    async def _probe(endpoint):
        return endpoint not in blocked_endpoints

    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.probe_endpoint = AsyncMock(side_effect=_probe)

        result = await get_blocked_tools("test-key", "https://example.com/api")
        assert "create_collection" in result
        assert "update_collection" in result
        assert "delete_collection" in result
        # Document write tools should NOT be blocked
        assert "create_document" not in result
        assert "update_document" not in result


@pytest.mark.anyio
async def test_get_blocked_tools_network_error():
    """All probes fail (network error) → empty set (fail-open)."""
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        mock_cls.side_effect = Exception("connection refused")

        result = await get_blocked_tools("test-key", "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_no_api_key():
    """No API key → empty set."""
    result = await get_blocked_tools(None, None)
    assert result == set()


@pytest.mark.anyio
async def test_disabled_values(fresh_mcp_server):
    """Feature should deactivate for 'false', '0', and 'no'."""
    for val in ("false", "False", "FALSE", "0", "no", "No"):
        mcp = FastMCP("Test")
        with patch.dict(
            os.environ,
            {"OUTLINE_DYNAMIC_TOOL_LIST": val},
        ):
            register_all(mcp)
            handler_before = mcp._mcp_server.request_handlers[ListToolsRequest]
            install_dynamic_tool_list(mcp)
            handler_after = mcp._mcp_server.request_handlers[ListToolsRequest]
            assert handler_after is handler_before, (
                f"Expected disabled for value '{val}'"
            )
