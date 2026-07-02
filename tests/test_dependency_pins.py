"""
Guardrail tests for critical dependency version pins in pyproject.toml.

Issue #134: the MCP Python SDK v2 is a breaking release (stateless
protocol core -- no ``initialize`` handshake, no ``Mcp-Session-Id``
header). The ``mcp[cli]`` requirement must keep an upper bound that
excludes v2 so a routine re-lock cannot silently pull it in.
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


def test_mcp_cli_pinned_below_v2():
    """Every ``mcp[cli]`` pin excludes the breaking SDK v2 while still
    allowing the latest v1 release (issue #134)."""
    specs = _mcp_specifiers()
    assert specs, "no mcp[cli] requirement found in pyproject.toml"
    for spec in specs:
        sset = SpecifierSet(spec)
        assert not sset.contains("2.0.0", prereleases=True), (
            f"mcp[cli]{spec} allows the breaking SDK v2"
        )
        assert sset.contains("1.28.1"), (
            f"mcp[cli]{spec} must still allow the latest v1 release"
        )
