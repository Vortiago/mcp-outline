"""Test suite for the MCP Outline server.

Three layers of test coverage, each with a distinct scope:

- **Unit tests** (``uv run poe test-unit``): Mock ``OutlineClient`` entirely.
  Fast, no network, no subprocess. Cover every tool function, client method,
  formatter, and error path.
- **Integration tests** (``uv run poe test-integration``): Start the MCP server
  as a subprocess and communicate via stdio or streamable-http. Verify the
  MCP protocol handshake, tool registration, read-only mode enforcement, and
  HTTP health endpoints.
- **E2E tests** (``uv run poe test-e2e``): Spin up a full Outline + Dex stack
  via Docker Compose and run every MCP tool against a live API. Marked
  ``@pytest.mark.e2e`` and excluded from normal ``pytest`` runs.

## E2E Fixture Chain

E2E tests share a session-scoped fixture chain defined in
``tests/e2e/conftest.py``: ``outline_stack`` → ``outline_api_key`` →
``mcp_server_params`` → ``mcp_session``.

The OIDC fixture uses manual cookie management (``_parse_set_cookies``) to
prevent httpx's cookie jar from leaking Outline session cookies to Dex —
both services run on ``localhost`` but on different ports.

## Conventions

**Unit test classes** use ``setup_method``/``teardown_method`` to save and
restore every environment variable they touch. Any new env var must be added
to both methods.

**Async tool tests** patch ``get_outline_client`` at the module level and
use ``AsyncMock``:

```python
with patch("module.get_outline_client") as mock_get_client:
    mock_client = AsyncMock()
    mock_client.some_method.return_value = {"key": "value"}
    mock_get_client.return_value = mock_client
    result = await tool_function("param")
    assert "expected" in result
```

**Test naming**: ``test_<method>_<scenario>`` — for example
``test_create_document_as_template`` or ``test_search_documents_client_error``.

**Parameter coverage**: every new tool parameter needs at least two tests —
one verifying the value is forwarded to the client, one verifying it is
omitted when not supplied (not sent as ``None``).

**E2E isolation**: each test creates its own collection so failures are
independent and there is no shared mutable state between tests.

**Search/index back-off**: full-text search and title lookup index
asynchronously. E2E tests that depend on indexing use a retry loop with
``await anyio.sleep(1)`` between attempts rather than a fixed sleep.
"""
