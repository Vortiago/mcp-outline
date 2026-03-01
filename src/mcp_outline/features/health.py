"""
Health check endpoints for MCP server.

Provides liveness and readiness probes for Docker/Kubernetes deployments.
"""

import os

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_outline.utils.outline_client import _sanitize_value


def _get_outline_base_url() -> str:
    """Return the Outline base URL (without ``/api`` suffix)."""
    raw = _sanitize_value(os.getenv("OUTLINE_API_URL"))
    if not raw:
        return "https://app.getoutline.com"
    url = raw.rstrip("/")
    if url.lower().endswith("/api"):
        return url[: -len("/api")]
    return url


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

        Sends a HEAD request to the Outline base URL to verify
        the instance is reachable.  No API key is required.
        Any HTTP response means ready; only network/timeout
        errors return 503.

        Returns:
            JSON response with status and connection info,
            or error details if not ready
        """
        try:
            base_url = _get_outline_base_url()
            async with httpx.AsyncClient() as client:
                await client.head(base_url, timeout=5.0)

            return JSONResponse(
                {
                    "status": "ready",
                    "outline": "connected",
                    "api_accessible": True,
                }
            )

        except Exception as e:
            return JSONResponse(
                {
                    "status": "not_ready",
                    "outline": "disconnected",
                    "api_accessible": False,
                    "error": str(e),
                },
                status_code=503,
            )
