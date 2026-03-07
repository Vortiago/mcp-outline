# Dynamic Tool List — Architecture

Per-user filtering of the MCP `tools/list` response based on API key scopes and Outline user role. Disabled by default; enable with `OUTLINE_DYNAMIC_TOOL_LIST=true`.

For configuration and setup, see [Configuration — Dynamic Tool List](configuration.md#dynamic-tool-list).

## Architecture Overview

The system has two phases: **startup** (build metadata maps from tool decorators) and **runtime** (filter `tools/list` per request).

```mermaid
flowchart TB
    subgraph Startup
        A["register_all(mcp)"] --> B["build_tool_endpoint_map()"]
        A --> C["build_write_tool_names()"]
        B --> D["install_dynamic_tool_list(mcp, maps)"]
        C --> D
        D --> E["Wrap tools/list handler"]
    end

    subgraph Runtime ["Runtime (per request)"]
        F["tools/list request"] --> G["Resolve API key"]
        G --> H["Check 1: Role (auth.info)"]
        H --> I["Check 2: Scopes (apiKeys.list)"]
        H --> J["Union blocked sets"]
        I --> J
        J --> K["Filter tool list"]
        K --> L["Return visible tools"]
    end

    E -.-> F
```

## Startup: Metadata Introspection

Every `@mcp.tool()` decorator carries two pieces of metadata that drive filtering:

```python
@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    meta={"endpoint": "documents.delete"},
)
async def delete_document(...) -> str:
```

After `register_all(mcp)`, `introspect.py` scans all registered tools via `mcp._tool_manager._tools` and builds:

| Map | Source | Purpose |
|-----|--------|---------|
| `tool_endpoint_map` | `meta["endpoint"]` | `{tool_name: "namespace.method"}` — used for scope matching |
| `write_tool_names` | `readOnlyHint=False` | `frozenset[str]` — used for viewer role blocking |

These maps are passed to `install_dynamic_tool_list()`, which wraps the `tools/list` protocol handler with a filtering function.

## Runtime: Per-Request Filtering

On each `tools/list` call, the wrapped handler:

1. Resolves the API key from `x-outline-api-key` header (HTTP) or `OUTLINE_API_KEY` env var (stdio)
2. Runs two checks sequentially (role, then scopes)
3. Unions the blocked sets
4. Filters out blocked tools from the response

### Check 1 — Role-Based Filtering

Calls `auth.info` to get the user's Outline role. If `viewer`, all write tools are blocked.

```mermaid
flowchart TD
    A["Call auth.info"] --> B{Response?}
    B -->|200| C{role == viewer?}
    C -->|Yes| D["Block all write tools"]
    C -->|No| E["Block nothing"]
    B -->|"403 (missing scope)"| F["Log WARNING\nBlock nothing"]
    B -->|Other error| E
```

**Fail-open**: if `auth.info` errors, no tools are blocked by this check. A 403 specifically logs a warning suggesting the operator add `auth.info` to the key's scope array.

### Check 2 — Scope-Based Filtering

Calls `apiKeys.list`, finds the key by its last 4 characters, reads the `scope` array, then checks each tool's endpoint against the scopes.

```mermaid
flowchart TD
    A["Call apiKeys.list"] --> B{Response?}
    B -->|"401 (invalid key)"| C["Block ALL tools"]
    B -->|"403 (missing scope)"| D["Log WARNING\nBlock nothing"]
    B -->|Other error| D
    B -->|200| E["Match key by last4"]
    E --> F{Key found?}
    F -->|No| D
    F -->|Yes| G{scope == null?}
    G -->|"null (full access)"| D
    G -->|"[scopes...]"| H["For each tool:\nis_endpoint_accessible(endpoint, scopes)?"]
    H --> I["Block inaccessible tools"]
```

**401 is special**: it means the key is invalid, expired, or revoked — *all* tools are hidden. Every other error fails open.

**last4 collision**: if multiple keys share the same last 4 digits, their scopes are unioned. If any matching key has `scope: null` (full access), the result is treated as full access.

## Scope Matching Algorithm

Mirrors Outline's [`AuthenticationHelper.canAccess`](https://github.com/outline/outline/blob/main/shared/helpers/AuthenticationHelper.ts). Implementation: `scope_matching.py`.

### Scope Formats

**Route scopes** — `/api/namespace.method`

Exact match with `*` wildcard support:

| Scope | Matches |
|-------|---------|
| `/api/documents.info` | `documents.info` only |
| `/api/documents.*` | Any method on `documents` |
| `/api/*.*` | Everything |

**Namespaced scopes** — `namespace:level`

The `level` determines which methods are accessible via a `methodToScope` mapping:

| Method | Maps to scope |
|--------|---------------|
| `create` | `create` |
| `config`, `list`, `info`, `search`, `documents`, `drafts`, `viewed`, `export` | `read` |
| Everything else (`update`, `delete`, `archive`, `restore`, `move`, `redirect`, `export_all`, `answerQuestion`, ...) | `write` (default) |

Level matching:

| Level | Grants |
|-------|--------|
| `read` | Methods that map to `read` |
| `create` | Only the `create` method |
| `write` | All methods (superset of read + create) |

**Wildcard namespace**: `*:read` matches the `read` level on any namespace.

### Gotchas

- `attachments:read` does **not** grant `attachments.redirect` — `redirect` defaults to `write`
- `collections:read` does **not** grant `collections.export_all` — `export_all` defaults to `write`
- Global scopes like `"read"` are broken in Outline v1.5.0 (storage normalisation prepends `/api/`). Use namespaced scopes (`documents:read`) instead

## Error Handling

The system is **fail-open by design** — if any check fails, the full tool list is shown. This is intentional: the dynamic tool list is a UX convenience, not a security boundary. Outline's API enforces permissions on individual operations regardless.

The single exception is **401 on `apiKeys.list`**, which indicates the key is invalid/expired/revoked. In this case, all tools are hidden to avoid showing tools that will all fail anyway.

| Scenario | Behavior |
|----------|----------|
| `auth.info` returns 403 | Log warning, skip role check |
| `auth.info` returns other error | Skip role check |
| `apiKeys.list` returns **401** | **Block all tools** |
| `apiKeys.list` returns 403 | Log warning, skip scope check |
| `apiKeys.list` returns other error | Skip scope check |
| Key not found by last4 | Skip scope check |
| Client init fails | Return full tool list |
| Any unexpected exception | Return full tool list |

## Module Structure

```
src/mcp_outline/features/dynamic_tools/
├── __init__.py          # Public exports
├── introspect.py        # Startup: build maps from tool metadata
├── filtering.py         # Runtime: per-request filtering logic
├── scope_matching.py    # Pure functions: Outline's scope algorithm
└── CLAUDE.md            # LLM-oriented reference
```

## Adding a New Tool

No changes needed in the dynamic tools module. Just ensure the `@mcp.tool()` decorator has:

1. **`meta={"endpoint": "namespace.method"}`** — the Outline API endpoint for scope matching
2. **`annotations=ToolAnnotations(readOnlyHint=True/False)`** — `False` for write tools (role filtering)

The maps are built automatically at startup. Integration tests (`test_all_tools_have_endpoint_meta`, `test_all_tools_have_read_only_hint`) verify every registered tool has both.
