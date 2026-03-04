"""Tests for the session start hook."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from check_outline_config import main


def test_exits_silently_with_env_var():
    """No warning when env var has a real value."""
    with patch.dict(os.environ, {"OUTLINE_API_KEY": "ol_api_real"}):
        with pytest.raises(SystemExit):
            main()


def test_warns_when_empty_string(capsys):
    """Empty string env var should trigger warning."""
    env = os.environ.copy()
    env["OUTLINE_API_KEY"] = ""
    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent")
            with pytest.raises(SystemExit):
                main()
    assert "OUTLINE_API_KEY is not set" in capsys.readouterr().out


def test_warns_when_unset(capsys):
    """Warning when env var is completely unset."""
    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent")
            with pytest.raises(SystemExit):
                main()
    assert "OUTLINE_API_KEY is not set" in capsys.readouterr().out


def test_exits_silently_with_config_file(tmp_path):
    """No warning when config file has the key."""
    env_file = tmp_path / ".config" / "mcp-outline" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("OUTLINE_API_KEY=ol_api_abc\n")

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env["OUTLINE_API_KEY"] = ""
    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with pytest.raises(SystemExit):
                main()


def test_warns_with_commented_config(tmp_path, capsys):
    """Warning when config file key is commented out."""
    env_file = tmp_path / ".config" / "mcp-outline" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("# OUTLINE_API_KEY=ol_api_abc\n")

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env["OUTLINE_API_KEY"] = ""
    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with pytest.raises(SystemExit):
                main()
    assert "OUTLINE_API_KEY is not set" in capsys.readouterr().out
