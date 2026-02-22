"""Dev test runner scripts (invoked via uv run test-*)."""


def test_unit() -> None:
    import sys

    import pytest

    sys.exit(pytest.main(["tests/", "-v", "--cov=src/mcp_outline"]))


def test_integration() -> None:
    import sys

    import pytest

    sys.exit(pytest.main(["tests/", "-v", "-m", "integration"]))


def test_e2e() -> None:
    import sys

    import pytest

    sys.exit(pytest.main(["tests/e2e/", "-v", "-m", "e2e"]))
