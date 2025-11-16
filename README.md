# MCP Outline Server

A Model Context Protocol server for interacting with Outline document management.

## Features

- **Document operations**: Search, read, create, edit, archive documents
- **Collections**: List, create, manage document hierarchies
- **Comments**: Add and view threaded comments
- **Backlinks**: Find documents referencing a specific document
- **MCP Resources**: Direct content access via URIs (outline://document/{id}, outline://collection/{id}, etc.)
- **Automatic rate limiting**: Transparent handling of API limits with retry logic

## Installation

### Using uv (Recommended)

```bash
uvx mcp-outline
```

### Using pip

```bash
pip install mcp-outline
```

### Using Docker

```bash
docker run -e OUTLINE_API_KEY=<your-key> ghcr.io/vortiago/mcp-outline:latest
```

Or build from source:
```bash
docker buildx build -t mcp-outline .
docker run -e OUTLINE_API_KEY=<your-key> mcp-outline
```

## Configuration

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `OUTLINE_API_KEY` | Yes | - | API token from Outline Settings → API Keys |
| `OUTLINE_API_URL` | No | `https://app.getoutline.com/api` | Self-hosted Outline: `https://your-domain/api` |
| `MCP_TRANSPORT` | No | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | No | `127.0.0.1` | Use `0.0.0.0` in Docker for external access |
| `MCP_PORT` | No | `3000` | HTTP server port (for `sse`/`streamable-http`) |

## Adding to Your Client

> **Prerequisites**: Install `uv` with `pip install uv` or from [astral.sh/uv](https://docs.astral.sh/uv/)

<details>
<summary><b>Add to Claude Desktop</b></summary>

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "mcp-outline": {
      "command": "uvx",
      "args": ["mcp-outline"],
      "env": {
        "OUTLINE_API_KEY": "<YOUR_API_KEY>",
        "OUTLINE_API_URL": "<YOUR_OUTLINE_URL>" // Optional
      }
    }
  }
}
```

</details>

<details>
<summary><b>Add to Cursor</b></summary>

Go to **Settings → MCP** and click **Add Server**:

```json
{
  "mcp-outline": {
    "command": "uvx",
    "args": ["mcp-outline"],
    "env": {
      "OUTLINE_API_KEY": "<YOUR_API_KEY>",
      "OUTLINE_API_URL": "<YOUR_OUTLINE_URL>" // Optional
    }
  }
}
```

</details>

<details>
<summary><b>Add to VS Code</b></summary>

Create a `.vscode/mcp.json` file in your workspace with the following configuration:

```json
{
  "servers": {
    "mcp-outline": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-outline"],
      "env": {
        "OUTLINE_API_KEY": "<YOUR_API_KEY>"
      }
    }
  }
}
```

For self-hosted Outline instances, add `OUTLINE_API_URL` to the `env` object.

**Optional**: Use input variables for sensitive credentials:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "outline-api-key",
      "description": "Outline API Key",
      "password": true
    }
  ],
  "servers": {
    "mcp-outline": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-outline"],
      "env": {
        "OUTLINE_API_KEY": "${input:outline-api-key}"
      }
    }
  }
}
```

VS Code will automatically discover and load MCP servers from this configuration file. For more details, see the [official VS Code MCP documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

</details>

<details>
<summary><b>Add to Cline (VS Code)</b></summary>

In Cline extension settings, add to MCP servers:

```json
{
  "mcp-outline": {
    "command": "uvx",
    "args": ["mcp-outline"],
    "env": {
      "OUTLINE_API_KEY": "<YOUR_API_KEY>",
      "OUTLINE_API_URL": "<YOUR_OUTLINE_URL>" // Optional
    }
  }
}
```

</details>

<details>
<summary><b>Using pip instead of uvx</b></summary>

If you prefer to use `pip` instead:

```bash
pip install mcp-outline
```

Then in your client config, replace `"command": "uvx"` with `"command": "mcp-outline"` and remove the `"args"` line:

```json
{
  "mcp-outline": {
    "command": "mcp-outline",
    "env": {
      "OUTLINE_API_KEY": "<YOUR_API_KEY>",
      "OUTLINE_API_URL": "<YOUR_OUTLINE_URL>" // Optional
    }
  }
}
```

</details>

<details>
<summary><b>Docker Deployment (HTTP)</b></summary>

For remote access or Docker containers, use HTTP transport. This runs the **MCP server** on port 3000:

```bash
docker run -p 3000:3000 \
  -e OUTLINE_API_KEY=<YOUR_API_KEY> \
  -e MCP_TRANSPORT=streamable-http \
  ghcr.io/vortiago/mcp-outline:latest
```

Then connect from client:

```json
{
  "mcp-outline": {
    "url": "http://localhost:3000/mcp"
  }
}
```

**Note**: `OUTLINE_API_URL` should point to where your Outline instance is running, not localhost:3000.

</details>

## Tools

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

### Quick Start with Self-Hosted Outline

```bash
# Generate configuration
cp config/outline.env.example config/outline.env
openssl rand -hex 32 > /tmp/secret_key && openssl rand -hex 32 > /tmp/utils_secret
# Update config/outline.env with generated secrets

# Start all services
docker compose up -d

# Create API key: http://localhost:3030 → Settings → API Keys
# Add to .env: OUTLINE_API_KEY=<token>
```

### Setup

```bash
git clone https://github.com/Vortiago/mcp-outline.git
cd mcp-outline
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
uv run pytest tests/

# Format code
uv run ruff format .

# Type check
uv run pyright src/

# Lint
uv run ruff check .
```

### Running Locally

```bash
uv run mcp-outline
```

### Testing with MCP Inspector

Use the MCP Inspector to test the server tools visually via an interactive UI.

**For local development** (with stdio):

```bash
npx @modelcontextprotocol/inspector -e OUTLINE_API_KEY=<your-key> -e OUTLINE_API_URL=<your-url> uv run python -m mcp_outline
```

**For Docker Compose** (with HTTP):

```bash
npx @modelcontextprotocol/inspector http://localhost:3000
```

![MCP Inspector](./docs/mcp_inspector_guide.png)

## Architecture Notes

**Rate Limiting**: Automatically handled via header tracking (`RateLimit-Remaining`, `RateLimit-Reset`) with exponential backoff retry (up to 3 attempts). No configuration needed.

**Transport Modes**:
- `stdio` (default): Direct process communication
- `sse`: HTTP Server-Sent Events (use for web clients)
- `streamable-http`: Streamable HTTP transport

**Connection Pooling**: Shared httpx connection pool across instances (configurable: `OUTLINE_MAX_CONNECTIONS=100`, `OUTLINE_MAX_KEEPALIVE=20`)

## Contributing

Contributions welcome! Please submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Outline API](https://getoutline.com) for document management
