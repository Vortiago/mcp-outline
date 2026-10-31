"""HTTP request headers for the MCP message in progress.

The SSE and streamable-http transports attach the Starlette request to
each message. A server middleware stores its headers here, so a tool or
the tool list can read them without a context parameter.
"""

from contextvars import ContextVar
from typing import Any, Optional

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from starlette.datastructures import Headers

# Written only by capture_request_headers, and reset when its message
# finishes. None for stdio and outside a message.
_headers: ContextVar[Optional[Headers]] = ContextVar(
    "mcp_outline_request_headers", default=None
)


async def capture_request_headers(
    ctx: ServerRequestContext[Any, Any], call_next: CallNext
) -> HandlerResult:
    """Server middleware that stores the request headers of a message."""
    request = ctx.request
    token = _headers.set(request.headers if request is not None else None)
    try:
        return await call_next(ctx)
    finally:
        _headers.reset(token)


def get_request_header(name: str) -> Optional[str]:
    """Return a header of the current HTTP request.

    None for stdio, outside a message, or when the header is absent.
    """
    headers = _headers.get()
    if headers is None:
        return None
    return headers.get(name)
