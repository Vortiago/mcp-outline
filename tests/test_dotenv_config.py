"""
Tests for dotenv configuration loading from
~/.config/mcp-outline/.env.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clean_server_module():
    """Remove cached server module so each test re-executes
    module-level code."""
    mods = [k for k in sys.modules if k.startswith("mcp_outline.server")]
    for m in mods:
        del sys.modules[m]
    yield
    mods = [k for k in sys.modules if k.startswith("mcp_outline.server")]
    for m in mods:
        del sys.modules[m]


def test_load_dotenv_called_with_config_path():
    """load_dotenv is called with ~/.config/mcp-outline/.env."""
    expected = Path.home() / ".config" / "mcp-outline" / ".env"

    with patch("dotenv.load_dotenv") as mock_load:
        import mcp_outline.server  # noqa: F401

        mock_load.assert_called_once_with(expected)


def test_env_var_not_overridden(tmp_path):
    """An existing OUTLINE_API_KEY env var must survive the
    module-level load_dotenv call (override=False default)."""
    config_dir = tmp_path / ".config" / "mcp-outline"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text("OUTLINE_API_KEY=from-file\n")

    with patch.dict(os.environ, {"OUTLINE_API_KEY": "from-env"}):
        with patch("pathlib.Path.home", return_value=tmp_path):
            import mcp_outline.server  # noqa: F401

        assert os.environ["OUTLINE_API_KEY"] == "from-env"


def test_env_var_loaded_from_file(tmp_path):
    """When OUTLINE_API_KEY is not set, the module-level
    load_dotenv populates it from the config file."""
    config_dir = tmp_path / ".config" / "mcp-outline"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text("OUTLINE_API_KEY=from-file\n")

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)

    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            import mcp_outline.server  # noqa: F401

        assert os.environ["OUTLINE_API_KEY"] == "from-file"


def test_missing_config_file_no_error():
    """Server imports without error when the config file does
    not exist."""
    with patch("dotenv.load_dotenv") as mock_load:
        mock_load.return_value = False
        import mcp_outline.server  # noqa: F401

        mock_load.assert_called_once()
