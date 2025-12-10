"""
Response handler utility for MCP tool responses.

This module provides a standardized way to create MCP-compliant responses
with both human-readable text and structured content for programmatic use.
"""

import os
from typing import Any, Dict, Optional, Tuple

from mcp.types import CallToolResult, TextContent

# Response limits are opt-in (off by default, becomes default in v2.0)
LIMITS_ENABLED = os.getenv("OUTLINE_RESPONSE_LIMITS", "").lower() in (
    "true",
    "1",
    "yes",
)

# Structured output is opt-in (disabled by default)
STRUCTURED_OUTPUT_ENABLED = os.getenv(
    "OUTLINE_STRUCTURED_OUTPUT", ""
).lower() in ("true", "1", "yes")

# Token-based thresholds (~4 chars per token estimate)
# Only apply when LIMITS_ENABLED is True
CHARS_PER_TOKEN = 4
SOFT_LIMIT_TOKENS = int(
    os.getenv("OUTLINE_RESPONSE_SOFT_LIMIT_TOKENS", "5000")
)
HARD_LIMIT_TOKENS = int(
    os.getenv("OUTLINE_RESPONSE_HARD_LIMIT_TOKENS", "22500")
)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text length.

    Uses a simple heuristic of ~4 characters per token.

    Args:
        text: The text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // CHARS_PER_TOKEN


def check_response_size(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Check response size and apply warnings/truncation if needed.

    Args:
        text: The response text to check

    Returns:
        Tuple of (possibly_modified_text, metadata_dict)
    """
    tokens = estimate_tokens(text)
    meta: Dict[str, Any] = {"tokens": tokens, "chars": len(text)}

    if tokens > HARD_LIMIT_TOKENS:
        # Truncate with notice
        truncate_chars = HARD_LIMIT_TOKENS * CHARS_PER_TOKEN
        truncated = text[:truncate_chars]
        truncated += (
            f"\n\n⚠️ RESPONSE TRUNCATED "
            f"({tokens:,} → {HARD_LIMIT_TOKENS:,} tokens)"
        )
        truncated += (
            "\nUse get_document_outline + read_document_section "
            "for large docs."
        )
        meta["truncated"] = True
        meta["original_tokens"] = tokens
        return truncated, meta
    elif tokens > SOFT_LIMIT_TOKENS:
        # Add warning but don't truncate
        text += f"\n\n💡 Large response: ~{tokens:,} tokens"
        meta["warning"] = "large_response"
        return text, meta

    return text, meta


def create_tool_response(
    text: str, data: Optional[Dict[str, Any]] = None
) -> CallToolResult:
    """
    Create an MCP-compliant tool response with structured content.

    This function creates responses that include both:
    - Human-readable text in the `content` field (for LLM consumption)
    - Machine-parseable data in the `structuredContent` field (for
      programmatic use)

    Structured output is enabled by default but can be disabled via
    OUTLINE_DISABLE_STRUCTURED_OUTPUT=true for reduced payload size.
    Response size warnings/truncation are only applied when
    OUTLINE_RESPONSE_LIMITS is enabled.

    Args:
        text: Human-readable response text
        data: Optional structured data to include

    Returns:
        CallToolResult with both text content and optionally structured data
    """
    response_meta: Dict[str, Any] = {}

    # Apply warnings/truncation only if enabled
    if LIMITS_ENABLED:
        text, response_meta = check_response_size(text)

    # Build structured content only if enabled
    structured: Optional[Dict[str, Any]] = None
    if STRUCTURED_OUTPUT_ENABLED:
        structured = data.copy() if data else {}
        if response_meta:
            structured["response_meta"] = response_meta
        # Don't return empty dict
        if not structured:
            structured = None

    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structuredContent=structured,
    )
