"""Generate human-readable markdown docs from test docstrings.

Run via: uv run generate-test-docs
"""

import ast
import inspect
import subprocess
from pathlib import Path

# Repository root (two levels above this file's package)
_REPO_ROOT = Path(__file__).parent.parent.parent

# E2E test files to document
_E2E_DIR = _REPO_ROOT / "tests" / "e2e"
_E2E_FILES = sorted(_E2E_DIR.glob("test_*.py"))

# E2E companion files (fixtures, helpers) — documented separately
_E2E_COMPANIONS = [
    _E2E_DIR / "conftest.py",
    _E2E_DIR / "helpers.py",
]

# Top-level integration test files to document
_TOP_DIR = _REPO_ROOT / "tests"
_TOP_FILES = [
    _TOP_DIR / "test_health.py",
    _TOP_DIR / "test_mcp_integration.py",
]

# Output directory root
_DOCS_ROOT = _REPO_ROOT / "docs" / "tests"

# Overview file: tests/__init__.py → docs/tests/testing.md
_OVERVIEW_SRC = _TOP_DIR / "__init__.py"
_OVERVIEW_OUT = _DOCS_ROOT / "testing.md"


def _stem_to_title(stem: str) -> str:
    """Convert e.g. ``'test_batch_operations'`` to ``'Batch Operations'``."""
    without_prefix = stem.removeprefix("test_")
    return without_prefix.replace("_", " ").title()


def _is_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if *node* has a ``@pytest.fixture`` decorator.

    Handles both bare ``@pytest.fixture`` and called forms such as
    ``@pytest.fixture(scope="session")``.
    """
    for dec in node.decorator_list:
        # Unwrap Call node: @pytest.fixture(...) → check the func
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name) and target.id == "fixture":
            return True
        if (
            isinstance(target, ast.Attribute)
            and target.attr == "fixture"
            and isinstance(target.value, ast.Name)
            and target.value.id == "pytest"
        ):
            return True
    return False


def _get_docstring(node: ast.AST) -> str:
    """Return the docstring of an AST node, or empty string."""
    if not isinstance(
        node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        return ""
    if not (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return ""
    return inspect.cleandoc(node.body[0].value.value)


def _generate_file_doc(
    src: Path,
    out: Path,
    title: str | None = None,
    func_filter=lambda n: n.name.startswith("test_"),
) -> None:
    """Parse *src* and write a markdown doc to *out*.

    *func_filter* selects which top-level function nodes to include.
    Defaults to ``test_*`` functions. Pass a different predicate for
    companion files (e.g. ``lambda n: not n.name.startswith("__")``).
    """
    source = src.read_text(encoding="utf-8")
    tree = ast.parse(source)

    if title is None:
        title = _stem_to_title(src.stem)
    # Relative path from repo root for the attribution line
    rel = src.relative_to(_REPO_ROOT).as_posix()

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> Auto-generated from `{rel}`.")
    lines.append(
        "> Edit docstrings in the source file to update this document."
    )
    lines.append("")

    func_nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and func_filter(node)
    ]

    module_doc = _get_docstring(tree)
    sidecar = src.parent / f"{src.stem}.mmd"

    if module_doc:
        lines.append(module_doc.strip())
        lines.append("")

    if sidecar.exists():
        lines.append("```mermaid")
        lines.append(sidecar.read_text(encoding="utf-8").strip())
        lines.append("```")
        lines.append("")

    if (module_doc or sidecar.exists()) and func_nodes:
        lines.append("---")
        lines.append("")

    for node in func_nodes:
        func_title = node.name.removeprefix("test_").replace("_", " ").title()
        lines.append(f"## {func_title}")
        lines.append("")
        label = f"**`{node.name}`**"
        if _is_fixture(node):
            label += " *(fixture)*"
        lines.append(label)
        lines.append("")

        doc = _get_docstring(node)
        if doc:
            lines.append(doc.strip())
        lines.append("")

    # Write with trailing newline, no trailing whitespace on any line
    content = "\n".join(line.rstrip() for line in lines)
    if not content.endswith("\n"):
        content += "\n"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def generate_test_docs() -> None:
    """Generate markdown docs for all covered test files and stage them."""
    generated: list[Path] = []

    # E2E tests → docs/tests/e2e/<stem>.md
    for src in _E2E_FILES:
        stem = src.stem.removeprefix("test_")
        out = _DOCS_ROOT / "e2e" / f"{stem}.md"
        _generate_file_doc(src, out)
        generated.append(out)

    # E2E companions (conftest, helpers) → docs/tests/e2e/<stem>.md
    def _companion_filter(n: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return not n.name.startswith("__")

    for src in _E2E_COMPANIONS:
        out = _DOCS_ROOT / "e2e" / f"{src.stem}.md"
        _generate_file_doc(src, out, func_filter=_companion_filter)
        generated.append(out)

    # Top-level tests → docs/tests/<stem>.md
    for src in _TOP_FILES:
        stem = src.stem.removeprefix("test_")
        out = _DOCS_ROOT / f"{stem}.md"
        _generate_file_doc(src, out)
        generated.append(out)

    # Overview → docs/tests/testing.md
    _generate_file_doc(_OVERVIEW_SRC, _OVERVIEW_OUT, title="Testing")
    generated.append(_OVERVIEW_OUT)

    # Stage generated files so they're included in the current commit
    rel_paths = [str(p.relative_to(_REPO_ROOT)) for p in generated]
    subprocess.run(
        ["git", "add", "--"] + rel_paths,
        check=True,
        cwd=_REPO_ROOT,
    )
