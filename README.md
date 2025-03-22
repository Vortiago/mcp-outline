# MCP Outline Server

A Model Context Protocol (MCP) server enabling AI assistants to interact with Outline documentation services.

## Overview

This project implements a Model Context Protocol (MCP) server that allows AI assistants (like Claude) to interact with Outline, providing a bridge between natural language interactions and the Outline API to manage documentation.

## Features

Currently implemented:
- **Document Retrieval**: Search and retrieve documents from Outline
- **Content Management**: Read and browse documents in Outline workspaces

Planned features:
- **Document Creation**: Create new documents and update existing ones
- **Collaboration**: Manage comments and collaborative editing
- **Workspace Organization**: Organize collections and document structures

## Getting Started

### Prerequisites

- Python 3.9+
- Outline instance with API access
- API token with necessary permissions for Outline access

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-outline.git
cd mcp-outline

# Install in development mode
pip install -e ".[dev]"

# Install from PyPi
pip install mcp_outline
```

### Configuration

Create a `.env` file in the project root with the following variables:

```
OUTLINE_API_TOKEN=your_api_token
OUTLINE_URL=https://your-outline-instance.example.com
```

Note: Make sure to provide the full URL to your Outline instance.

### Running the Server

```bash
# Development mode with the MCP Inspector
mcp dev src/mcp_outline/server.py

# Install in Claude Desktop
mcp install src/mcp_outline/server.py --name "Outline Documentation Assistant"
```

## Usage Examples

### Search for Documents

```
Find all documents related to API authentication in our documentation
```

### Read Document Content (Coming Soon)

```
Show me the content of the "Getting Started" guide
```

### Create a New Document (Coming Soon)

```
Create a new document in the Development collection titled "API Rate Limiting"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Outline API](https://github.com/outline/outline/blob/main/docs/API.md)