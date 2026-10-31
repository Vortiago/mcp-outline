"""Compatibility with GitHub Copilot CLI.

Copilot CLI sends ``"arguments": ""`` instead of ``"arguments": {}`` for a
tool with no parameters, and the SDK rejects a string there. A server
middleware rewrites the raw params before the SDK validates them.

References:
- Similar issue in Vercel AI SDK: https://github.com/vercel/ai/issues/6687
- Similar issue in FastMCP: https://github.com/jlowin/fastmcp/issues/883
"""

from dataclasses import replace
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext


async def coerce_empty_tool_arguments(
    ctx: ServerRequestContext[Any, Any], call_next: CallNext
) -> HandlerResult:
    """Server middleware that turns empty-string tool arguments into {}."""
    params = ctx.params
    if (
        ctx.method == "tools/call"
        and params is not None
        and params.get("arguments") == ""
    ):
        ctx = replace(ctx, params={**params, "arguments": {}})
    return await call_next(ctx)
