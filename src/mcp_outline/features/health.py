"""
Health check endpoints for MCP server.

Provides liveness and readiness probes for Docker/Kubernetes deployments.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse


def register_routes(mcp) -> None:
    """
    Register health check routes with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.custom_route(path="/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """
        Liveness check endpoint.

        Returns 200 OK if the server is running. Used by container
        orchestration systems to detect if the process is alive.

        Returns:
            JSON response with status "healthy"
        """
        return JSONResponse({"status": "healthy"})

    @mcp.custom_route(path="/ready", methods=["GET"])
    async def ready_check(request: Request) -> JSONResponse:
        """
        Readiness check endpoint.

        Verifies that:
        1. The server is running
        2. The Outline API key is configured
        3. The server can connect to Outline
        4. The API key is valid (by attempting collections.list)

        Returns 200 OK with detailed status, or appropriate error if not ready.

        Returns:
            JSON response with status and Outline connection info,
            or error details if not ready
        """
        try:
            # Import here to avoid circular imports
            from mcp_outline.features.documents.common import (
                get_outline_client,
            )

            # Get the outline client
            client = await get_outline_client()

            # Verify API connectivity by listing collections with limit=1
            # This verifies:
            # - Network connectivity to Outline
            # - API key is valid
            # - API endpoint is accessible
            await client.post("collections.list", {"limit": 1})

            # If we got here, everything is ready
            return JSONResponse(
                {
                    "status": "ready",
                    "outline": "connected",
                    "api_accessible": True,
                }
            )

        except Exception as e:
            # Not ready - return error with status code
            return JSONResponse(
                {
                    "status": "not_ready",
                    "outline": "disconnected",
                    "api_accessible": False,
                    "error": str(e),
                },
                status_code=503,  # Service Unavailable
            )
