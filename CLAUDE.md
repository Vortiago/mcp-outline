# MCP Outline Server Guide

This guide helps Claude implement and modify the MCP Outline server
codebase effectively.

## 1. Purpose & Overview

This MCP server enables AI assistants to interact with Outline by:
- Connecting to Outline services via REST API
- Exposing Outline data (documents, collections, comments)
- Providing 25 tools across 8 feature categories
- Using API key authentication for secure interactions
- Supporting Docker deployment and local development

**Current Version**: 0.2.2
**Python Requirement**: 3.10+
**MCP Framework**: FastMCP (mcp[cli] >= 0.1.0)

## 2. Architecture Overview

### Project Structure

```
src/mcp_outline/
├── server.py                    # MCP server entry point
├── __init__.py
├── __main__.py
├── features/                    # Feature modules (25 tools)
│   ├── __init__.py
│   └── documents/               # All document-related tools
│       ├── __init__.py          # Tool registration
│       ├── common.py            # Shared utilities
│       ├── document_search.py       # 4 tools
│       ├── document_reading.py      # 2 tools
│       ├── document_content.py      # 3 tools
│       ├── document_organization.py # 1 tool
│       ├── document_lifecycle.py    # 6 tools
│       ├── document_collaboration.py # 3 tools
│       ├── collection_tools.py      # 5 tools
│       └── ai_tools.py              # 1 tool
└── utils/
    ├── __init__.py
    └── outline_client.py        # API client (378 lines)

tests/
├── test_server.py
├── features/documents/          # Feature tests
│   ├── test_document_search.py
│   ├── test_document_reading.py
│   ├── test_document_content.py
│   └── test_document_collaboration.py
└── utils/
    └── test_outline_client.py   # API client tests
```

### MCP Components

**Implemented**: 25 Tools organized into 8 categories
**Not Implemented**: Resources, Prompts (tools only)

### Tool Categories

1. **Document Search** (4 tools): `search_documents`,
   `list_collections`, `get_collection_structure`,
   `get_document_id_from_title`
2. **Document Reading** (2 tools): `read_document`,
   `export_document`
3. **Document Content** (3 tools): `create_document`,
   `update_document`, `add_comment`
4. **Document Organization** (1 tool): `move_document`
5. **Document Lifecycle** (6 tools): `archive_document`,
   `unarchive_document`, `delete_document`, `restore_document`,
   `list_archived_documents`, `list_trash`
6. **Document Collaboration** (3 tools): `list_document_comments`,
   `get_comment`, `get_document_backlinks`
7. **Collection Management** (5 tools): `create_collection`,
   `update_collection`, `delete_collection`, `export_collection`,
   `export_all_collections`
8. **AI Tools** (1 tool): `ask_ai_about_documents`

## 3. Core Concepts

### Outline Objects

- **Documents**: Content with title, text (markdown), metadata
- **Collections**: Grouping mechanism with name, description, color
- **Comments**: Threaded discussions on documents with replies
- **Hierarchy**: Parent-child document relationships
- **Lifecycle**: Draft → Published → Archived → Deleted states

### API Client (`utils/outline_client.py`)

The `OutlineClient` class handles all Outline REST API interactions:

**Key Methods** (20+ total):
- Document ops: `get_document`, `search_documents`,
  `create_document`, `update_document`, `move_document`,
  `archive_document`, `delete_document`, etc.
- Collection ops: `list_collections`, `create_collection`,
  `export_collection`, `export_all_collections`
- Comment ops: `create_comment`, `list_comments`, `get_comment`
- Lifecycle ops: `list_trash`, `restore_document`
- AI ops: `answer_question`

**Configuration**:
- Environment: `OUTLINE_API_KEY` (required),
  `OUTLINE_API_URL` (optional)
- Authentication: Bearer token in Authorization header
- Default base URL: `https://app.getoutline.com/api`

**Error Handling**:
- Raises `OutlineError` for API failures
- Includes status code and error message
- Tools catch and return friendly error strings

## 4. Implementation Guidelines

### Module Pattern

Each feature module follows this structure:

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

1. **Choose the right module**: Add to existing feature module or
   create new one
2. **Implement in OutlineClient** (if new API endpoint):
   ```python
   def new_operation(self, param: str) -> dict:
       """Docstring describing operation."""
       url = f"{self.base_url}/endpoint"
       response = requests.post(
           url,
           headers=self.headers,
           json={"param": param}
       )
       if response.status_code != 200:
           raise OutlineError(
               f"Error: {response.status_code}",
               response
           )
       return response.json().get("data", {})
   ```

3. **Create formatter helper** (if needed):
   ```python
   def _format_new_data(data: dict) -> str:
       """Format for readable output."""
       # Return clean string representation
       pass
   ```

4. **Add tool function**:
   ```python
   @mcp.tool()
   async def new_tool_name(param: str) -> str:
       """Clear description of what this tool does.

       Args:
           param: Description of parameter

       Returns:
           Description of return value
       """
       try:
           client = OutlineClient()
           result = client.new_operation(param)
           return _format_new_data(result)
       except Exception as e:
           return f"Error: {str(e)}"
   ```

5. **Write tests**: Create test file in `tests/features/documents/`
   ```python
   import pytest
   from unittest.mock import Mock, patch

   @pytest.mark.asyncio
   async def test_new_tool_name():
       """Test successful operation."""
       mock_mcp = MockMCP()

       with patch('outline_client.OutlineClient') as mock_client:
           mock_client.return_value.new_operation.return_value = {
               "id": "123",
               "name": "test"
           }

           # Register tools
           from features.documents.module import register_tools
           register_tools(mock_mcp)

           # Call tool
           result = await mock_mcp.call_tool(
               "new_tool_name",
               {"param": "value"}
           )

           assert "test" in result
   ```

### Development Workflow

1. **Review Outline API docs**: Understand endpoint behavior
2. **Check existing patterns**: Look at similar tools
3. **Implement incrementally**: Client method → Tool → Tests
4. **Test thoroughly**: Success cases and error handling
5. **Format and lint**: `uv run ruff format .`
6. **Run tests**: `uv run pytest tests/`
7. **Manual testing**: Use MCP Inspector to verify

## 5. Technical Requirements

### Code Style

- **PEP 8 conventions**: Follow Python style guide
- **Type hints**: All function parameters and returns
- **Line length**: 79 characters (enforced by ruff)
- **Docstrings**: Google-style for all public functions
- **Small functions**: Single responsibility principle
- **Import order**:
  1. Standard library
  2. Third-party packages
  3. Local modules

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

### Testing Patterns

Use `MockMCP` class to simulate FastMCP:

```python
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

    async def call_tool(self, name, args):
        return await self.tools[name](**args)
```

Mock OutlineClient in tests:

```python
with patch('module.OutlineClient') as mock_client:
    mock_instance = mock_client.return_value
    mock_instance.method.return_value = {"data": "value"}
    # Test tool behavior
```

### Development Tools

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run development server with MCP Inspector
mcp dev src/mcp_outline/server.py

# Alternative: use provided script
./start_server.sh

# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/features/documents/test_document_search.py

# Format code (auto-fix)
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run pyright src/

# Build Docker image
docker buildx build -t mcp-outline .

# Test Docker container with MCP Inspector
npx @modelcontextprotocol/inspector docker run -i --rm \
  --init -e DOCKER_CONTAINER=true --env-file .env mcp-outline
```

### Configuration

Create `.env` file in project root:

```bash
# Required
OUTLINE_API_KEY=ol_api_xxxxxxxxxxxxxxxxxxxxxxxx

# Optional (defaults to https://app.getoutline.com/api)
OUTLINE_API_URL=https://your-instance.com/api
```

### Deployment Options

**1. Local Development**:
```bash
mcp dev src/mcp_outline/server.py
```

**2. Claude Desktop**:
```bash
mcp install src/mcp_outline/server.py --name "Document Outline"
```

**3. Cursor IDE** (with Docker):
```json
{
  "mcpServers": {
    "mcp-outline": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--init",
        "-e", "DOCKER_CONTAINER=true",
        "-e", "OUTLINE_API_KEY",
        "-e", "OUTLINE_API_URL",
        "mcp-outline"
      ],
      "env": {
        "OUTLINE_API_KEY": "<YOUR_KEY>",
        "OUTLINE_API_URL": "<OPTIONAL_URL>"
      }
    }
  }
}
```

### Critical Requirements

- **No stdout/stderr logging**: MCP uses stdio for protocol
- **String returns**: All tools must return strings (not dicts)
- **Async tool signatures**: Use `async def` for all tools
- **Error messages as strings**: Catch exceptions, return error text
- **Import sorting**: Enforced by ruff (E, F, I rules)
- **KISS principle**: Keep implementations simple and clear

## 6. Common Patterns

### Document ID Resolution

Many tools need document IDs. Use `get_document_id_from_title` for
user-friendly title-based lookups:

```python
# User provides title, tool resolves to ID
doc_id = get_document_id_from_title("My Document")
content = read_document(doc_id)
```

### Pagination

Handle large result sets with offset/limit:

```python
def list_items(offset: int = 0, limit: int = 25) -> str:
    """List with pagination support."""
    result = client.list_items(offset=offset, limit=limit)
    return _format_paginated_results(result, offset, limit)
```

### Hierarchical Display

Use tree formatting for nested structures:

```python
def _format_tree(items: list, indent: int = 0) -> str:
    """Format hierarchical data as tree."""
    output = []
    for item in items:
        output.append("  " * indent + f"- {item['title']}")
        if item.get('children'):
            output.append(_format_tree(item['children'], indent + 1))
    return "\n".join(output)
```

## 7. Troubleshooting

**"No tools available"**: Check tool registration in
`features/documents/__init__.py`

**API authentication errors**: Verify `OUTLINE_API_KEY` in `.env`

**MCP Inspector connection fails**: Ensure no other process on stdio

**Docker container issues**: Check environment variable passing

**Type errors**: Run `uv run pyright src/` to catch issues early

**Test failures**: Use `pytest -v` for verbose output with details

## 8. Resources

- **Outline API Docs**: https://www.getoutline.com/developers
- **MCP Specification**: https://modelcontextprotocol.io
- **FastMCP SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Project Repo**: https://github.com/Vortiago/mcp-outline
