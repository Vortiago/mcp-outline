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

## Role-Based Filtering

Every tool carries `meta={"min_role": "viewer"|"member"|"admin"}`
declaring the minimum Outline role required.  At startup,
`build_role_blocked_map()` in `introspect.py` builds
`{role: frozenset(blocked_tool_names)}` from these annotations.

At runtime, `get_blocked_tools` calls `auth.info` to get the user's
role and looks it up in the map.  For example, a `"viewer"` sees
all tools whose `min_role` is `"viewer"`, but tools with
`min_role="member"` or `"admin"` are hidden.

This is independent of scope matching — both results are combined
(union).  Fails open: if `auth.info` errors, only scope matching
is applied.

**Important**: `min_role` is independent of `readOnlyHint`.
`readOnlyHint` controls `OUTLINE_READ_ONLY` module registration.
`min_role` controls per-request role filtering.  Examples:
- `add_comment`: `readOnlyHint=False` but `min_role="viewer"`
  (viewers can comment in Outline)
- `list_archived_documents`: `readOnlyHint=True` but
  `min_role="member"` (Outline requires Member role)

**Outline bug (v1.5.0)**: global scopes like `"read"` get `/api/`
prepended by storage normalisation and become broken route scopes.
Use namespaced scopes (`documents:read`) instead.
