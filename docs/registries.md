# Registries & Marketplaces

Where mcp-outline is listed and which files control each listing.

| Registry | Config Files | Published How | Notes |
|----------|-------------|---------------|-------|
| **PyPI** | `pyproject.toml` | CI on tag (`publish.yml`) | Version from git tag via setuptools-scm |
| **Docker (GHCR)** | `Dockerfile` | CI on tag | Image: `ghcr.io/vortiago/mcp-outline` |
| **MCP Official Registry** | `server.json` | CI on tag (`publish-mcp-registry.yml`) | Version patched from tag at publish time |
| **Glama** | `glama.json` | Manual claim at [glama.ai](https://glama.ai) | Only sets maintainer for ownership |
| **Claude Code Plugin** | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.mcp.json` | Repo discovery | Install: `/plugin marketplace add Vortiago/mcp-outline` |
| **VS Code / Copilot CLI Plugin** | `.github/plugin/marketplace.json`, `.claude-plugin/plugin.json`, `.mcp.json` | Repo discovery | Add repo as marketplace source via `chat.plugins.marketplaces` setting |

## File reference

- **`server.json`** — MCP Registry server manifest. Schema: `2025-12-11`. Versions updated by CI at publish time.
- **`glama.json`** — Glama ownership claim. Minimal: just `$schema` + `maintainers`.
- **`.claude-plugin/plugin.json`** — Claude Code plugin metadata (name, description, keywords).
- **`.claude-plugin/marketplace.json`** — Claude Code marketplace entry. Lists plugins available from this repo.
- **`.github/plugin/marketplace.json`** — VS Code / Copilot CLI marketplace entry. Same format as Claude Code marketplace, in the Copilot-standard location.
- **`.mcp.json`** — MCP server config used by both Claude Code and VS Code plugins. Defines how to run the server with env vars.
