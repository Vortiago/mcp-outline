"""Tests for the scope matching module.

Verifies that the local Python implementation of Outline's
``AuthenticationHelper.canAccess`` algorithm produces the
correct results for route scopes, namespaced scopes, and
edge cases.
"""

import pytest

from mcp_outline.features.dynamic_tools.scope_matching import (
    blocked_tools_for_scopes,
    is_endpoint_accessible,
)

# ------------------------------------------------------------------
# Route scopes (/api/namespace.method)
# ------------------------------------------------------------------


class TestRouteScopes:
    """Route scopes: exact namespace.method matching."""

    def test_exact_match(self):
        assert is_endpoint_accessible(
            "documents.info", ["/api/documents.info"]
        )

    def test_no_match_different_method(self):
        assert not is_endpoint_accessible(
            "documents.create", ["/api/documents.info"]
        )

    def test_no_match_different_namespace(self):
        assert not is_endpoint_accessible(
            "collections.list", ["/api/documents.list"]
        )

    def test_wildcard_method(self):
        assert is_endpoint_accessible("documents.info", ["/api/documents.*"])

    def test_wildcard_namespace(self):
        assert is_endpoint_accessible("documents.info", ["/api/*.info"])

    def test_full_wildcard(self):
        assert is_endpoint_accessible("documents.info", ["/api/*.*"])

    def test_broken_route_scope(self):
        """Route scope without dot separator is skipped."""
        assert not is_endpoint_accessible("documents.info", ["/api/read"])


# ------------------------------------------------------------------
# Namespaced scopes (namespace:level)
# ------------------------------------------------------------------


class TestNamespacedScopes:
    """Namespaced scopes: namespace:level matching."""

    def test_read_grants_list(self):
        assert is_endpoint_accessible("documents.list", ["documents:read"])

    def test_read_grants_info(self):
        assert is_endpoint_accessible("documents.info", ["documents:read"])

    def test_read_grants_search(self):
        assert is_endpoint_accessible("documents.search", ["documents:read"])

    def test_read_grants_export(self):
        assert is_endpoint_accessible("documents.export", ["documents:read"])

    def test_read_grants_config(self):
        assert is_endpoint_accessible("documents.config", ["documents:read"])

    def test_read_grants_documents(self):
        """The ``documents`` method maps to read."""
        assert is_endpoint_accessible(
            "collections.documents", ["collections:read"]
        )

    def test_read_grants_drafts(self):
        assert is_endpoint_accessible("documents.drafts", ["documents:read"])

    def test_read_grants_viewed(self):
        assert is_endpoint_accessible("documents.viewed", ["documents:read"])

    def test_read_blocks_create(self):
        assert not is_endpoint_accessible(
            "documents.create", ["documents:read"]
        )

    def test_read_blocks_update(self):
        assert not is_endpoint_accessible(
            "documents.update", ["documents:read"]
        )

    def test_read_blocks_delete(self):
        assert not is_endpoint_accessible(
            "documents.delete", ["documents:read"]
        )

    def test_read_blocks_archive(self):
        """``archive`` defaults to write scope."""
        assert not is_endpoint_accessible(
            "documents.archive", ["documents:read"]
        )

    def test_write_grants_all(self):
        for method in (
            "list",
            "info",
            "create",
            "update",
            "delete",
            "archive",
            "search",
            "export",
        ):
            assert is_endpoint_accessible(
                f"documents.{method}", ["documents:write"]
            ), f"documents:write should grant documents.{method}"

    def test_create_grants_only_create(self):
        assert is_endpoint_accessible("documents.create", ["documents:create"])

    def test_create_blocks_info(self):
        assert not is_endpoint_accessible(
            "documents.info", ["documents:create"]
        )

    def test_create_blocks_update(self):
        assert not is_endpoint_accessible(
            "documents.update", ["documents:create"]
        )

    def test_wrong_namespace(self):
        assert not is_endpoint_accessible(
            "collections.list", ["documents:read"]
        )

    def test_wildcard_namespace(self):
        """Wildcard namespace matches any namespace."""
        assert is_endpoint_accessible("documents.list", ["*:read"])
        assert is_endpoint_accessible("collections.info", ["*:read"])


# ------------------------------------------------------------------
# Multiple scopes
# ------------------------------------------------------------------


class TestMultipleScopes:
    """Any matching scope grants access."""

    def test_any_match_grants(self):
        assert is_endpoint_accessible(
            "documents.info",
            ["collections:read", "documents:read"],
        )

    def test_none_match_blocks(self):
        assert not is_endpoint_accessible(
            "documents.create",
            ["documents:read", "collections:read"],
        )

    def test_mixed_route_and_namespace(self):
        assert is_endpoint_accessible(
            "documents.info",
            ["/api/collections.list", "documents:read"],
        )

    def test_mixed_all_miss(self):
        assert not is_endpoint_accessible(
            "documents.create",
            [
                "/api/collections.list",
                "documents:read",
            ],
        )


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and unusual inputs."""

    def test_empty_scopes_blocks(self):
        assert not is_endpoint_accessible("documents.info", [])

    def test_unparseable_endpoint_fails_open(self):
        """Endpoint without dot separator → fail-open."""
        assert is_endpoint_accessible("nodot", ["x:read"])

    def test_method_defaults_to_write(self):
        """Unlisted methods default to write scope."""
        assert not is_endpoint_accessible(
            "documents.archive", ["documents:read"]
        )
        assert is_endpoint_accessible("documents.archive", ["documents:write"])

    def test_global_scope_broken(self):
        """Global scopes are skipped (broken in Outline)."""
        assert not is_endpoint_accessible("documents.info", ["read"])


# ------------------------------------------------------------------
# get_blocked_tools
# ------------------------------------------------------------------


class TestBlockedToolsForScopes:
    """Bulk tool blocking via scope matching."""

    @pytest.fixture(autouse=True)
    def _build_map(self):
        from mcp.server.fastmcp import FastMCP

        from mcp_outline.features import register_all
        from mcp_outline.features.dynamic_tools.introspect import (
            build_tool_endpoint_map,
        )

        mcp = FastMCP("scope-test")
        register_all(mcp)
        self.tool_endpoint_map = build_tool_endpoint_map(mcp)

    def test_none_scopes_returns_empty(self):
        assert blocked_tools_for_scopes(None, self.tool_endpoint_map) == set()

    def test_empty_scopes_blocks_all(self):
        """Empty scope list → every tool blocked."""
        assert blocked_tools_for_scopes([], self.tool_endpoint_map) == set(
            self.tool_endpoint_map.keys()
        )

    def test_read_scopes_block_write_tools(self):
        scopes = [
            "documents:read",
            "collections:read",
            "comments:read",
        ]
        blocked = blocked_tools_for_scopes(scopes, self.tool_endpoint_map)
        assert "create_document" in blocked
        assert "update_document" in blocked
        assert "delete_document" in blocked
        # Read tools should not be blocked
        assert "read_document" not in blocked
        assert "search_documents" not in blocked
        assert "list_collections" not in blocked

    def test_write_scopes_block_nothing(self):
        scopes = [
            "documents:write",
            "collections:write",
            "comments:write",
            "attachments:write",
        ]
        blocked = blocked_tools_for_scopes(scopes, self.tool_endpoint_map)
        assert blocked == set()

    def test_single_namespace_blocks_others(self):
        """Only documents:read → collection + comment tools blocked."""
        blocked = blocked_tools_for_scopes(
            ["documents:read"], self.tool_endpoint_map
        )
        assert "list_collections" in blocked
        assert "list_document_comments" in blocked
        assert "read_document" not in blocked
        assert "search_documents" not in blocked

    @pytest.mark.parametrize(
        "scope,tool,accessible",
        [
            (
                "/api/documents.info",
                "read_document",
                True,
            ),
            (
                "/api/documents.info",
                "create_document",
                False,
            ),
            (
                "documents:create",
                "create_document",
                True,
            ),
            (
                "documents:create",
                "read_document",
                False,
            ),
        ],
    )
    def test_scope_tool_combinations(self, scope, tool, accessible):
        blocked = blocked_tools_for_scopes([scope], self.tool_endpoint_map)
        if accessible:
            assert tool not in blocked
        else:
            assert tool in blocked
