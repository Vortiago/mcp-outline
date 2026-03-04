"""Tests for the session start hook that checks Outline
configuration."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# The hook lives outside the package, so add its directory
# to sys.path for import.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from check_outline_config import _has_api_key, _key_in_config_file

# -- _key_in_config_file tests --


def test_key_in_config_file_found(tmp_path):
    """Returns True when file has an uncommented key."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=ol_api_abc123\n")
    assert _key_in_config_file(env_file) is True


def test_key_in_config_file_commented(tmp_path):
    """Returns False when the key line is commented out."""
    env_file = tmp_path / ".env"
    env_file.write_text("# OUTLINE_API_KEY=ol_api_abc123\n")
    assert _key_in_config_file(env_file) is False


def test_key_in_config_file_empty_value(tmp_path):
    """Returns False when the key exists but value is empty."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=\n")
    assert _key_in_config_file(env_file) is False


def test_key_in_config_file_missing(tmp_path):
    """Returns False when the file does not exist."""
    env_file = tmp_path / "nonexistent" / ".env"
    assert _key_in_config_file(env_file) is False


def test_key_in_config_file_no_key_line(tmp_path):
    """Returns False when file exists but has no key line."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_URL=http://localhost\n")
    assert _key_in_config_file(env_file) is False


# -- _has_api_key tests --


def test_has_key_from_env_var(tmp_path):
    """Returns True when env var has a real value."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    with patch.dict(os.environ, {"OUTLINE_API_KEY": "ol_api_real"}):
        assert _has_api_key(env_file) is True


def test_has_key_empty_string_env_falls_through(tmp_path):
    """Empty string env var should NOT count as having a key.
    Falls through to config file check."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    with patch.dict(os.environ, {"OUTLINE_API_KEY": ""}):
        assert _has_api_key(env_file) is False


def test_has_key_empty_string_env_uses_config(tmp_path):
    """Empty string env var falls through to config file,
    which has the key."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=ol_api_abc123\n")
    with patch.dict(os.environ, {"OUTLINE_API_KEY": ""}):
        assert _has_api_key(env_file) is True


def test_has_key_unset_env_uses_config(tmp_path):
    """When env var is completely unset, falls through to
    config file."""
    env_file = tmp_path / ".env"
    env_file.write_text("OUTLINE_API_KEY=ol_api_abc123\n")
    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        assert _has_api_key(env_file) is True


def test_has_key_unset_env_no_config(tmp_path):
    """Returns False when env var unset and no config file."""
    env_file = tmp_path / "nonexistent" / ".env"
    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        assert _has_api_key(env_file) is False


def test_has_key_empty_env_commented_config(tmp_path):
    """Returns False when env var is empty and config key is
    commented out."""
    env_file = tmp_path / ".env"
    env_file.write_text("# OUTLINE_API_KEY=ol_api_abc123\n")
    with patch.dict(os.environ, {"OUTLINE_API_KEY": ""}):
        assert _has_api_key(env_file) is False
