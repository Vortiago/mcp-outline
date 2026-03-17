# Dynamic Tool List

Filters the MCP `tools/list` response per-user based on the API
key's scopes.  Calls `apiKeys.list` once, matches the key by `last4`,
then applies Outline's scope matching algorithm locally.

## Scope Matching

Mirrors `AuthenticationHelper.canAccess` from
[Outline source](https://github.com/outline/outline/blob/main/shared/helpers/AuthenticationHelper.ts).
See `scope_matching.py` for the implementation.

Two scope formats:

- **Route scopes** (`/api/namespace.method`) — exact match with `*` wildcards
- **Namespaced scopes** (`namespace:level`) — matched via `methodToScope`:

```
create    → "create"
config    → "read"
list      → "read"
info      → "read"
search    → "read"
documents → "read"
drafts    → "read"
viewed    → "read"
export    → "read"
(other)   → defaults to "write"
```

`redirect` and `export_all` are not in the mapping and default to
`write`.  So `attachments:read` and `collections:read` do **not**
grant access to `attachments.redirect` or `collections.export_all`.

## Error Behavior

Fail-open by default — if scope introspection fails, all tools
are shown.  Two exceptions fail-closed (all tools hidden):
- `apiKeys.list` returns 401 (invalid/expired key)
- API key not found by `last4` (deleted or mismatched key)
