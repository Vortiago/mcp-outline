# MCP Outline Server Guide

This guide helps you implement and modify the MCP Outline server effectively.

## Purpose

This MCP server bridges AI assistants with Outline's document management platform:
- REST API integration for Outline services
- Tools for documents, collections, and comments
- API key authentication
- Docker and local development support

## Architecture

### Tool Categories

- **Search**: Find documents, collections, hierarchies
- **Reading**: Read content, export markdown
- **Content**: Create, update, comment
- **Organization**: Move documents between collections
- **Lifecycle**: Archive, delete, restore operations
- **Collaboration**: Comments, backlinks
- **Collections**: Create, update, delete, export
- **AI**: Natural language queries

## Core Concepts

### Outline Objects

- **Documents**: Markdown content with title and metadata
- **Collections**: Grouping with name, description, color
- **Comments**: Threaded discussions with replies
- **Hierarchy**: Parent-child document relationships
- **Lifecycle**: Draft → Published → Archived → Deleted

### API Client

`OutlineClient` in `utils/outline_client.py` handles async REST API interactions:

**Operations** (all async):
- Documents: get, search, create, update, move, archive, delete, restore
- Collections: list, create, update, delete, export
- Comments: create, list, get
- AI: answer questions

**Configuration**:
- `OUTLINE_API_KEY` (required)
- `OUTLINE_API_URL` (optional, defaults to https://app.getoutline.com/api)
- `OUTLINE_MAX_CONNECTIONS` (optional, default: 100) - Maximum concurrent connections
- `OUTLINE_MAX_KEEPALIVE` (optional, default: 20) - Maximum idle connections in pool
- `OUTLINE_TIMEOUT` (optional, default: 30.0) - Request timeout in seconds
- `OUTLINE_CONNECT_TIMEOUT` (optional, default: 5.0) - Connection timeout in seconds
- Authentication via Bearer token

**Connection Pooling**:
- Uses httpx with class-level connection pool
- Shared across all OutlineClient instances
- Automatic connection reuse for better performance
- Configurable limits via environment variables

**Error Handling**:
- Raises `OutlineError` for API failures
- Tools catch exceptions and return error strings
- Supports httpx exceptions (RequestError, HTTPStatusError, TimeoutException)

**Rate Limiting**:
- Tracks `RateLimit-Remaining` and `RateLimit-Reset` headers, waits proactively when exhausted
- Uses asyncio.Lock for thread-safe rate limiting in concurrent scenarios
- Automatic handling of HTTP 429 responses
- Respects `Retry-After` header
- Enabled by default, no configuration required

## Implementation Patterns

### Module Structure

Feature modules follow this pattern:

```python
# 1. Imports (standard lib → third-party → local)
import os
from typing import Any, Optional
from mcp_outline.utils.outline_client import OutlineClient

# 2. Helper formatters (private functions)
def _format_search_results(data: dict) -> str:
    """Format API response for user display."""
    # Clean, readable output formatting
    pass

# 3. Tool registration function
def register_tools(mcp):
    """Register all tools in this module."""

    @mcp.tool()
    async def search_documents(
        query: str,
        collection_id: Optional[str] = None
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
            result = await client.search_documents(query, collection_id)
            return _format_search_results(result)
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
@mcp.tool()
async def new_tool_name(param: str) -> str:
    """Clear description."""
    try:
        client = await get_outline_client()
        result = await client.new_operation(param)
        return _format_result(result)
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
- Import order: stdlib → third-party → local
- Single responsibility per function

### Error Handling

```python
# In OutlineClient methods
try:
    response = await self._client_pool.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        raise OutlineError(f"Rate limited")
    raise OutlineError(f"HTTP {e.response.status_code}: {e.response.text}")
except httpx.TimeoutException as e:
    raise OutlineError(f"Request timeout: {str(e)}")
except httpx.RequestError as e:
    raise OutlineError(f"API request failed: {str(e)}")

# In tool functions
try:
    client = await get_outline_client()
    result = await client.operation()
    return format_result(result)
except OutlineError as e:
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

### Configuration

`.env` file:
```bash
OUTLINE_API_KEY=<your_key>                 # Required
OUTLINE_API_URL=<custom_url>               # Optional
OUTLINE_MAX_CONNECTIONS=100                # Optional - Max connections
OUTLINE_MAX_KEEPALIVE=20                   # Optional - Max keepalive
OUTLINE_TIMEOUT=30.0                       # Optional - Request timeout
OUTLINE_CONNECT_TIMEOUT=5.0                # Optional - Connect timeout
```

### Critical Requirements

- No stdout/stderr logging (MCP uses stdio)
- Tools return strings, not dicts
- Use `async def` for ALL tool functions
- Use `await` for ALL client method calls
- Always use `await get_outline_client()` to get client instance
- Catch exceptions, return error strings
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
uv run pytest tests/ -v --cov=src/mcp_outline

# Run integration tests
uv run pytest tests/ -v -m integration
```

## Common Patterns

**Pagination**: Use `offset` and `limit` parameters for large result sets

**Tree Formatting**: Recursive formatting with indentation for hierarchies

**Document ID Resolution**: `get_document_id_from_title` for user-friendly lookups
