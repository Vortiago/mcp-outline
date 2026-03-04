"""Check Outline plugin configuration at session start."""

import os
import sys

CONFIG_PATH = "~/.config/mcp-outline/.env"


def main():
    if not os.environ.get("OUTLINE_API_KEY"):
        print(
            "[MCP Outline Plugin] OUTLINE_API_KEY is not set.\n"
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
