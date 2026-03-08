# Configuration

Detailed configuration for server permissions, tool filtering, and authentication.

## Read-Only Mode

Set `OUTLINE_READ_ONLY=true` to enable viewer-only access. Only search, read, export, and collaboration viewing tools are available. All write operations (create, update, move, archive, delete) are disabled.

**Use cases:**
- Shared access for team members who should only view content
- Safe integration with AI assistants that should not modify documents
- Public or demo instances where content should be protected

**Available tools in read-only mode:**
- Search & Discovery: `search_documents`, `list_collections`, `get_collection_structure`, `get_document_id_from_title`
- Document Reading: `read_document`, `export_document`
- Comments: `list_document_comments`, `get_comment`
- Collaboration: `get_document_backlinks`
- Collections: `export_collection`, `export_all_collections`
- AI: `ask_ai_about_documents` (if not disabled with `OUTLINE_DISABLE_AI_TOOLS`)

## Disable Delete Operations

Set `OUTLINE_DISABLE_DELETE=true` to allow create and update workflows while preventing accidental data loss. Only delete operations are disabled.

**Use cases:**
- Production environments where documents should not be deleted
- Protecting against accidental deletions
- Safe content editing workflows

**Disabled tools:**
- `delete_document`, `delete_collection`
- `batch_delete_documents`

**Important:** `OUTLINE_READ_ONLY=true` takes precedence over `OUTLINE_DISABLE_DELETE`. If both are set, the server operates in read-only mode.

## Multi-User Setup (HTTP)

When running in HTTP mode (`sse` or `streamable-http`), multiple users can share a single MCP server, each authenticating with their own Outline API key.

### Per-User Outline API Keys

Each user passes their own Outline API key via the `x-outline-api-key` HTTP header instead of (or in addition to) the `OUTLINE_API_KEY` environment variable.

**Priority:** Header value takes precedence over the environment variable. If the header is not present, the server falls back to the env var.

**Example** (with a streamable-http server on port 3000):

Start the server:

```bash
docker run -p 3000:3000 \
  -e OUTLINE_API_KEY=<DEFAULT_KEY> \
  -e MCP_TRANSPORT=streamable-http \
  ghcr.io/vortiago/mcp-outline:latest
```

Then connect from your client with a user-specific key:

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "mcp-outline": {
      "type": "http",
      "url": "http://localhost:3000/mcp",
      "headers": {
        "x-outline-api-key": "<YOUR_KEY>"
      }
    }
  }
}
```

**Claude Code** (`.mcp.json`):
```json
{
  "mcpServers": {
    "mcp-outline": {
      "type": "http",
      "url": "http://localhost:3000/mcp",
      "headers": {
        "x-outline-api-key": "<YOUR_KEY>"
      }
    }
  }
}
```

> **Note:** The `x-outline-api-key` header is only available for HTTP transports (SSE, streamable-http). In `stdio` mode, you must set `OUTLINE_API_KEY` via environment variable or a [dotenv config file](client-setup.md#claude-code-plugin). If it is missing, the server still starts but every tool call will return an error with setup instructions.

### Dynamic Tool List

Set `OUTLINE_DYNAMIC_TOOL_LIST=true` to automatically filter the tool list based on each user's Outline role and API key scopes. This pairs well with per-user Outline API keys — each user sees only the tools their key allows.

**How it works:**

On each `tools/list` request, the server performs two independent checks:

1. **Role check** (`auth.info`) — tools requiring a higher role than the user's are hidden (e.g. viewers cannot see member/admin tools)
2. **Scope check** (`apiKeys.list`) — if the API key has restricted scopes, tools for excluded endpoints are hidden. See the [Outline API documentation](https://www.getoutline.com/developers) for details on scope formats and available scopes.

Both results are combined. Each check fails open independently — if either call fails (e.g. the key lacks `apiKeys.list` scope), that check is skipped and all tools remain visible. The only exception is a 401 (invalid key), which hides all tools.

> **Note:** This is a convenience feature, not a security boundary. Even if a tool is hidden from the list, Outline's own API enforces permissions on individual operations.

This feature composes with `OUTLINE_READ_ONLY` and `OUTLINE_DISABLE_DELETE`. If `OUTLINE_READ_ONLY=true`, write tools are never registered regardless of this setting.

For architecture details and diagrams, see [Dynamic Tool List Architecture](dynamic-tool-list.md).
