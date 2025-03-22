"""
Outline MCP Server

A simple MCP server that provides document outline capabilities.
"""
from mcp.server.fastmcp import FastMCP
from mcp_outline.features import register_all

# Create a FastMCP server instance with a name
mcp = FastMCP("Document Outline")

# Register all features
register_all(mcp)

def main():
    # Start the server
    mcp.run()

if __name__ == "__main__":
    main()
