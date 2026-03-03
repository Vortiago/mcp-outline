"""Check Outline plugin configuration at session start."""

import os
import sys


def main():
    if not os.environ.get("OUTLINE_API_KEY"):
        print(
            "[MCP Outline Plugin] OUTLINE_API_KEY is not set.\n"
            "\n"
            "To configure the Outline plugin:\n"
            "1. Get an API key from your Outline instance"
            " (Settings > API)\n"
            "2. Add to your shell profile"
            " (~/.bashrc or ~/.zshrc):\n"
            '   export OUTLINE_API_KEY="your-api-key-here"\n'
            "3. For self-hosted Outline, also set:\n"
            "   export OUTLINE_API_URL="
            '"https://your-instance.example.com/api"\n'
            "4. Restart Claude Code to apply changes."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
