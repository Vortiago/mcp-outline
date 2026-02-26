"""
Tests for dynamic tool list filtering.

Verifies that the ``OUTLINE_DYNAMIC_TOOL_LIST`` feature correctly
filters tools based on the authenticated user's Outline role and
API-key scopes.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all
from mcp_outline.features.dynamic_tools import (
    WRITE_TOOL_NAMES,
    _get_user_permissions,
    _has_write_endpoint_scope,
    _has_write_scope,
    install_dynamic_tool_list,
)


@pytest.fixture
def fresh_mcp_server():
    """Create a fresh MCP server instance for testing."""
    return FastMCP("Test Server")


# ------------------------------------------------------------------
# install_dynamic_tool_list
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_disabled_by_default(fresh_mcp_server):
    """Feature is off when env var is unset — list_tools unchanged."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OUTLINE_DYNAMIC_TOOL_LIST", None)
        register_all(fresh_mcp_server)

        install_dynamic_tool_list(fresh_mcp_server)

        # When disabled, no instance-level override is set
        assert "list_tools" not in fresh_mcp_server.__dict__


@pytest.mark.anyio
async def test_viewer_sees_only_read_tools(fresh_mcp_server):
    """Viewer-role user should not see write tools."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools._get_user_permissions",
            new_callable=AsyncMock,
            return_value={
                "role": "viewer",
                "can_write": False,
            },
        ):
            tools = await fresh_mcp_server.list_tools()
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
    """Member-role user should see all tools."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools._get_user_permissions",
            new_callable=AsyncMock,
            return_value={
                "role": "member",
                "can_write": True,
            },
        ):
            tools = await fresh_mcp_server.list_tools()
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "create_document" in names
            assert "update_document" in names
            assert "delete_document" in names


@pytest.mark.anyio
async def test_admin_sees_all_tools(fresh_mcp_server):
    """Admin-role user should see all tools."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools._get_user_permissions",
            new_callable=AsyncMock,
            return_value={
                "role": "admin",
                "can_write": True,
            },
        ):
            tools = await fresh_mcp_server.list_tools()
            names = {t.name for t in tools}

            assert "create_document" in names
            assert "update_document" in names
            assert "search_documents" in names


@pytest.mark.anyio
async def test_scoped_key_without_write(fresh_mcp_server):
    """Member with read-only scoped key should not see write tools."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools._get_user_permissions",
            new_callable=AsyncMock,
            return_value={
                "role": "member",
                "can_write": False,
            },
        ):
            tools = await fresh_mcp_server.list_tools()
            names = {t.name for t in tools}

            assert "search_documents" in names
            assert "read_document" in names
            assert "create_document" not in names
            assert "update_document" not in names


@pytest.mark.anyio
async def test_graceful_degradation_auth_failure(
    fresh_mcp_server,
):
    """When auth.info fails, return all tools (fail-open)."""
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
            "mcp_outline.features.dynamic_tools._get_user_permissions",
            new_callable=AsyncMock,
            return_value={
                "role": None,
                "can_write": True,
            },
        ):
            tools = await fresh_mcp_server.list_tools()
            names = {t.name for t in tools}

            # All tools should be returned
            assert "create_document" in names
            assert "search_documents" in names


@pytest.mark.anyio
async def test_graceful_degradation_no_api_key(
    fresh_mcp_server,
):
    """When no API key is available, return all tools."""
    with patch.dict(
        os.environ,
        {"OUTLINE_DYNAMIC_TOOL_LIST": "true"},
    ):
        os.environ.pop("OUTLINE_API_KEY", None)
        register_all(fresh_mcp_server)
        install_dynamic_tool_list(fresh_mcp_server)

        with patch(
            "mcp_outline.features.dynamic_tools._get_header_api_key",
            return_value=None,
        ):
            tools = await fresh_mcp_server.list_tools()
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
# _get_user_permissions
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_user_permissions_viewer_role():
    """Viewer role should yield can_write=False."""
    mock_response = {
        "data": {"user": {"role": "viewer"}},
        "policies": [],
    }
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(return_value=mock_response)

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["role"] == "viewer"
        assert result["can_write"] is False


@pytest.mark.anyio
async def test_get_user_permissions_member_role():
    """Member role with policies should yield can_write=True."""
    mock_response = {
        "data": {"user": {"role": "member"}},
        "policies": [
            {
                "abilities": {
                    "read": True,
                    "createDocument": True,
                    "update": True,
                }
            }
        ],
    }
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(return_value=mock_response)

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["role"] == "member"
        assert result["can_write"] is True


@pytest.mark.anyio
async def test_get_user_permissions_scoped_read_only():
    """Member with read-only scoped key should be can_write=False."""
    mock_response = {
        "data": {
            "user": {"role": "member"},
            "apiKey": {"scope": "documents.list documents.info"},
        },
        "policies": [{"abilities": {"read": True}}],
    }
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(return_value=mock_response)

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["role"] == "member"
        assert result["can_write"] is False


@pytest.mark.anyio
async def test_get_user_permissions_error_returns_full():
    """On error, should return can_write=True (fail-open)."""
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(
            side_effect=Exception("network error")
        )

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["can_write"] is True


@pytest.mark.anyio
async def test_get_user_permissions_no_api_key():
    """No API key should return can_write=True."""
    result = await _get_user_permissions(None, None)
    assert result["can_write"] is True


# ------------------------------------------------------------------
# _has_write_scope (policies)
# ------------------------------------------------------------------


def test_has_write_scope_empty_policies():
    """Empty policies → assume full access."""
    assert _has_write_scope([]) is True


def test_has_write_scope_with_create():
    """Policies with createDocument ability → write access."""
    policies = [{"abilities": {"createDocument": True, "read": True}}]
    assert _has_write_scope(policies) is True


def test_has_write_scope_read_only():
    """Policies with only read ability → no write access."""
    policies = [{"abilities": {"read": True}}]
    assert _has_write_scope(policies) is False


def test_has_write_scope_with_update():
    """Policies with update ability → write access."""
    policies = [{"abilities": {"update": True}}]
    assert _has_write_scope(policies) is True


# ------------------------------------------------------------------
# _has_write_endpoint_scope (API key scopes)
# ------------------------------------------------------------------


def test_has_write_endpoint_scope_none():
    """No scopes → unscoped key has full access."""
    assert _has_write_endpoint_scope(None) is True


def test_has_write_endpoint_scope_empty():
    """Empty string scopes → full access."""
    assert _has_write_endpoint_scope("") is True


def test_has_write_endpoint_scope_read_only():
    """Read-only scopes → no write access."""
    assert (
        _has_write_endpoint_scope(
            "documents.list documents.info collections.list"
        )
        is False
    )


def test_has_write_endpoint_scope_with_create():
    """Scopes including documents.create → write access."""
    assert _has_write_endpoint_scope("documents.list documents.create") is True


def test_has_write_endpoint_scope_wildcard():
    """Global write scope → write access."""
    assert _has_write_endpoint_scope("write") is True


def test_has_write_endpoint_scope_star():
    """Star wildcard → write access."""
    assert _has_write_endpoint_scope("*") is True


def test_has_write_endpoint_scope_documents_prefix():
    """Broad 'documents' prefix covers documents.create."""
    assert _has_write_endpoint_scope("documents") is True


def test_has_write_endpoint_scope_partial_prefix_rejected():
    """Short prefix that isn't a dot-boundary must NOT match."""
    # "doc" is a prefix of "documents.create" but not at a
    # dot boundary — it should NOT grant write access.
    assert _has_write_endpoint_scope("doc") is False
    assert _has_write_endpoint_scope("d") is False
    assert _has_write_endpoint_scope("document") is False
    assert _has_write_endpoint_scope("coll") is False
    assert _has_write_endpoint_scope("comment") is False


def test_has_write_endpoint_scope_exact_endpoint_match():
    """Exact endpoint match should grant write access."""
    assert _has_write_endpoint_scope("documents.create") is True
    assert _has_write_endpoint_scope("collections.delete") is True


def test_has_write_endpoint_scope_sub_endpoint():
    """Scope more specific than a write prefix is accepted."""
    # e.g. "documents.create.bulk" starts with "documents.create."
    assert _has_write_endpoint_scope("documents.create.bulk") is True


# ------------------------------------------------------------------
# _get_user_permissions — cross-layer AND logic
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_user_permissions_admin_read_only_scope():
    """Admin role + read-only scoped key → can_write=False.

    The AND logic means the most restrictive layer wins:
    role says yes, scope says no → no write.
    """
    mock_response = {
        "data": {
            "user": {"role": "admin"},
            "apiKey": {"scope": "documents.list documents.info"},
        },
        "policies": [
            {
                "abilities": {
                    "read": True,
                    "createDocument": True,
                    "update": True,
                }
            }
        ],
    }
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(return_value=mock_response)

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["role"] == "admin"
        assert result["can_write"] is False


@pytest.mark.anyio
async def test_get_user_permissions_viewer_write_scope():
    """Viewer role + write scoped key → can_write=False.

    Role says no, scope says yes → no write.
    """
    mock_response = {
        "data": {
            "user": {"role": "viewer"},
            "apiKey": {"scope": "documents.list documents.create"},
        },
        "policies": [
            {
                "abilities": {
                    "read": True,
                    "createDocument": True,
                }
            }
        ],
    }
    with patch("mcp_outline.features.dynamic_tools.OutlineClient") as mock_cls:
        instance = mock_cls.return_value
        instance.auth_info_full = AsyncMock(return_value=mock_response)

        result = await _get_user_permissions(
            "test-key", "https://example.com/api"
        )
        assert result["role"] == "viewer"
        assert result["can_write"] is False


@pytest.mark.anyio
async def test_enabled_values(fresh_mcp_server):
    """Feature should activate for 'true', '1', and 'yes'."""
    for val in ("true", "True", "TRUE", "1", "yes", "Yes"):
        mcp = FastMCP("Test")
        with patch.dict(
            os.environ,
            {"OUTLINE_DYNAMIC_TOOL_LIST": val},
        ):
            register_all(mcp)
            original = mcp.list_tools
            install_dynamic_tool_list(mcp)
            assert mcp.list_tools is not original, (
                f"Expected enabled for value '{val}'"
            )
