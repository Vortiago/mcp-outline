# MCP Outline Server Guide

Instructions for AI assistants working with this codebase.

## What This Is

An MCP server connecting AI assistants to Outline's document management API.
Provides tools for searching, reading, creating, and managing documents.

## Project Structure

```
src/mcp_outline/
├── server.py                 # FastMCP server entry point
├── features/
│   └── documents/            # All document tools
│       ├── __init__.py       # Conditional tool registration
│       ├── common.py         # Shared: get_outline_client(), OutlineClientError
│       ├── document_search.py
│       ├── document_reading.py
│       ├── document_content.py
│       ├── document_lifecycle.py
│       ├── document_organization.py
│       ├── document_collaboration.py
│       ├── collection_tools.py
│       ├── batch_operations.py
│       └── ai_tools.py
└── utils/
    └── outline_client.py     # OutlineClient: async API wrapper
```

## Key Patterns

### Tool Module Structure

Every tool module follows this pattern:

```python
from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)

def _format_result(data: dict) -> str:
    """Private helper to format API response."""
    pass

def register_tools(mcp) -> None:
    """Register tools with MCP server."""

    @mcp.tool()
    async def tool_name(param: str) -> str:
        """Docstring becomes tool description for AI."""
        try:
            client = await get_outline_client()
            result = await client.some_method(param)
            return _format_result(result)
        except OutlineClientError as e:
            return f"Error: {str(e)}"
```

### Critical Rules

1. **Always async**: All tools use `async def` and `await`
2. **Return strings**: Tools return formatted strings, never dicts
3. **Catch exceptions**: Return error strings, don't raise
4. **Use get_outline_client()**: Always `await get_outline_client()` for client
5. **No stdout/stderr**: MCP uses stdio - logging breaks the protocol

### Batch Operations Pattern

For bulk operations, use the `_process_batch` helper in `batch_operations.py`:

```python
async def _process_batch(
    items: List[Any],
    process_item: Callable[[OutlineClient, Any], Awaitable[Dict]],
    operation_name: str,
    empty_error: str = "No items provided.",
) -> str:
    """Generic batch processor with error handling per item."""
```

Define a per-item processor and call `_process_batch`:

```python
async def batch_archive_documents(document_ids: List[str]) -> str:
    async def archive_one(client, doc_id):
        document = await client.archive_document(doc_id)
        if document:
            return _create_result_entry(doc_id, "success", title=...)
        return _create_result_entry(doc_id, "failed", error=...)

    return await _process_batch(
        document_ids, archive_one, "archive", "No document IDs provided."
    )
```

## Environment Variables

```bash
# Required
OUTLINE_API_KEY=your_key

# Optional
OUTLINE_API_URL=https://app.getoutline.com/api  # Default
OUTLINE_READ_ONLY=true          # Disable all write tools
OUTLINE_DISABLE_AI_TOOLS=true   # Disable AI question tool
OUTLINE_DISABLE_DELETE=true     # Disable only delete tools
```

## Testing

Tests mock `get_outline_client`:

```python
@pytest.mark.asyncio
@patch("mcp_outline.features.documents.module.get_outline_client")
async def test_tool(mock_get_client):
    mock_client = AsyncMock()
    mock_client.method.return_value = {"data": ...}
    mock_get_client.return_value = mock_client

    result = await tool_function("param")
    assert "expected" in result
```

## Before Committing

```bash
uv run ruff format .           # Format
uv run ruff check .            # Lint
uv run pyright src/            # Type check
uv run pytest tests/ -v        # Test
```

## Code Style

- 79-char line limit (ruff enforced)
- Type hints on all functions
- Google-style docstrings
- Import order: stdlib, third-party, local

## Version Tagging

When tagging releases, check commits since last version:
- `feat!:` = major version bump
- `feat:` = minor version bump
- `fix:` only = patch version bump

Use annotated tags with a summary of changes.
