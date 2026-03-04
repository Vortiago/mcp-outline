"""Check Outline plugin configuration at session start."""

import os
import sys


def main():
    key = os.environ.get("OUTLINE_API_KEY", "")
    if key:
        sys.exit(0)

    # Check config file as fallback
    try:
        from pathlib import Path

        env_file = Path.home() / ".config" / "mcp-outline" / ".env"
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("OUTLINE_API_KEY="):
                if line.split("=", 1)[1].strip():
                    sys.exit(0)
    except Exception:
        pass

    print(
        "[MCP Outline Plugin] OUTLINE_API_KEY is not set.\n"
        "\n"
        "To configure, create ~/.config/mcp-outline/.env:\n"
        "   mkdir -p ~/.config/mcp-outline\n"
        "   echo 'OUTLINE_API_KEY=your-key-here'"
        " > ~/.config/mcp-outline/.env\n"
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
