# Contributing

Contributions are welcome! This guide will get you set up quickly.

## Quick Setup

```bash
# 1. Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/mcp-outline.git
cd mcp-outline

# 2. Install dependencies
uv sync --extra dev

# 3. Install pre-commit hooks (important!)
pre-commit install
```

That's it! The pre-commit hooks will automatically format and lint your code on every commit.

## Making Changes

1. Create a branch: `git checkout -b my-feature`
2. Make your changes
3. Commit - pre-commit runs automatically and fixes formatting
4. Push and open a PR

## Running Checks Manually

If you want to run checks before committing:

```bash
uv run ruff format .      # Format code
uv run ruff check .       # Lint code
uv run pyright src/       # Type check
uv run pytest tests/ -v   # Run tests
```

## Questions?

Open an issue on GitHub.
