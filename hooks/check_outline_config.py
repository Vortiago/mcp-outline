"""Check Outline plugin configuration at session start."""

import os
import sys
from pathlib import Path

CONFIG_PATH = "~/.config/mcp-outline/.env"


def _key_in_config_file(
    path: "Path | None" = None,
) -> bool:
    """Check if OUTLINE_API_KEY is set in the config file."""
    if path is None:
        path = Path.home() / ".config" / "mcp-outline" / ".env"
    try:
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("OUTLINE_API_KEY="):
                value = stripped.split("=", 1)[1].strip()
                if value:
                    return True
    except (OSError, ValueError):
        pass
    return False


def _has_api_key(
    path: "Path | None" = None,
) -> bool:
    """Return True if OUTLINE_API_KEY is available from
    env vars or config file."""
    env_val = os.environ.get("OUTLINE_API_KEY")
    if env_val is not None and env_val != "":
        return True
    return _key_in_config_file(path)


def main():
    try:
        if _has_api_key():
            sys.exit(0)
    except Exception:
        # If config check fails, fall through to warning
        pass

    print(
        "[MCP Outline Plugin] OUTLINE_API_KEY is not"
        " set.\n"
        "\n"
        "To configure, create " + CONFIG_PATH + ":\n"
        "   mkdir -p ~/.config/mcp-outline\n"
        "   echo 'OUTLINE_API_KEY=your-key-here' > " + CONFIG_PATH + "\n"
        "\n"
        "For self-hosted Outline, also add:\n"
        "   OUTLINE_API_URL="
        "https://your-instance.example.com/api\n"
        "\n"
        "Get your API key from your Outline instance"
        " (Settings > API).\n"
        "Restart Claude Code after configuring."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
