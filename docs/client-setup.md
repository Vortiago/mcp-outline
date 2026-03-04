# Client Setup

Instructions for connecting mcp-outline to your MCP client.

The examples below use [`uvx`](https://docs.astral.sh/uv/) to run mcp-outline without installing it globally. If you prefer `pip`, see [Using pip instead of uvx](#using-pip-instead-of-uvx).

## Claude Desktop

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

## Cursor

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

## VS Code

Create a `.vscode/mcp.json` file in your workspace:

```json
{
  "servers": {
    "mcp-outline": {
      "type": "stdio",
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

See the [official VS Code MCP documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) for more details.

## Cline (VS Code)

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

## Using pip Instead of uvx

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

## Docker Deployment (HTTP)

For remote access or Docker containers, use HTTP transport. This runs the MCP server on port 3000:

```bash
docker run -p 3000:3000 \
  -e OUTLINE_API_KEY=<YOUR_API_KEY> \
  -e MCP_TRANSPORT=streamable-http \
  ghcr.io/vortiago/mcp-outline:latest
```

Then connect from your client:

```json
{
  "mcp-outline": {
    "url": "http://localhost:3000/mcp"
  }
}
```

**Note**: `OUTLINE_API_URL` should point to where your Outline instance is running, not localhost:3000.

**Per-request API key**: In HTTP modes, clients can also pass the API key via the `x-outline-api-key` header instead of setting it as an env var. See [Configuration](configuration.md#per-request-authentication).
