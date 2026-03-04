# MCP Outline Server Guide

This guide helps you implement and modify the MCP Outline server effectively.

## Purpose

This MCP server bridges AI assistants with Outline's document management platform:
- REST API integration for Outline services
- Tools for documents, collections, attachments, and comments
- MCP resources via `outline://` URI scheme
- API key authentication with rate limiting
- Docker and local development support
- Health check endpoints for container orchestration

## Architecture

### Tool Categories

- **Search**: Find documents, collections, hierarchies
- **Reading**: Read content, export markdown
- **Attachments**: Resolve URLs, fetch content, list attachments
- **Content**: Create, update, comment (supports templates)
- **Organization**: Move documents between collections
- **Lifecycle**: Archive, delete, restore operations
- **Collaboration**: Comments, backlinks
- **Collections**: Create, update, delete, export
- **Batch Operations**: Bulk create, update, move, archive, delete
- **AI**: Natural language queries

### Feature Registration Flow

```
register_all(mcp)
  |- health.register_routes(mcp)               # Always
  |- documents.register(mcp)
  |   |- document_search.register_tools()      # Always
  |   |- document_reading.register_tools()     # Always
  |   |- document_attachments.register_tools() # Always
  |   |- document_collaboration.register_tools() # Always
  |   |- collection_tools.register_tools()     # Always (exports always, writes conditional)
  |   |- ai_tools.register_tools()             # If not OUTLINE_DISABLE_AI_TOOLS
  |   |- document_content.register_tools()     # If not OUTLINE_READ_ONLY
  |   |- document_lifecycle.register_tools()   # If not OUTLINE_READ_ONLY
  |   |- document_organization.register_tools() # If not OUTLINE_READ_ONLY
  |   |- batch_operations.register_tools()     # If not OUTLINE_READ_ONLY
  |- resources.register(mcp)                   # Always
install_dynamic_tool_list(mcp)                   # If OUTLINE_DYNAMIC_TOOL_LIST=true
```

### MCP Resources (`outline://` URI scheme)

- `outline://document/{document_id}` - Full markdown content
- `outline://document/{document_id}/backlinks` - Documents linking to this one
- `outline://collection/{collection_id}` - Collection metadata
- `outline://collection/{collection_id}/tree` - Hierarchical document tree
- `outline://collection/{collection_id}/documents` - List documents in collection

### Health Check Endpoints

- `GET /health` - Liveness probe (always returns 200)
- `GET /ready` - Readiness probe (verifies API connectivity, returns 503 if not ready)

## Core Concepts

### Outline Objects

- **Documents**: Markdown content with title, URL, and metadata
- **Collections**: Grouping with name, description, color
- **Comments**: Threaded discussions with replies and anchor text
- **Attachments**: Binary files referenced in document content
- **Hierarchy**: Parent-child document relationships
- **Templates**: Documents marked as templates appear in "New from template" picker
- **Lifecycle**: Draft -> Published -> Archived -> Deleted

### API Client

`OutlineClient` in `utils/outline_client.py` handles async REST API interactions:

**Operations** (all async):
- Documents: get, search, list, create, update, move, archive, unarchive, delete, restore
- Collections: list, get, get_documents, create, update, delete, export, export_all
- Comments: create, list, get
- Attachments: get_redirect_url, fetch_content
- AI: answer questions
- API Keys: list_api_keys (scope introspection for dynamic tool list)

**Connection Pooling**:
- Uses httpx with class-level connection pool
- Shared across all OutlineClient instances
- Automatic connection reuse for better performance
- Configurable limits via environment variables

**Rate Limiting**:
- Tracks `RateLimit-Remaining` and `RateLimit-Reset` headers, waits proactively when exhausted
- Uses asyncio.Lock for thread-safe rate limiting in concurrent scenarios
- Automatic retry with exponential backoff (max 3 attempts)
- Respects `Retry-After` header on HTTP 429 responses
- Enabled by default, no configuration required

**Error Handling**:
- Raises `OutlineError` for API failures
- Tools catch exceptions and return error strings
- Supports httpx exceptions (RequestError, HTTPStatusError, TimeoutException)

### Common Utilities (`features/documents/common.py`)

- `get_outline_client()` - Async function that creates an OutlineClient. Checks for a per-user Outline API key from the `x-outline-api-key` HTTP header first (SSE/streamable-http), then falls back to `OUTLINE_API_KEY` env var.
- `_get_header_api_key()` - Reads the `x-outline-api-key` header from the MCP SDK's `request_ctx` ContextVar. Returns `None` for stdio or when header is absent.
- `OutlineClientError` - Exception class for client-related errors

### Copilot CLI Patch (`patches/copilot_cli.py`)

Workaround for GitHub Copilot CLI sending `""` instead of `{}` for empty tool parameters.
Applied before server initialization. Patches `mcp.types.CallToolRequestParams` with a field validator.

## Implementation Patterns

### Module Structure

Feature modules follow this pattern:

```python
# 1. Imports (standard lib -> third-party -> local)
import os
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from mcp_outline.features.documents.common import (
    get_outline_client,
    OutlineClientError,
)

# 2. Helper formatters (private functions)
def _format_search_results(data: dict) -> str:
    """Format API response for user display."""
    # Clean, readable output formatting
    pass

# 3. Tool registration function
def register_tools(mcp: FastMCP) -> None:
    """Register all tools in this module."""

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        )
    )
    async def search_documents(
        query: str,
        collection_id: Optional[str] = None,
    ) -> str:
        """
        Search for documents by keywords.

        Args:
            query: Search keywords
            collection_id: Optional collection filter

        Returns:
            Formatted search results
        """
        try:
            client = await get_outline_client()
            result = await client.search_documents(
                query, collection_id
            )
            return _format_search_results(result)
        except OutlineClientError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
```

### Adding New Tools

**Client Method** (if new endpoint needed):
```python
async def new_operation(self, param: str) -> dict:
    """Docstring describing operation."""
    response = await self.post("endpoint", {"param": param})
    return response.get("data", {})
```

**Tool Function**:
```python
@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
    )
)
async def new_tool_name(param: str) -> str:
    """Clear description."""
    try:
        client = await get_outline_client()
        result = await client.new_operation(param)
        return _format_result(result)
    except OutlineClientError as e:
        return f"Outline API error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

**Testing**: Mock OutlineClient, test success and error cases

## Technical Requirements

### Code Style

- PEP 8 conventions
- Type hints for all functions
- Max line length: 79 characters (ruff enforced)
- Google-style docstrings
- Import order: stdlib -> third-party -> local
- Single responsibility per function

### Error Handling

```python
# In OutlineClient methods
try:
    response = await self._client_pool.post(
        url, headers=headers, json=data
    )
    response.raise_for_status()
    return response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        raise OutlineError(f"Rate limited")
    raise OutlineError(
        f"HTTP {e.response.status_code}: {e.response.text}"
    )
except httpx.TimeoutException as e:
    raise OutlineError(f"Request timeout: {str(e)}")
except httpx.RequestError as e:
    raise OutlineError(f"API request failed: {str(e)}")

# In tool functions
try:
    client = await get_outline_client()
    result = await client.operation()
    return format_result(result)
except OutlineClientError as e:
    return f"Outline API error: {str(e)}"
except Exception as e:
    return f"Error: {str(e)}"
```

### Testing

Mock `OutlineClient` in async tests:

```python
@pytest.mark.asyncio
async def test_tool():
    with patch('module.get_outline_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.method.return_value = {"data": "value"}
        mock_get_client.return_value = mock_client

        result = await tool_function("param")
        assert "expected" in result
```

**Test Conventions**:
- `TestOutlineClient` uses `setup_method`/`teardown_method` to save and restore
  ALL environment variables it touches. New env vars MUST be added to both methods.
- Tool test classes use `MockMCP` fixture and `register_*_tools` pattern
- Use `AsyncMock` for client mocking, not manual mocks
- Test names: `test_<method>_<scenario>` (e.g., `test_create_document_as_template`)
- Every new parameter needs at least two tests: one with value set, one verifying
  it's not sent when `None`/default

### E2E Tests

Run against a real Outline instance via Docker Compose:

```bash
uv run poe test-e2e
```

- **Marker**: `@pytest.mark.e2e` — excluded from normal `pytest` runs
- **Fixture chain**: `outline_stack` (Docker lifecycle) →
  `_outline_credentials` (OIDC login) → `outline_api_key` (API key
  creation) / `outline_access_token` (session token) →
  `mcp_server_params` → `mcp_session` (stdio client factory)
- **OIDC fixture**: Uses manual cookie management (`_parse_set_cookies`) to
  prevent httpx's cookie jar from leaking Outline cookies to Dex (both run on
  localhost but on different ports)
- **Attachment tests**: Upload a real file via the Outline REST API
  (`attachments.create` + `files.create`) using the API key, then test
  the read-only MCP attachment tools against it
- **Skipped tools**:
  - AI tool (`ask_ai_about_documents`): Disabled via `OUTLINE_DISABLE_AI_TOOLS`

### Configuration

`.env` file:
```bash
# Outline API (optional — if unset, every request must include x-outline-api-key header)
OUTLINE_API_KEY=<your_key>

# Outline API (optional)
OUTLINE_API_URL=<custom_url>               # Default: https://app.getoutline.com/api
OUTLINE_VERIFY_SSL=true                    # Default: true (set false for self-signed certs)

# Connection pooling (optional)
OUTLINE_MAX_CONNECTIONS=100                # Max concurrent connections
OUTLINE_MAX_KEEPALIVE=20                   # Max idle connections in pool
OUTLINE_TIMEOUT=30.0                       # Read timeout in seconds
OUTLINE_CONNECT_TIMEOUT=5.0               # Connection timeout in seconds
OUTLINE_WRITE_TIMEOUT=30.0                # Write timeout in seconds

# Feature flags (optional)
OUTLINE_DISABLE_AI_TOOLS=true              # Disable AI tools
OUTLINE_READ_ONLY=true                     # Disable all write operations
OUTLINE_DISABLE_DELETE=true                # Disable delete operations only
OUTLINE_DYNAMIC_TOOL_LIST=true             # Enable per-user tool filtering (requires apiKeys.list scope)

# MCP server (optional)
MCP_TRANSPORT=stdio                        # Transport: stdio, sse, streamable-http
MCP_HOST=127.0.0.1                         # Server host (use 0.0.0.0 for Docker)
MCP_PORT=3000                              # Server port
```

**Access Control Notes**:
- `OUTLINE_READ_ONLY`: Blocks entire write modules at registration (content, lifecycle, organization, batch_operations)
- `OUTLINE_DISABLE_DELETE`: Conditionally registers delete tools within document_lifecycle and collection_tools
- `OUTLINE_DYNAMIC_TOOL_LIST`: Off by default. Uses `apiKeys.list` to introspect API key scopes and filters tools per-user based on scope matching. Scoped API keys must include `apiKeys.list` in their scope array for introspection to work. Fail-open: if scope introspection fails, all tools are shown. Set to `true` to enable.
- Read-only mode takes precedence: If both are set, server operates in read-only mode

### Critical Requirements

- No stdout/stderr logging (MCP uses stdio)
- Tools return strings, not dicts
- Use `async def` for ALL tool functions
- Use `await` for ALL client method calls
- Always use `await get_outline_client()` to get client instance
- Catch exceptions, return error strings
- Use `ToolAnnotations` on all tools (readOnlyHint, destructiveHint, etc.)
- Follow KISS principle

### Pre-Commit Checks

**IMPORTANT**: Before committing, run all CI checks locally to ensure they pass:

```bash
# Format code
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Lint code
uv run ruff check .

# Type check
uv run pyright src/

# Run tests
uv run poe test-unit

# Run integration tests
uv run poe test-integration

# Run E2E tests (requires Docker)
uv run poe test-e2e
```

## Common Patterns

**Pagination**: Use `offset` and `limit` parameters for large result sets

**Tree Formatting**: Recursive formatting with indentation for hierarchies

**Document ID Resolution**: `get_document_id_from_title` for user-friendly lookups

**Tool Annotations**: All tools should include `ToolAnnotations` with appropriate hints

**Conditional Registration**: Use environment variables to control which tools are registered

## Version Tagging

When tagging version numbers look at changes since last version. Follow this rule for version number, go from left to right. First one hit is the new version number. Any feat!: => major version, any feat: => minor version, Only fix: => patch version. Use annotated tag with a short summary of what the release contains.
