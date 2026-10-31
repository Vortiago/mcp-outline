"""
Guardrail tests for critical dependency version pins in pyproject.toml.

A major release of the MCP Python SDK breaks the server (issue #134 for
v2). The ``mcp[cli]`` requirement keeps an upper bound that excludes the
next major release, so a routine re-lock cannot pull it in.
"""

import re
from pathlib import Path

from packaging.specifiers import SpecifierSet

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
_MCP_REQ = re.compile(r'"mcp\[cli\]([^"]*)"')


def _mcp_specifiers() -> list[str]:
    """Return the version specifier of every ``mcp[cli]`` requirement
    declared in pyproject.toml (runtime deps + dev group)."""
    text = _PYPROJECT.read_text(encoding="utf-8")
    return _MCP_REQ.findall(text)


def test_pyproject_declares_two_mcp_requirements():
    """Both the runtime deps and the dev group pin ``mcp[cli]``."""
    assert len(_mcp_specifiers()) == 2


def test_mcp_cli_pinned_below_v3():
    """Every ``mcp[cli]`` pin excludes the next major SDK release while
    allowing the v2 release the server is migrated to."""
    specs = _mcp_specifiers()
    assert specs, "no mcp[cli] requirement found in pyproject.toml"
    for spec in specs:
        sset = SpecifierSet(spec)
        assert not sset.contains("3.0.0", prereleases=True), (
            f"mcp[cli]{spec} allows the next major SDK release"
        )
        assert sset.contains("2.3.0"), (
            f"mcp[cli]{spec} must allow the migrated v2 release"
        )
