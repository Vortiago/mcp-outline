"""E2E tests for the dynamic tool list feature.

Verifies that ``OUTLINE_DYNAMIC_TOOL_LIST=true`` correctly filters
the MCP ``tools/list`` response based on API key scope.

The feature introspects scopes via the ``apiKeys.list`` endpoint.
Scoped API keys must include ``apiKeys.list`` in their scope array
for introspection to work.

Tests run against a real Outline instance via Docker Compose.
All assertions use **exact set matching** to catch both missing
and leaked tools.

**Transports tested**:

- **stdio** — each test spawns a fresh subprocess with the scoped
  API key in ``OUTLINE_API_KEY``.  The ``stdio_client`` context
  manager handles lifecycle; no manual subprocess management.
- **streamable-http** — one module-scoped server verifies that
  per-request ``x-outline-api-key`` header filtering works.

Scope types tested:

- **Invalid key** — apiKeys.list returns 401 -> no tools
- **Full-access key** — null scope -> all tools
- **Route scopes** — explicit ``namespace.method`` entries
- **Namespaced scopes** — ``namespace:level`` (read/write/create)
- **Mixed scopes** — combination of namespace and route entries
"""

import os
import subprocess
import sys
import time

import httpx
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all
from mcp_outline.features.dynamic_tools.introspect import (
    build_tool_endpoint_map,
)

from .conftest import _create_api_key
from .helpers import OUTLINE_URL

HTTP_PORT = 3997
HTTP_BASE = f"http://127.0.0.1:{HTTP_PORT}"
STARTUP_TIMEOUT = 15  # seconds

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


# -------------------------------------------------------------------
# Expected tool sets — derived from source-of-truth maps
# -------------------------------------------------------------------


def _build_expected_tools():
    """Build expected tool sets by introspecting registered tools."""
    _mcp = FastMCP("tool-set-builder")
    register_all(_mcp)
    endpoint_map = build_tool_endpoint_map(_mcp)
    all_tools = set(endpoint_map) - {"ask_ai_about_documents"}
    return all_tools


# All tools registered when AI tools are disabled.
ALL_TOOLS = _build_expected_tools()


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _stdio_env(api_key: str) -> dict:
    """Build a clean env dict for a stdio MCP subprocess."""
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("OUTLINE_") and not k.startswith("MCP_")
    }
    env["MCP_TRANSPORT"] = "stdio"
    env["OUTLINE_API_KEY"] = api_key
    env["OUTLINE_API_URL"] = f"{OUTLINE_URL}/api"
    env["OUTLINE_DYNAMIC_TOOL_LIST"] = "true"
    env["OUTLINE_DISABLE_AI_TOOLS"] = "true"
    return env


async def _list_tools_stdio(api_key: str) -> set[str]:
    """List tool names via a stdio MCP session.

    Spawns a fresh subprocess, initialises, calls ``list_tools``,
    and tears down.  The ``stdio_client`` context manager handles
    all subprocess lifecycle.
    """
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_outline"],
        env=_stdio_env(api_key),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return {t.name for t in result.tools}


def _assert_tools(
    actual: set[str],
    expected: set[str],
    label: str,
) -> None:
    """Assert exact tool set match with a clear diff message."""
    assert actual == expected, (
        f"Tool set mismatch for {label}.\n"
        f"  Missing (expected but absent): "
        f"{expected - actual or 'none'}\n"
        f"  Extra (present but unexpected): "
        f"{actual - expected or 'none'}"
    )


# -------------------------------------------------------------------
# Streamable-HTTP helpers (one server for header tests)
# -------------------------------------------------------------------


def _wait_for_server(base_url: str, timeout: float) -> bool:
    """Poll ``/health`` until 200 or *timeout*."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.25)
    return False


def _start_http_server(api_key: str) -> subprocess.Popen:
    """Start the MCP server in streamable-http mode."""
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("OUTLINE_") and not k.startswith("MCP_")
    }
    env["MCP_TRANSPORT"] = "streamable-http"
    env["MCP_HOST"] = "127.0.0.1"
    env["MCP_PORT"] = str(HTTP_PORT)
    env["OUTLINE_API_KEY"] = api_key
    env["OUTLINE_API_URL"] = f"{OUTLINE_URL}/api"
    env["OUTLINE_DYNAMIC_TOOL_LIST"] = "true"
    env["OUTLINE_DISABLE_AI_TOOLS"] = "true"
    kwargs: dict = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "env": env,
    }
    # On Windows, CREATE_NEW_PROCESS_GROUP allows reliable
    # termination without hanging on pipe reads.
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(
        [sys.executable, "-m", "mcp_outline"],
        **kwargs,
    )


def _stop(process: subprocess.Popen) -> None:
    """Terminate a server subprocess."""
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


async def _list_tools_http(api_key: str) -> set[str]:
    """List tool names via streamable-http with per-request key."""
    http_client = httpx.AsyncClient(
        headers={"x-outline-api-key": api_key},
        timeout=httpx.Timeout(30.0, read=300.0),
    )
    async with streamable_http_client(
        url=f"{HTTP_BASE}/mcp",
        http_client=http_client,
    ) as (read, write, _):
        async with ClientSession(read, write) as s:
            await s.initialize()
            result = await s.list_tools()
            return {t.name for t in result.tools}


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture(scope="module")
def _http_server(outline_stack):
    """Start one streamable-http MCP server for header tests."""
    process = _start_http_server(api_key="e2e-placeholder-key")
    ready = _wait_for_server(HTTP_BASE, STARTUP_TIMEOUT)
    assert ready, f"HTTP server did not start within {STARTUP_TIMEOUT}s"
    yield
    _stop(process)


# -------------------------------------------------------------------
# Stdio tests — scope filtering via OUTLINE_API_KEY
# -------------------------------------------------------------------


async def test_invalid_key_returns_no_tools(outline_stack):
    """Invalid API key -> apiKeys.list returns 401 -> 0 tools.

    Guards against: tools leaking through when the key is
    completely invalid.
    """
    names = await _list_tools_stdio("totally-invalid-key-12345")
    _assert_tools(names, set(), "invalid key")


async def test_admin_key_returns_all_tools(
    outline_stack,
    outline_api_key,
):
    """Full-access admin key -> null scope -> all tools.

    Uses exact set matching to detect both missing and leaked
    tools.
    """
    names = await _list_tools_stdio(outline_api_key)
    _assert_tools(names, ALL_TOOLS, "admin key")


async def test_route_scoped_read_only(
    outline_stack,
    outline_access_token,
):
    """Route-scoped key with all read endpoints -> only read tools.

    Scope: explicit ``namespace.method`` entries for every
    read-only endpoint in the TOOL_ENDPOINT_MAP.
    """
    key = _create_api_key(
        outline_access_token,
        "e2e-stdio-route-read-only",
        [
            "apiKeys.list",
            "documents.info",
            "documents.export",
            "documents.search",
            "documents.list",
            "collections.list",
            "collections.documents",
            "collections.export",
            "collections.export_all",
            "attachments.redirect",
            "comments.list",
            "comments.info",
            "documents.archived",
            "documents.deleted",
        ],
        skip_on_error=True,
    )

    expected = {
        "read_document",
        "get_document_toc",
        "read_document_section",
        "export_document",
        "search_documents",
        "get_document_id_from_title",
        "list_collections",
        "get_collection_structure",
        "export_collection",
        "export_all_collections",
        "list_document_comments",
        "get_comment",
        "get_document_backlinks",
        "get_attachment_url",
        "fetch_attachment",
        "list_document_attachments",
        "list_archived_documents",
        "list_trash",
    }

    names = await _list_tools_stdio(key)
    _assert_tools(names, expected, "route-scoped read-only")


async def test_namespace_read_scope(
    outline_stack,
    outline_access_token,
):
    """Namespaced read scopes -> only methods that map to ``read``.

    Scope: ``documents:read``, ``collections:read``,
    ``comments:read``, ``apiKeys.list``

    Outline's ``methodToScope`` mapping classifies methods as
    ``read`` (list, info, search, export, documents, drafts,
    viewed, config) or ``write`` (everything else).

    Notably, ``documents.archived`` and ``documents.deleted``
    default to ``write`` and are excluded by ``:read`` scopes.
    Attachment tools (``attachments.redirect``) also default to
    ``write`` and require ``attachments:write`` or an explicit
    route scope.  ``collections.export_all`` likewise defaults
    to ``write`` and needs ``collections:write`` or a route scope.
    """
    key = _create_api_key(
        outline_access_token,
        "e2e-stdio-namespace-read",
        [
            "apiKeys.list",
            "documents:read",
            "collections:read",
            "comments:read",
        ],
        skip_on_error=True,
    )

    expected = {
        "read_document",  # documents.info
        "get_document_toc",  # documents.info
        "read_document_section",  # documents.info
        "export_document",  # documents.export
        "search_documents",  # documents.search
        "get_document_id_from_title",  # documents.search
        "get_document_backlinks",  # documents.list
        "list_document_attachments",  # documents.info
        "list_collections",  # collections.list
        "get_collection_structure",  # collections.documents
        "export_collection",  # collections.export
        # export_all_collections excluded: export_all defaults to write
        "list_document_comments",  # comments.list
        "get_comment",  # comments.info
    }

    names = await _list_tools_stdio(key)
    _assert_tools(names, expected, "namespace read scope")


async def test_namespace_write_documents_only(
    outline_stack,
    outline_access_token,
):
    """``documents:write`` grants ALL document methods, nothing else.

    The ``write`` level matches every method regardless of
    ``methodToScope``, granting both read and write operations
    on documents.  Collection, comment, and attachment tools
    stay blocked (attachment tools now map to the ``attachments``
    namespace).
    """
    key = _create_api_key(
        outline_access_token,
        "e2e-stdio-namespace-write-docs",
        ["apiKeys.list", "documents:write"],
        skip_on_error=True,
    )

    expected = {
        # Read document tools
        "read_document",
        "get_document_toc",
        "read_document_section",
        "export_document",
        "search_documents",
        "get_document_id_from_title",
        "get_document_backlinks",
        "list_document_attachments",
        "list_archived_documents",
        "list_trash",
        # Write document tools
        "create_document",
        "update_document",
        "edit_document",
        "archive_document",
        "unarchive_document",
        "delete_document",
        "restore_document",
        "move_document",
        "batch_create_documents",
        "batch_update_documents",
        "batch_move_documents",
        "batch_archive_documents",
        "batch_delete_documents",
    }

    names = await _list_tools_stdio(key)
    _assert_tools(names, expected, "namespace write documents")


async def test_mixed_namespace_and_route_scope(
    outline_stack,
    outline_access_token,
):
    """Mix of namespace and route scopes in one API key.

    Scope: ``documents:read`` (namespace) +
           ``collections.create`` + ``collections.list`` (route)

    The namespace scope grants broad document read access.
    The route scopes grant two specific collection operations.
    Attachment, export, comment, and other write tools are
    blocked.
    """
    key = _create_api_key(
        outline_access_token,
        "e2e-stdio-mixed-scope",
        [
            "apiKeys.list",
            "documents:read",
            "collections.create",
            "collections.list",
        ],
        skip_on_error=True,
    )

    expected = {
        # Document read tools (from documents:read)
        "read_document",
        "get_document_toc",
        "read_document_section",
        "export_document",
        "search_documents",
        "get_document_id_from_title",
        "get_document_backlinks",
        "list_document_attachments",
        # Collection tools (from route scopes)
        "list_collections",
        "create_collection",
    }

    names = await _list_tools_stdio(key)
    _assert_tools(names, expected, "mixed namespace + route scope")


async def test_namespace_create_scope(
    outline_stack,
    outline_access_token,
):
    """``documents:create`` grants only ``documents.create``.

    The ``create`` level is the most restrictive -- it only
    matches methods whose ``methodToScope`` is ``create``
    (i.e. the ``create`` method itself).
    """
    key = _create_api_key(
        outline_access_token,
        "e2e-stdio-namespace-create-docs",
        ["apiKeys.list", "documents:create"],
        skip_on_error=True,
    )

    expected = {
        "create_document",
        "batch_create_documents",
    }

    names = await _list_tools_stdio(key)
    _assert_tools(names, expected, "namespace create scope")


# -------------------------------------------------------------------
# Streamable-HTTP test — per-request header filtering
# -------------------------------------------------------------------


async def test_http_header_filters_tools(
    _http_server,
    outline_api_key,
    outline_access_token,
):
    """Per-request ``x-outline-api-key`` header triggers filtering.

    The server runs with a placeholder env-var key.  A real
    admin key via header should show all tools; a scoped key
    via header should show only the permitted subset.
    """
    # Admin key via header -> all tools
    admin_names = await _list_tools_http(outline_api_key)
    _assert_tools(admin_names, ALL_TOOLS, "http header admin key")

    # Scoped key via header -> subset
    scoped_key = _create_api_key(
        outline_access_token,
        "e2e-http-header-scoped",
        ["apiKeys.list", "documents:read"],
        skip_on_error=True,
    )
    scoped_names = await _list_tools_http(scoped_key)
    assert "read_document" in scoped_names
    assert "list_collections" not in scoped_names
    assert "create_document" not in scoped_names
