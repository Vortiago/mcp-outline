#!/usr/bin/env python3
"""
Test script to verify MCP server functionality
"""

import asyncio
import os

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_mcp_server():
    """Test the MCP server by connecting and listing tools."""

    # Set environment for stdio mode
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    server_params = StdioServerParameters(
        command="python", args=["-m", "mcp_outline"], env=env
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                result = await session.initialize()
                print(f"Server initialized: {result.serverInfo.name}")
                print(f"Protocol version: {result.protocolVersion}")

                # List available tools
                tools_result = await session.list_tools()
                print(f"\nAvailable tools ({len(tools_result.tools)}):")
                for tool in tools_result.tools:
                    print(f"- {tool.name}: {tool.description}")

                return True

    except Exception as e:
        print(f"Error testing MCP server: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    exit(0 if success else 1)
