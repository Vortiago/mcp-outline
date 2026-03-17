---
name: new-tool
description: Scaffold a new MCP tool with client method, tool function, formatter, and tests following project conventions
disable-model-invocation: true
---

# New Tool Scaffolding

Create a new MCP tool for the Outline server by following this checklist.

## 1. Gather Information

Ask the user for:
- **Tool name**: The function name (e.g., `get_document_comments`)
- **Outline API endpoint**: The REST endpoint (e.g., `comments.list`)
- **Description**: What the tool does
- **Read-only or write**: Whether this tool modifies data
- **Parameters**: What arguments the tool accepts
- **Which module**: Existing module to add to, or new module name

## 2. Add Client Method (if needed)

If the Outline API endpoint isn't already in `src/mcp_outline/utils/outline_client.py`, add an async method:

```python
async def new_operation(self, param: str) -> dict:
    """Docstring describing operation."""
    response = await self.post("endpoint", {"param": param})
    return response.get("data", {})
```

For GET-style endpoints that don't send a body, use `await self.post("endpoint")` without a payload dict.

## 3. Add Formatter Function

Add a private `_format_*` function above the `register_tools` function in the target module:

```python
def _format_result(data: dict) -> str:
    """Format API response for user display."""
    if not data:
        return "No results found."
    output = "# Title\n\n"
    # Build clean, readable markdown output
    return output
```

## 4. Create Tool Function

Add to the appropriate module in `src/mcp_outline/features/documents/`. Follow this pattern exactly:

```python
@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,    # True for read ops, False for writes
        destructiveHint=False, # True only for delete/archive
        idempotentHint=True,   # True if calling twice has same effect
        openWorldHint=True,    # True if it accesses external services
    ),
    meta={
        "endpoint": "namespace.method",  # Outline API endpoint
    },
)
async def tool_name(param: str) -> str:
    """
    Clear description of what the tool does.

    Use this tool when you need to:
    - Specific use case 1
    - Specific use case 2

    Args:
        param: Description of parameter

    Returns:
        Formatted string describing what's returned
    """
    try:
        client = await get_outline_client()
        result = await client.operation(param)
        return _format_result(result)
    except OutlineClientError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
```

## 5. Create Tests

Add tests in `tests/features/documents/test_<module>.py`:

```python
@pytest.mark.asyncio
async def test_tool_name_success(self, mock_mcp):
    """Test successful operation."""
    mock_client = AsyncMock()
    mock_client.operation.return_value = {"expected": "data"}

    with patch(
        "mcp_outline.features.documents.<module>.get_outline_client",
        return_value=mock_client,
    ):
        register_tools(mock_mcp)
        tool_fn = mock_mcp.get_tool("tool_name")
        result = await tool_fn(param="value")
        assert "expected" in result

@pytest.mark.asyncio
async def test_tool_name_error(self, mock_mcp):
    """Test error handling."""
    mock_client = AsyncMock()
    mock_client.operation.side_effect = OutlineClientError("fail")

    with patch(
        "mcp_outline.features.documents.<module>.get_outline_client",
        return_value=mock_client,
    ):
        register_tools(mock_mcp)
        tool_fn = mock_mcp.get_tool("tool_name")
        result = await tool_fn(param="value")
        assert "Error" in result
```

Every new parameter needs at least two tests: one with value set, one verifying it's not sent when `None`/default.

## 6. Register the Tool

If adding to an existing module, the tool is automatically registered via the module's `register_tools()` function.

If creating a new module:
1. Create `src/mcp_outline/features/documents/<module_name>.py`
2. Add a `register_tools(mcp)` function
3. Call it from `src/mcp_outline/features/documents/__init__.py`
4. Decide whether it's always-on, read-only-conditional, or feature-flag-gated

## 7. Verify

Run all pre-commit checks:

```bash
uv run ruff format .
uv run ruff check .
uv run pyright src/
uv run poe test-unit
```

## Checklist

- [ ] Client method added (if new endpoint)
- [ ] Formatter function for output
- [ ] Tool function with ToolAnnotations and meta (endpoint)
- [ ] Tests for success and error cases
- [ ] Every new parameter has tests: one with value, one with None/default
- [ ] Line length <= 79 characters
- [ ] All checks pass
