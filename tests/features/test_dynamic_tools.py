"""
Tests for dynamic tool list filtering.

Verifies that the ``OUTLINE_DYNAMIC_TOOL_LIST`` feature correctly
filters tools by introspecting API key scopes via ``apiKeys.list``.

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
from mcp_outline.utils.outline_client import OutlineError
from tests.helpers import list_tools_via_handler


@pytest.fixture
def fresh_mcp_server():
    """Create a fresh MCP server instance for testing."""
    return FastMCP("Test Server")


# ------------------------------------------------------------------
# install_dynamic_tool_list
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_disabled_by_default(fresh_mcp_server):
    """Feature is off when env var is unset — handler unchanged."""
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
        assert handler_after is handler_before


@pytest.mark.anyio
async def test_explicitly_enabled(fresh_mcp_server):
    """Feature is on when env var is 'true' — handler re-registered."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
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
            tools = await list_tools_via_handler(fresh_mcp_server)
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
            tools = await list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "create_document" in names
            assert "update_document" in names
            assert "delete_document" in names


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
            tools = await list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "read_document" in names
            assert "create_document" not in names
            assert "update_document" not in names


@pytest.mark.anyio
async def test_graceful_degradation_scope_check_error(
    fresh_mcp_server,
):
    """When get_blocked_tools raises, return all tools (fail-open).

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
            side_effect=Exception("unexpected error"),
        ):
            tools = await list_tools_via_handler(fresh_mcp_server)
            names = {t.name for t in tools}

            # All tools should be returned on error
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
            tools = await list_tools_via_handler(fresh_mcp_server)
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
# get_blocked_tools — scope-based filtering
# ------------------------------------------------------------------


def _mock_key(api_key: str, scope=None, name: str = "test"):
    """Build a mock API key dict matching *api_key*'s last4."""
    return {
        "last4": api_key[-4:],
        "scope": scope,
        "name": name,
    }


@pytest.mark.anyio
async def test_get_blocked_tools_full_access():
    """Key with null scope → full access → empty blocked set."""
    api_key = "key-full-access"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(return_value=[_mock_key(api_key)])

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_read_only_key():
    """Read-only scoped key → write tools blocked."""
    api_key = "key-read-only"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            return_value=[
                _mock_key(
                    api_key,
                    scope=[
                        "documents:read",
                        "collections:read",
                        "comments:read",
                    ],
                )
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert WRITE_TOOL_NAMES <= result


@pytest.mark.anyio
async def test_get_blocked_tools_partial_scope():
    """Scope missing collection write → collection write blocked."""
    api_key = "key-partial"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            return_value=[
                _mock_key(
                    api_key,
                    scope=[
                        "documents:write",
                        "comments:write",
                        "collections:read",
                    ],
                )
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert "create_collection" in result
        assert "update_collection" in result
        assert "delete_collection" in result
        # Document write tools should NOT be blocked
        assert "create_document" not in result
        assert "update_document" not in result


@pytest.mark.anyio
async def test_get_blocked_tools_network_error():
    """OutlineClient constructor fails → empty set (fail-open)."""
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        mock_cls.side_effect = Exception("connection refused")

        result = await get_blocked_tools(
            "key-network-error", "https://example.com/api"
        )
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_no_api_key():
    """No API key → empty set."""
    result = await get_blocked_tools(None, None)
    assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_empty_string_api_key():
    """Empty string API key → empty set (no API call)."""
    result = await get_blocked_tools("", None)
    assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_invalid_key_401():
    """401 from apiKeys.list → block ALL tools."""
    api_key = "key-invalid-401x"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            side_effect=OutlineError(
                "HTTP 401: authentication_required",
                status_code=401,
            )
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert result == set(TOOL_ENDPOINT_MAP.keys())


@pytest.mark.anyio
async def test_get_blocked_tools_403_fail_open():
    """403 from apiKeys.list → fail-open (empty set)."""
    api_key = "key-missing-scope"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            side_effect=OutlineError(
                "HTTP 403: authorization_error",
                status_code=403,
            )
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_key_not_found():
    """Key not found in apiKeys.list → fail-open."""
    api_key = "key-not-found-xxxx"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            return_value=[
                {
                    "last4": "zzzz",
                    "scope": None,
                    "name": "other",
                }
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_pagination():
    """Key found on second page of apiKeys.list results."""
    api_key = "key-on-page-two"
    filler = [
        {
            "last4": f"{i:04d}",
            "scope": None,
            "name": f"k{i}",
        }
        for i in range(100)
    ]
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            side_effect=[
                filler,
                [_mock_key(api_key, scope=["documents:read"])],
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert "create_document" in result
        assert instance.list_api_keys.call_count == 2


@pytest.mark.anyio
async def test_get_blocked_tools_last4_collision_union():
    """Multiple keys with same last4 → scopes combined (union)."""
    api_key = "key-collision-test"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            return_value=[
                {
                    "last4": api_key[-4:],
                    "scope": ["documents:read"],
                    "name": "key-a",
                },
                {
                    "last4": api_key[-4:],
                    "scope": ["collections:read"],
                    "name": "key-b",
                },
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        # documents:read tools should NOT be blocked
        assert "read_document" not in result
        assert "search_documents" not in result
        # collections:read tools should NOT be blocked
        assert "list_collections" not in result
        # Write tools should still be blocked
        assert "create_document" in result
        assert "create_collection" in result


@pytest.mark.anyio
async def test_get_blocked_tools_last4_collision_null_wins():
    """If any colliding key has null scope, result is full access."""
    api_key = "key-null-wins-test"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            return_value=[
                {
                    "last4": api_key[-4:],
                    "scope": ["documents:read"],
                    "name": "key-scoped",
                },
                {
                    "last4": api_key[-4:],
                    "scope": None,
                    "name": "key-admin",
                },
            ]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        # null scope = full access → nothing blocked
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_last4_collision_across_pages():
    """Collision across pagination pages → scopes combined."""
    api_key = "key-cross-page-test"
    page1 = [
        {
            "last4": api_key[-4:],
            "scope": ["documents:read"],
            "name": "key-page1",
        },
        *[
            {
                "last4": f"{i:04d}",
                "scope": None,
                "name": f"filler-{i}",
            }
            for i in range(99)
        ],
    ]
    page2 = [
        {
            "last4": api_key[-4:],
            "scope": ["collections:read"],
            "name": "key-page2",
        },
    ]
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.list_api_keys = AsyncMock(
            side_effect=[page1, page2],
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        # Both pages' scopes should be combined
        assert "read_document" not in result
        assert "list_collections" not in result
        # Write tools still blocked
        assert "create_document" in result
        assert instance.list_api_keys.call_count == 2


@pytest.mark.anyio
async def test_enabled_values():
    """Feature should activate for 'true', '1', and 'yes'."""
    for val in ("true", "True", "TRUE", "1", "yes", "Yes"):
        mcp = FastMCP("Test")
        with patch.dict(
            os.environ,
            {"OUTLINE_DYNAMIC_TOOL_LIST": val},
        ):
            register_all(mcp)
            handler_before = mcp._mcp_server.request_handlers[ListToolsRequest]
            install_dynamic_tool_list(mcp)
            handler_after = mcp._mcp_server.request_handlers[ListToolsRequest]
            assert handler_after is not handler_before, (
                f"Expected enabled for value '{val}'"
            )


# ------------------------------------------------------------------
# get_blocked_tools — role-based filtering (auth.info)
# ------------------------------------------------------------------


def _mock_auth_info(role: str):
    """Build an AsyncMock returning auth.info with *role*."""
    return AsyncMock(return_value={"user": {"role": role}})


@pytest.mark.anyio
async def test_get_blocked_tools_viewer_role():
    """Viewer role + full-access key → write tools blocked."""
    api_key = "key-viewer-role"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_auth_info = _mock_auth_info("viewer")
        instance.list_api_keys = AsyncMock(return_value=[_mock_key(api_key)])

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert WRITE_TOOL_NAMES <= result


@pytest.mark.anyio
async def test_get_blocked_tools_member_role():
    """Member role + full-access key → nothing blocked."""
    api_key = "key-member-role"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_auth_info = _mock_auth_info("member")
        instance.list_api_keys = AsyncMock(return_value=[_mock_key(api_key)])

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert result == set()


@pytest.mark.anyio
async def test_get_blocked_tools_auth_info_fails_scope_works():
    """auth.info error → scope check still applied."""
    api_key = "key-auth-fail"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_auth_info = AsyncMock(
            side_effect=OutlineError("auth.info failed")
        )
        instance.list_api_keys = AsyncMock(
            return_value=[_mock_key(api_key, scope=["documents:read"])]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert "create_document" in result


@pytest.mark.anyio
async def test_get_blocked_tools_scope_fails_role_works():
    """apiKeys.list error → role check still applied."""
    api_key = "key-scope-fail"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_auth_info = _mock_auth_info("viewer")
        instance.list_api_keys = AsyncMock(
            side_effect=Exception("network error")
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        assert WRITE_TOOL_NAMES <= result


@pytest.mark.anyio
async def test_get_blocked_tools_viewer_plus_scope_union():
    """Viewer + scoped key → union of both blocked sets."""
    api_key = "key-viewer-scoped"
    with patch(
        "mcp_outline.features.dynamic_tools.filtering.OutlineClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_auth_info = _mock_auth_info("viewer")
        instance.list_api_keys = AsyncMock(
            return_value=[_mock_key(api_key, scope=["documents:read"])]
        )

        result = await get_blocked_tools(api_key, "https://example.com/api")
        # Write tools from role check
        assert WRITE_TOOL_NAMES <= result
        # Scope-blocked read tools too
        assert "export_all_collections" in result
