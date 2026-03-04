"""
Tests for dotenv configuration loading from
~/.config/mcp-outline/.env.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clean_server_module():
    """Remove cached server module so each test re-executes
    module-level code."""
    import sys

    mods = [k for k in sys.modules if k.startswith("mcp_outline.server")]
    for m in mods:
        del sys.modules[m]
    yield
    mods = [k for k in sys.modules if k.startswith("mcp_outline.server")]
    for m in mods:
        del sys.modules[m]


def test_load_dotenv_called_with_config_path():
    """load_dotenv should be called with
    ~/.config/mcp-outline/.env."""
    expected = Path.home() / ".config" / "mcp-outline" / ".env"

    with patch("dotenv.load_dotenv") as mock_load:
        import mcp_outline.server  # noqa: F401

        mock_load.assert_called_once_with(expected)


def test_env_vars_not_overridden_by_dotenv(tmp_path):
    """Existing environment variables should take priority
    over values in the config file."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=from-file\n")

    with patch.dict(os.environ, {"OUTLINE_API_KEY": "from-env"}):
        with patch("mcp_outline.server._config_path", env_file):
            # load_dotenv with override=False (default) won't
            # replace existing env vars.
            from dotenv import load_dotenv

            load_dotenv(env_file)
            assert os.environ["OUTLINE_API_KEY"] == "from-env"


def test_dotenv_loads_when_no_env_var(tmp_path):
    """Config file values should be used when no env var is
    set."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=from-file\n")

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OUTLINE_API_KEY", None)
        from dotenv import load_dotenv

        load_dotenv(env_file)
        assert os.environ["OUTLINE_API_KEY"] == "from-file"

    # Clean up
    os.environ.pop("OUTLINE_API_KEY", None)


def test_missing_config_file_is_harmless():
    """Server should start fine when config file doesn't
    exist."""
    with patch("dotenv.load_dotenv") as mock_load:
        mock_load.return_value = False  # file not found
        import mcp_outline.server  # noqa: F401

        # No exception raised
        mock_load.assert_called_once()
