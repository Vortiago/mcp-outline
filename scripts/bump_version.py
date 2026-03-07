"""Bump version across all project files.

Usage: python scripts/bump_version.py <new_version>

Validates that the new version is a valid semver bump (major,
minor, or patch) from the current version in server.json.
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

VERSION_FILES = {
    "server.json": ROOT / "server.json",
    ".claude-plugin/plugin.json": (ROOT / ".claude-plugin" / "plugin.json"),
    ".claude-plugin/marketplace.json": (
        ROOT / ".claude-plugin" / "marketplace.json"
    ),
    ".github/plugin/marketplace.json": (
        ROOT / ".github" / "plugin" / "marketplace.json"
    ),
    ".mcp.json": ROOT / ".mcp.json",
}

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_version(v: str) -> tuple[int, int, int]:
    """Parse 'X.Y.Z' into (major, minor, patch)."""
    parts = v.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def read_current_version() -> str:
    """Read current version from server.json."""
    path = VERSION_FILES["server.json"]
    data = json.loads(path.read_text())
    return data["version"]


def valid_bumps(
    current: tuple[int, int, int],
) -> list[str]:
    """Return list of valid next versions."""
    major, minor, patch = current
    return [
        f"{major}.{minor}.{patch + 1}",
        f"{major}.{minor + 1}.0",
        f"{major + 1}.0.0",
    ]


def update_json_file(
    path: Path,
    version: str,
    updater: Callable[[dict[str, Any], str], None],
) -> None:
    """Read, update, and write a JSON file."""
    data = json.loads(path.read_text())
    updater(data, version)
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_server_json(data: dict[str, Any], version: str) -> None:
    """Update both version fields in server.json."""
    data["version"] = version
    if "packages" in data and len(data["packages"]) > 0:
        data["packages"][0]["version"] = version


def update_plugin_json(data: dict[str, Any], version: str) -> None:
    """Update version in plugin.json."""
    data["version"] = version


def update_marketplace_json(data: dict[str, Any], version: str) -> None:
    """Update version in marketplace.json plugins."""
    if "plugins" in data and len(data["plugins"]) > 0:
        data["plugins"][0]["version"] = version


def update_mcp_json(path: Path, version: str) -> None:
    """Update pinned version in .mcp.json args."""
    text = path.read_text()
    text = re.sub(
        r"mcp-outline==[\d.]+",
        f"mcp-outline=={version}",
        text,
    )
    path.write_text(text)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <version>")
        print("Example: python scripts/bump_version.py 1.8.0")
        sys.exit(1)

    new_version = sys.argv[1]

    if not VERSION_RE.match(new_version):
        print(f"Error: '{new_version}' is not valid X.Y.Z format")
        sys.exit(1)

    current_version = read_current_version()
    current = parse_version(current_version)
    allowed = valid_bumps(current)

    if new_version not in allowed:
        print(f"Error: {current_version} -> {new_version}")
        print(f"  Allowed bumps: {', '.join(allowed)}")
        sys.exit(1)

    # Update all files
    update_json_file(
        VERSION_FILES["server.json"],
        new_version,
        update_server_json,
    )
    update_json_file(
        VERSION_FILES[".claude-plugin/plugin.json"],
        new_version,
        update_plugin_json,
    )
    update_json_file(
        VERSION_FILES[".claude-plugin/marketplace.json"],
        new_version,
        update_marketplace_json,
    )
    update_json_file(
        VERSION_FILES[".github/plugin/marketplace.json"],
        new_version,
        update_marketplace_json,
    )
    update_mcp_json(VERSION_FILES[".mcp.json"], new_version)

    print(f"Version bumped: {current_version} -> {new_version}")
    print("Updated files:")
    for name in VERSION_FILES:
        print(f"  {name}")


if __name__ == "__main__":
    main()
