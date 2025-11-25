# Contributing to MCP Outline

Thanks for your interest in contributing! This is a hobby project, so we keep
things simple.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Vortiago/mcp-outline.git
cd mcp-outline

# Install dependencies (requires uv - https://docs.astral.sh/uv/)
uv sync --extra dev

# Copy environment template
cp .env.example .env
# Edit .env and add your OUTLINE_API_KEY
```

## Development Workflow

### Running Tests

```bash
# Set a dummy API key for tests (or use your real one)
export OUTLINE_API_KEY=dummy

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/features/documents/test_document_search.py -v

# Run with coverage
uv run pytest tests/ -v --cov=src/mcp_outline
```

### Code Quality Checks

Run these before committing:

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run pyright src/
```

Or install pre-commit hooks to run automatically:

```bash
uv run pre-commit install
```

## Code Style

- **Line length**: 79 characters (PEP 8)
- **Type hints**: Required on all functions
- **Docstrings**: Google style
- **Imports**: stdlib, then third-party, then local

## Adding a New Tool

1. Create or edit a module in `src/mcp_outline/features/documents/`
2. Follow the existing pattern:

```python
from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)

def register_tools(mcp) -> None:
    @mcp.tool()
    async def my_new_tool(param: str) -> str:
        """Tool description for AI assistants."""
        try:
            client = await get_outline_client()
            result = await client.some_method(param)
            return _format_result(result)
        except OutlineClientError as e:
            return f"Error: {str(e)}"
```

3. Add tests in `tests/features/documents/test_<module>.py`
4. Register in `src/mcp_outline/features/documents/__init__.py` if new module

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Make your changes with tests
3. Run the checks: `uv run ruff format . && uv run ruff check . && uv run pyright src/ && uv run pytest tests/ -v`
4. Open a PR with a clear description

## Questions?

Open an issue on GitHub if you have questions or run into problems.
