"""
Patch for GitHub Copilot CLI compatibility.

GitHub Copilot CLI has a bug where it sends "arguments": "" (empty string)
instead of "arguments": {} (empty object) for tools with no parameters.

This causes Pydantic validation to fail since the MCP SDK expects:
    arguments: dict[str, Any] | None

This patch replaces CallToolRequestParams with a subclass that includes
a validator to coerce empty strings to empty dicts.

References:
- Similar issue in Vercel AI SDK: https://github.com/vercel/ai/issues/6687
- Similar issue in FastMCP: https://github.com/jlowin/fastmcp/issues/883
"""

import logging
from typing import Any

from pydantic import field_validator


def patch_for_copilot_cli() -> None:
    """
    Patch MCP SDK's CallToolRequestParams to handle empty string arguments.

    This is a workaround for GitHub Copilot CLI sending "" instead of {}
    for tools with no parameters.

    The patch creates a subclass with a validator that coerces:
    - "" → {}
    - Other values pass through unchanged

    This is safe because:
    1. It only affects invalid input (empty string)
    2. Valid inputs ({}, None, {"key": "val"}) are unchanged
    3. Claude Desktop and other clients already send {} correctly
    """
    try:
        import mcp.types

        # Check if already patched
        if hasattr(mcp.types.CallToolRequestParams, "_copilot_cli_patched"):
            return

        # Import the original class
        OriginalCallToolRequestParams = mcp.types.CallToolRequestParams

        # Create a patched subclass
        class PatchedCallToolRequestParams(OriginalCallToolRequestParams):
            """Patched version that handles empty string arguments."""

            _copilot_cli_patched: bool = True

            @field_validator("arguments", mode="before")
            @classmethod
            def coerce_empty_string_to_dict(cls, v: Any) -> Any:
                """
                Convert empty string to empty dict.

                GitHub Copilot CLI sends "" for tools with no parameters,
                but MCP protocol expects {} or None. This validator
                normalizes the input.
                """
                if v == "":
                    return {}
                return v

        # Replace the original class in the module
        mcp.types.CallToolRequestParams = PatchedCallToolRequestParams

    except ImportError:
        # MCP SDK not installed - this is fine during testing
        pass
    except Exception as e:
        # Log but don't crash - the patch is optional
        logging.warning(f"Failed to apply GitHub Copilot CLI patch: {e}")
