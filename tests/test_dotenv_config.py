"""
Tests for dotenv configuration loading from
.mcp-outline.env (project) and ~/.config/mcp-outline/.env (user).
"""

import os
import sys
from pathlib import Path
from unittest.mock import call, patch

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


def test_load_dotenv_called_project_then_user():
    """load_dotenv is called for project env first,
    then user config."""
    project = Path.cwd() / ".mcp-outline.env"
    user = Path.home() / ".config" / "mcp-outline" / ".env"

    with patch("dotenv.load_dotenv") as mock_load:
        import mcp_outline.server  # noqa: F401

        assert mock_load.call_count == 2
        mock_load.assert_has_calls([call(project), call(user)])


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


def test_env_var_loaded_from_user_file(tmp_path):
    """When OUTLINE_API_KEY is not set, the module-level
    load_dotenv populates it from the user config file."""
    config_dir = tmp_path / ".config" / "mcp-outline"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text("OUTLINE_API_KEY=from-file\n")

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)

    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            import mcp_outline.server  # noqa: F401

        assert os.environ["OUTLINE_API_KEY"] == "from-file"


def test_project_env_takes_priority(tmp_path):
    """Project-level .mcp-outline.env wins over user-level
    config when both exist."""
    # User config
    user_dir = tmp_path / ".config" / "mcp-outline"
    user_dir.mkdir(parents=True)
    (user_dir / ".env").write_text(
        "OUTLINE_API_KEY=from-user\nOUTLINE_API_URL=http://user-instance/api\n"
    )

    # Project config
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".mcp-outline.env").write_text(
        "OUTLINE_API_KEY=from-project\n"
        "OUTLINE_API_URL=http://project-instance/api\n"
    )

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env.pop("OUTLINE_API_URL", None)

    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch(
                "pathlib.Path.cwd",
                return_value=project_dir,
            ):
                import mcp_outline.server  # noqa: F401

        assert os.environ["OUTLINE_API_KEY"] == "from-project"
        assert os.environ["OUTLINE_API_URL"] == "http://project-instance/api"


def test_empty_env_vars_stripped_before_dotenv(tmp_path):
    """Empty OUTLINE_* env vars (from MCP client env blocks)
    should be stripped so dotenv can fill them from file."""
    config_dir = tmp_path / ".config" / "mcp-outline"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text(
        "OUTLINE_API_KEY=from-file\nOUTLINE_API_URL=http://localhost:3030\n"
    )

    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env.pop("OUTLINE_API_URL", None)
    # Simulate MCP client passing empty strings
    env["OUTLINE_API_KEY"] = ""
    env["OUTLINE_API_URL"] = ""

    with patch.dict(os.environ, env, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            import mcp_outline.server  # noqa: F401

        assert os.environ["OUTLINE_API_KEY"] == "from-file"
        assert os.environ["OUTLINE_API_URL"] == "http://localhost:3030"


def test_missing_config_file_no_error():
    """Server imports without error when config files
    do not exist."""
    with patch("dotenv.load_dotenv") as mock_load:
        mock_load.return_value = False
        import mcp_outline.server  # noqa: F401

        assert mock_load.call_count == 2


def test_stdio_exits_without_api_key(capsys):
    """In stdio mode, main() exits with error when no
    API key is configured."""
    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env["MCP_TRANSPORT"] = "stdio"

    with patch.dict(os.environ, env, clear=True):
        import mcp_outline.server

        with pytest.raises(SystemExit) as exc_info:
            mcp_outline.server.main()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "OUTLINE_API_KEY is not set" in err
        assert ".mcp-outline.env" in err


def test_stdio_starts_with_api_key():
    """In stdio mode, main() proceeds when API key is set."""
    with patch.dict(
        os.environ,
        {
            "OUTLINE_API_KEY": "ol_api_test",
            "MCP_TRANSPORT": "stdio",
        },
    ):
        import mcp_outline.server

        with patch.object(mcp_outline.server.mcp, "run") as mock_run:
            mcp_outline.server.main()
            mock_run.assert_called_once_with(transport="stdio")


def test_sse_skips_api_key_check():
    """In SSE mode, main() starts without API key
    (keys come per-request via headers)."""
    env = os.environ.copy()
    env.pop("OUTLINE_API_KEY", None)
    env["MCP_TRANSPORT"] = "sse"

    with patch.dict(os.environ, env, clear=True):
        import mcp_outline.server

        with patch.object(mcp_outline.server.mcp, "run") as mock_run:
            mcp_outline.server.main()
            mock_run.assert_called_once_with(transport="sse")
