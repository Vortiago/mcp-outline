"""Check Outline plugin configuration at session start."""

import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "mcp-outline" / ".env"


def _key_in_config_file() -> bool:
    """Check if OUTLINE_API_KEY is set in the config file."""
    try:
        for line in CONFIG_PATH.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("OUTLINE_API_KEY="):
                value = stripped.split("=", 1)[1].strip()
                if value:
                    return True
    except (OSError, ValueError):
        pass
    return False


def main():
    if os.environ.get("OUTLINE_API_KEY"):
        sys.exit(0)

    if _key_in_config_file():
        sys.exit(0)

    config_str = str(CONFIG_PATH)
    print(
        "[MCP Outline Plugin] OUTLINE_API_KEY is not set.\n"
        "\n"
        "To configure, create " + config_str + ":\n"
        "   mkdir -p ~/.config/mcp-outline\n"
        "   echo 'OUTLINE_API_KEY=your-key-here' > " + config_str + "\n"
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
