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

## Dynamic Tool List

Set `OUTLINE_DYNAMIC_TOOL_LIST=true` to filter the tool list per-request based on the authenticated user's Outline role and API key scopes. On each `tools/list` request, the server calls `auth.info` and hides write tools for viewer-role users or read-only-scoped API keys. This is disabled by default.

**Use cases:**
- Multi-user HTTP deployments where different API keys have different permission levels
- Environments where viewer-role users should not see write tools
- API keys with restricted endpoint scopes should only show matching tools

**How it works:**
1. On each `tools/list` request, the server calls Outline's `auth.info` endpoint
2. If the user's role is `viewer`, write tools are hidden
3. If the API key has restricted scopes that exclude write endpoints, write tools are hidden
4. If `auth.info` fails for any reason, all tools are returned (fail-open)

**Note:** This is a convenience feature, not a security boundary. Even if a tool is hidden from the list, Outline's own API enforces permissions on individual operations.

This feature composes with `OUTLINE_READ_ONLY` and `OUTLINE_DISABLE_DELETE`. If `OUTLINE_READ_ONLY=true`, write tools are never registered regardless of this setting.

## Per-Request Authentication

When running in HTTP mode (`sse` or `streamable-http`), you can pass the Outline API key per-request via the `x-outline-api-key` HTTP header instead of (or in addition to) the `OUTLINE_API_KEY` environment variable.

**Priority:** Header value takes precedence over the environment variable. If the header is not present, the server falls back to the env var.

**Use cases:**
- Multi-tenant deployments where different clients use different Outline accounts
- Centralized API key management via a reverse proxy or gateway
- Dynamic key rotation without restarting the server

**Example** (with a streamable-http server on port 3000):

Start the server:

```bash
docker run -p 3000:3000 \
  -e OUTLINE_API_KEY=<DEFAULT_KEY> \
  -e MCP_TRANSPORT=streamable-http \
  ghcr.io/vortiago/mcp-outline:latest
```

Then connect from your client with a per-request key:

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

> **Note:** The `x-outline-api-key` header is only available for HTTP transports. In `stdio` mode, the `OUTLINE_API_KEY` environment variable is the only option.
