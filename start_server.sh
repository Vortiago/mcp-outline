#!/bin/bash
# Start the MCP Outline server.
# Primarily used during development to make it easier for Claude to access the server living inside WSL2.

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export $(grep -v '^#' .env | xargs)

# Run the server in development mode
python src/mcp_outline/server.py
