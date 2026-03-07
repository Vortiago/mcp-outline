# MCP Outline Server

<!-- mcp-name: io.github.Vortiago/mcp-outline -->

[![PyPI](https://img.shields.io/pypi/v/mcp-outline)](https://pypi.org/project/mcp-outline/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Vortiago/mcp-outline/actions/workflows/ci.yml/badge.svg)](https://github.com/Vortiago/mcp-outline/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/Vortiago/mcp-outline/pkgs/container/mcp-outline)

A Model Context Protocol server for interacting with Outline document management.

## Features

- **Document operations**: Search, read, create, edit, archive documents
- **Collections**: List, create, manage document hierarchies
- **Comments**: Add and view threaded comments
- **Backlinks**: Find documents referencing a specific document
- **MCP Resources**: Direct content access via URIs (outline://document/{id}, outline://collection/{id}, etc.)
- **Automatic rate limiting**: Transparent handling of API limits with retry logic

## Prerequisites

Before using this MCP server, you need:

- An [Outline](https://www.getoutline.com/) account (cloud hosted or self-hosted)
- API key from Outline web UI: **Settings → API Keys → Create New**
- Python 3.10+ (for non-Docker installations)

> **Getting your API key**: Log into Outline → Click your profile → Settings → API Keys → "New API Key". Copy the generated token.

## Quick Start

### One-Click Install

Click a button to install with interactive API key prompt:

[![Install in VS Code](https://img.shields.io/badge/Install_in-VS_Code-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=mcp-outline&inputs=%5B%7B%22id%22%3A%22outline_api_key%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20OUTLINE_API_KEY%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22outline_api_url%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Outline%20API%20URL%20(optional%2C%20for%20self-hosted)%22%2C%22password%22%3Afalse%7D%5D&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-outline%22%5D%2C%22env%22%3A%7B%22OUTLINE_API_KEY%22%3A%22%24%7Binput%3Aoutline_api_key%7D%22%2C%22OUTLINE_API_URL%22%3A%22%24%7Binput%3Aoutline_api_url%7D%22%7D%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/Install_in-VS_Code_Insiders-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=mcp-outline&inputs=%5B%7B%22id%22%3A%22outline_api_key%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20OUTLINE_API_KEY%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22outline_api_url%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Outline%20API%20URL%20(optional%2C%20for%20self-hosted)%22%2C%22password%22%3Afalse%7D%5D&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-outline%22%5D%2C%22env%22%3A%7B%22OUTLINE_API_KEY%22%3A%22%24%7Binput%3Aoutline_api_key%7D%22%2C%22OUTLINE_API_URL%22%3A%22%24%7Binput%3Aoutline_api_url%7D%22%7D%7D&quality=insiders)
[![Install in Cursor](https://img.shields.io/badge/Install_in-Cursor-000000?style=flat-square&logoColor=white)](https://cursor.com/en/install-mcp?name=mcp-outline&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJtY3Atb3V0bGluZSJdLCJlbnYiOnsiT1VUTElORV9BUElfS0VZIjoiJHtpbnB1dDpvdXRsaW5lX2FwaV9rZXl9IiwiT1VUTElORV9BUElfVVJMIjoiJHtpbnB1dDpvdXRsaW5lX2FwaV91cmx9In0sImlucHV0cyI6W3siaWQiOiJvdXRsaW5lX2FwaV9rZXkiLCJ0eXBlIjoicHJvbXB0U3RyaW5nIiwiZGVzY3JpcHRpb24iOiJFbnRlciBPVVRMSU5FX0FQSV9LRVkiLCJwYXNzd29yZCI6dHJ1ZX0seyJpZCI6Im91dGxpbmVfYXBpX3VybCIsInR5cGUiOiJwcm9tcHRTdHJpbmciLCJkZXNjcmlwdGlvbiI6Ik91dGxpbmUgQVBJIFVSTCAob3B0aW9uYWwsIGZvciBzZWxmLWhvc3RlZCkiLCJwYXNzd29yZCI6ZmFsc2V9XX0=)

### Manual Install

Install with uv (recommended), pip, or Docker:

```bash
uvx mcp-outline          # using uv
pip install mcp-outline   # using pip
```

```bash
# using Docker
docker run -e OUTLINE_API_KEY=<your-key> ghcr.io/vortiago/mcp-outline:latest
```

Then add to your MCP client config (works with VS Code, Claude Desktop, Cursor, and others):

```json
{
  "inputs": [
    {
      "id": "outline_api_key",
      "type": "promptString",
      "description": "Enter OUTLINE_API_KEY",
      "password": true
    },
    {
      "id": "outline_api_url",
      "type": "promptString",
      "description": "Outline API URL (optional, for self-hosted)",
      "password": false
    }
  ],
  "servers": {
    "mcp-outline": {
      "command": "uvx",
      "args": ["mcp-outline"],
      "env": {
        "OUTLINE_API_KEY": "${input:outline_api_key}",
        "OUTLINE_API_URL": "${input:outline_api_url}"
      }
    }
  }
}
```

<details>
<summary>VS Code Agent Plugin</summary>

Add this repo as a plugin marketplace source in VS Code settings:

```json
"chat.plugins.marketplaces": ["Vortiago/mcp-outline"]
```

Then search for `@agentPlugins mcp-outline` in the Extensions view.
</details>

<details>
<summary>Claude Code</summary>

```bash
claude mcp add mcp-outline uvx mcp-outline
```
</details>

<details>
<summary>Claude Desktop</summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-outline": {
      "command": "uvx",
      "args": ["mcp-outline"],
      "env": {
        "OUTLINE_API_KEY": "<YOUR_API_KEY>",
        "OUTLINE_API_URL": "<YOUR_OUTLINE_URL>"
      }
    }
  }
}
```
</details>

Setup guides for more clients: [Docker (HTTP), Cline, Codex, Windsurf, and others](docs/client-setup.md)

## Configuration

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `OUTLINE_API_KEY` | Yes* | - | Required for tool calls to succeed. For SSE/HTTP, can alternatively be provided per-request via `x-outline-api-key` header ([details](docs/configuration.md#per-user-outline-api-keys)) |
| `OUTLINE_API_URL` | No | `https://app.getoutline.com/api` | For self-hosted: `https://your-domain/api` |
| `OUTLINE_VERIFY_SSL` | No | `true` | Set `false` for self-signed certificates |
| `OUTLINE_READ_ONLY` | No | `false` | `true` = disable ALL write operations ([details](docs/configuration.md#read-only-mode)) |
| `OUTLINE_DISABLE_DELETE` | No | `false` | `true` = disable only delete operations ([details](docs/configuration.md#disable-delete-operations)) |
| `OUTLINE_DISABLE_AI_TOOLS` | No | `false` | `true` = disable AI tools (for Outline instances without OpenAI) |
| `OUTLINE_DYNAMIC_TOOL_LIST` | No | `false` | `true` = enable per-user tool filtering by role/key scopes ([details](docs/configuration.md#dynamic-tool-list)) |
| `OUTLINE_MAX_CONNECTIONS` | No | `100` | Max concurrent connections in pool |
| `OUTLINE_MAX_KEEPALIVE` | No | `20` | Max idle connections in pool |
| `OUTLINE_TIMEOUT` | No | `30.0` | Read timeout in seconds |
| `OUTLINE_CONNECT_TIMEOUT` | No | `5.0` | Connection timeout in seconds |
| `OUTLINE_WRITE_TIMEOUT` | No | `30.0` | Write timeout in seconds |
| `MCP_TRANSPORT` | No | `stdio` | Transport mode: `stdio` (local), `sse` or `streamable-http` (remote) |
| `MCP_HOST` | No | `127.0.0.1` | Server host. Use `0.0.0.0` in Docker for external connections |
| `MCP_PORT` | No | `3000` | HTTP server port (only for `sse` and `streamable-http` modes) |

## Access Control

| Feature | Env Var | Effect |
|---------|---------|--------|
| Read-only mode | `OUTLINE_READ_ONLY=true` | Disables all write operations — only search, read, and export tools available |
| Disable deletes | `OUTLINE_DISABLE_DELETE=true` | Disables only delete operations, all other writes allowed |
| Dynamic tool list | `OUTLINE_DYNAMIC_TOOL_LIST=true` | Filters tools per-user based on Outline role and API key scopes |
| Per-user Outline API keys | `x-outline-api-key` header | Each user passes their own Outline API key in HTTP mode for multi-user setups |

Read-only mode takes precedence over disable-delete. See [Configuration Guide](docs/configuration.md) for details.

## Tools

> **Note**: Tool availability depends on your [access control](#access-control) settings.

### Search & Discovery
- `search_documents(query, collection_id?, limit?, offset?)` - Search documents by keywords with pagination
- `list_collections()` - List all collections
- `get_collection_structure(collection_id)` - Get document hierarchy within a collection
- `get_document_id_from_title(query, collection_id?)` - Find document ID by title search

### Document Reading
- `read_document(document_id)` - Get document content
- `export_document(document_id)` - Export document as markdown

### Document Management
- `create_document(title, collection_id, text?, parent_document_id?, publish?)` - Create new document
- `update_document(document_id, title?, text?, append?)` - Update document (append mode available)
- `move_document(document_id, collection_id?, parent_document_id?)` - Move document to different collection or parent

### Document Lifecycle
- `archive_document(document_id)` - Archive document
- `unarchive_document(document_id)` - Restore document from archive
- `delete_document(document_id, permanent?)` - Delete document (or move to trash)
- `restore_document(document_id)` - Restore document from trash
- `list_archived_documents()` - List all archived documents
- `list_trash()` - List all documents in trash

### Comments & Collaboration
- `add_comment(document_id, text, parent_comment_id?)` - Add comment to document (supports threaded replies)
- `list_document_comments(document_id, include_anchor_text?, limit?, offset?)` - View document comments with pagination
- `get_comment(comment_id, include_anchor_text?)` - Get specific comment details
- `get_document_backlinks(document_id)` - Find documents that link to this document

### Collection Management
- `create_collection(name, description?, color?)` - Create new collection
- `update_collection(collection_id, name?, description?, color?)` - Update collection properties
- `delete_collection(collection_id)` - Delete collection
- `export_collection(collection_id, format?)` - Export collection (default: outline-markdown)
- `export_all_collections(format?)` - Export all collections

### Batch Operations
- `batch_create_documents(documents)` - Create multiple documents at once
- `batch_update_documents(updates)` - Update multiple documents at once
- `batch_move_documents(document_ids, collection_id?, parent_document_id?)` - Move multiple documents
- `batch_archive_documents(document_ids)` - Archive multiple documents
- `batch_delete_documents(document_ids, permanent?)` - Delete multiple documents

### AI-Powered
- `ask_ai_about_documents(question, collection_id?, document_id?)` - Ask natural language questions about your documents

## Resources

- `outline://collection/{id}` - Collection metadata (name, description, color, document count)
- `outline://collection/{id}/tree` - Hierarchical document tree structure
- `outline://collection/{id}/documents` - Flat list of documents in collection
- `outline://document/{id}` - Full document content (markdown)
- `outline://document/{id}/backlinks` - Documents that link to this document

## Development

```bash
git clone https://github.com/Vortiago/mcp-outline.git
cd mcp-outline
uv sync --group dev

uv run poe test-unit          # unit tests
uv run poe test-integration   # integration tests (starts MCP server via stdio)
uv run poe test-e2e           # E2E tests (requires Docker)
```

See [Development Guide](docs/development.md) for self-hosted Outline setup, MCP Inspector, and more.

## Troubleshooting

**Server not connecting?** Test your API key:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" YOUR_OUTLINE_URL/api/auth.info
```

See [Troubleshooting Guide](docs/troubleshooting.md) for common issues with tools, rate limiting, and Docker.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Outline API](https://getoutline.com) for document management
