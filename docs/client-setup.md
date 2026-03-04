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

**One-click install**: [![Install in Cursor](https://img.shields.io/badge/Install_in-Cursor-000000?style=flat-square&logoColor=white)](https://cursor.com/en/install-mcp?name=mcp-outline&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJtY3Atb3V0bGluZSJdLCJlbnYiOnsiT1VUTElORV9BUElfS0VZIjoiJHtpbnB1dDpvdXRsaW5lX2FwaV9rZXl9IiwiT1VUTElORV9BUElfVVJMIjoiJHtpbnB1dDpvdXRsaW5lX2FwaV91cmx9In0sImlucHV0cyI6W3siaWQiOiJvdXRsaW5lX2FwaV9rZXkiLCJ0eXBlIjoicHJvbXB0U3RyaW5nIiwiZGVzY3JpcHRpb24iOiJFbnRlciBPVVRMSU5FX0FQSV9LRVkiLCJwYXNzd29yZCI6dHJ1ZX0seyJpZCI6Im91dGxpbmVfYXBpX3VybCIsInR5cGUiOiJwcm9tcHRTdHJpbmciLCJkZXNjcmlwdGlvbiI6Ik91dGxpbmUgQVBJIFVSTCAob3B0aW9uYWwsIGZvciBzZWxmLWhvc3RlZCkiLCJwYXNzd29yZCI6ZmFsc2V9XX0=)

Or go to **Settings → MCP** and click **Add Server**:

```json
{
  "mcp-outline": {
    "command": "uvx",
    "args": ["mcp-outline"],
    "env": {
      "OUTLINE_API_KEY": "${input:outline_api_key}",
      "OUTLINE_API_URL": "${input:outline_api_url}"
    },
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
    ]
  }
}
```

## VS Code

**One-click install**: [![Install in VS Code](https://img.shields.io/badge/Install_in-VS_Code-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=mcp-outline&inputs=%5B%7B%22id%22%3A%22outline_api_key%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20OUTLINE_API_KEY%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22outline_api_url%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Outline%20API%20URL%20(optional%2C%20for%20self-hosted)%22%2C%22password%22%3Afalse%7D%5D&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-outline%22%5D%2C%22env%22%3A%7B%22OUTLINE_API_KEY%22%3A%22%24%7Binput%3Aoutline_api_key%7D%22%2C%22OUTLINE_API_URL%22%3A%22%24%7Binput%3Aoutline_api_url%7D%22%7D%7D)

Or create a `.vscode/mcp.json` file in your workspace (recommended — uses secure password prompts):

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "outline_api_key",
      "description": "Enter OUTLINE_API_KEY",
      "password": true
    },
    {
      "type": "promptString",
      "id": "outline_api_url",
      "description": "Outline API URL (optional, for self-hosted)",
      "password": false
    }
  ],
  "servers": {
    "mcp-outline": {
      "type": "stdio",
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

You can also install via the CLI:

```bash
code --add-mcp '{"name":"mcp-outline","command":"uvx","args":["mcp-outline"],"env":{"OUTLINE_API_KEY":"${input:outline_api_key}","OUTLINE_API_URL":"${input:outline_api_url}"},"inputs":[{"id":"outline_api_key","type":"promptString","description":"Enter OUTLINE_API_KEY","password":true},{"id":"outline_api_url","type":"promptString","description":"Outline API URL (optional, for self-hosted)","password":false}]}'
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

## Claude Code (Plugin)

Install directly as a Claude Code plugin from GitHub:

```bash
/plugin marketplace add Vortiago/mcp-outline
/plugin install mcp-outline@mcp-outline
```

Or test locally during development:

```bash
claude --plugin-dir ./path-to-mcp-outline
```

Set your Outline API key in your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export OUTLINE_API_KEY="your-api-key-here"
# For self-hosted Outline:
export OUTLINE_API_URL="https://your-instance.example.com/api"
```

Restart Claude Code after setting environment variables. The plugin includes a session start hook that will remind you if `OUTLINE_API_KEY` is not configured.

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

**Per-user Outline API key**: In HTTP modes, each user can pass their own Outline API key via the `x-outline-api-key` header instead of setting it as an env var:

```json
{
  "mcp-outline": {
    "type": "http",
    "url": "http://localhost:3000/mcp",
    "headers": {
      "x-outline-api-key": "<YOUR_API_KEY>"
    }
  }
}
```

See [Configuration](configuration.md#per-user-outline-api-keys) for more details.
