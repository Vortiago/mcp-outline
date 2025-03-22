# MCP Outline Server

A Model Context Protocol (MCP) server enabling AI assistants to interact with document outlines.

## Overview

This project implements a Model Context Protocol (MCP) server that allows AI assistants (like Claude) to interact with document outline services, providing a bridge between natural language interactions and document structure operations.

## Features

Currently implemented:
- **Document Outline Retrieval**: Get document outlines

Planned features:
- **Document Creation**: Create new documents with outlines
- **Outline Manipulation**: Add, move, and remove sections
- **Content Management**: Add and update content within outline sections
- **Document Export**: Export documents in various formats (Markdown, HTML, etc.)

## Getting Started

### Prerequisites

- Python 3.10+
- Document storage backend (to be determined)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-outline.git
cd mcp-outline

# Install in development mode
pip install -e ".[dev]"

# Install from PyPi
pip install mcp-outline
```

### Configuration

Create a `.env` file in the project root with the following variables:

```
# Configuration variables will go here
```

### Running the Server

```bash
# Development mode with the MCP Inspector
mcp dev src/mcp_outline/server.py

# Install in Claude Desktop
mcp install src/mcp_outline/server.py --name "Document Outline Assistant"
```

## Usage Examples

### Query Document Outline

```
Show me the outline for document "project-proposal"
```

### Create a New Document (Coming Soon)

```
Create a new document titled "Research Report" with sections for Introduction, Methodology, Results, and Discussion
```

### Modify an Outline (Coming Soon)

```
Add a new section called "Future Work" after the Discussion section in document "research-report"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
