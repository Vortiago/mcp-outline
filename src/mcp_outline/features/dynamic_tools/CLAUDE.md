# Dynamic Tool List — Outline Scope Reference

How the dynamic tool list feature determines API key permissions.

## How It Works

The feature calls the `apiKeys.list` endpoint once per API key to
retrieve the key's stored scopes.  It matches the current key by
comparing the last 4 characters against the `last4` field in the
response.  The scope array is then evaluated locally using
Outline's `canAccess` algorithm to determine which tools to show.

**Requirement**: scoped API keys must include `apiKeys.list` in
their scope array.  Without it, the feature degrades gracefully
(shows all tools).

**Key matching**: the current key is identified by comparing its
last 4 characters against the `last4` field in the response.  If
multiple keys share the same `last4` (collision), all their scopes
are combined (union).  If any matching key has `null` scope (full
access), the result is full access.  This is consistent with the
fail-open design: the combined scopes are the most permissive
possible, so no tools are hidden unnecessarily.

**Error handling**:
- 401 from `apiKeys.list` → key is invalid → block ALL tools
- 403 or other errors → fail-open (show all tools)
- Key not found in response → fail-open

## Outline Source Files

- **Scope enum** (`Scope.Read`, `Scope.Write`, `Scope.Create`):
  <https://github.com/outline/outline/blob/main/shared/types.ts>
- **`canAccess(path, scopes)`** — path-to-scope matching logic:
  <https://github.com/outline/outline/blob/main/shared/helpers/AuthenticationHelper.ts>
- **`ApiKey` model** — scope stored as `DataType.ARRAY(DataType.STRING)`:
  <https://github.com/outline/outline/blob/main/server/models/ApiKey.ts>
- **Authentication middleware** — calls `apiKey.canAccess(ctx.originalUrl)`:
  <https://github.com/outline/outline/blob/main/server/middlewares/authentication.ts>
- **`apiKeys.create` handler** — normalises scopes on save:
  <https://github.com/outline/outline/blob/main/server/routes/api/apiKeys/apiKeys.ts>
- **`apiKeys.list` handler** — lists keys for authenticated user:
  <https://github.com/outline/outline/blob/main/server/routes/api/apiKeys/apiKeys.ts>
- **API key scopes feature** (issue + PR):
  <https://github.com/outline/outline/issues/8186>
  <https://github.com/outline/outline/pull/8297>

## Scope Storage Normalisation (apiKeys.create)

Before persisting, the server transforms each scope entry:

```typescript
scope?.map((s) =>
  s.startsWith("/api/") || s.includes(":")
    ? s                                // keep as-is
    : `/api/${s.replace(/^\\/, "")}`   // prepend /api/
)
```

- `"documents.list"` → `"/api/documents.list"` (route scope)
- `"auth.info"` → `"/api/auth.info"` (route scope)
- `"documents:read"` → `"documents:read"` (namespaced, kept as-is)
- `"read"` → `"/api/read"` (becomes broken route scope — see below)

## Scope Matching Algorithm (AuthenticationHelper.canAccess)

Given a request path and stored scopes, for each scope token:

1. Extract `resource` from path: `/api/documents.create` →
   `namespace = "documents"`, `method = "create"`
2. Parse scope format:

### Route scopes (start with `/api/`)

Stored as `/api/namespace.method`. Matched by exact namespace + method:

```
(namespace === scopeNamespace || scopeNamespace === "*") &&
(method === scopeMethod || scopeMethod === "*")
```

Examples: `/api/documents.list` matches only `documents.list`.

### Namespaced scopes (contain `:`)

Format `namespace:level` where level is `read`, `write`, or `create`.
Matched against the `methodToScope` mapping:

```
(namespace === scopeNamespace || scopeNamespace === "*") &&
(scopeMethod === "write" || methodToScope[method] === scopeMethod)
```

- `documents:read` → grants `documents.list`, `documents.info`,
  `documents.search`, `documents.export` (methods mapped to `read`)
- `documents:write` → grants ALL document endpoints (write matches
  everything)
- `documents:create` → grants only `documents.create`

### Global scopes (no `:` or `.`)

Parsed as `scopeNamespace = "*"`, `scopeMethod = scope`. Same matching
as namespaced but with wildcard namespace.

- `read` → all read methods across all namespaces
- `write` → all endpoints (write matches everything)

**Outline bug (v1.5.0)**: global scopes like `"read"` get `/api/`
prepended by the storage normalisation → stored as `"/api/read"` →
treated as a route scope for namespace `"read"` which matches nothing →
401 on every endpoint. Namespaced scopes (`documents:read`) are not
affected because the `:` bypasses the `/api/` prepend.

### methodToScope mapping

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

## Local Scope Matching Implementation

The `scope_matching.py` module implements the algorithm above in
Python.  `is_endpoint_accessible(endpoint, scopes)` checks a
single endpoint; `get_blocked_tools(scopes)` checks all tools
in `TOOL_ENDPOINT_MAP` and returns blocked tool names.
