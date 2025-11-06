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

`OutlineClient` in `utils/outline_client.py` handles REST API interactions:

**Operations**:
- Documents: get, search, create, update, move, archive, delete, restore
- Collections: list, create, update, delete, export
- Comments: create, list, get
- AI: answer questions

**Configuration**:
- `OUTLINE_API_KEY` (required)
- `OUTLINE_API_URL` (optional, defaults to https://app.getoutline.com/api)
- Authentication via Bearer token

**Error Handling**:
- Raises `OutlineError` for API failures
- Tools catch exceptions and return error strings

**Rate Limiting**:
- Tracks `RateLimit-Remaining` and `RateLimit-Reset` headers, waits proactively when exhausted
- Automatic retry on HTTP 429 with exponential backoff (1s, 2s, 4s)
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
            client = OutlineClient()
            result = client.search_documents(query, collection_id)
            return _format_search_results(result)
        except Exception as e:
            return f"Error: {str(e)}"
```

### Adding New Tools

**Client Method** (if new endpoint needed):
```python
def new_operation(self, param: str) -> dict:
    """Docstring describing operation."""
    url = f"{self.base_url}/endpoint"
    response = requests.post(url, headers=self.headers, json={"param": param})
    if response.status_code != 200:
        raise OutlineError(f"Error: {response.status_code}", response)
    return response.json().get("data", {})
```

**Tool Function**:
```python
@mcp.tool()
async def new_tool_name(param: str) -> str:
    """Clear description."""
    try:
        client = OutlineClient()
        result = client.new_operation(param)
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
if response.status_code != 200:
    raise OutlineError(
        f"Operation failed: {response.status_code}",
        response
    )

# In tool functions
try:
    client = OutlineClient()
    result = client.operation()
    return format_result(result)
except OutlineError as e:
    return f"Outline API error: {str(e)}"
except Exception as e:
    return f"Error: {str(e)}"
```

### Testing

Mock `OutlineClient` in tests:

```python
with patch('module.OutlineClient') as mock_client:
    mock_client.return_value.method.return_value = {"data": "value"}
    # Test tool behavior
```

### Configuration

`.env` file:
```bash
OUTLINE_API_KEY=<your_key>       # Required
OUTLINE_API_URL=<custom_url>     # Optional
```

### Critical Requirements

- No stdout/stderr logging (MCP uses stdio)
- Tools return strings, not dicts
- Use `async def` for tool functions
- Catch exceptions, return error strings
- Follow KISS principle

## Common Patterns

**Pagination**: Use `offset` and `limit` parameters for large result sets

**Tree Formatting**: Recursive formatting with indentation for hierarchies

**Document ID Resolution**: `get_document_id_from_title` for user-friendly lookups
