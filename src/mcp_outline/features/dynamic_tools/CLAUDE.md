# Dynamic Tool List — Outline Scope Reference

How Outline checks API key scopes against request endpoints.

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

## `auth.info` and Scope Detection

- `auth.info` does NOT return the API key's scope in its response —
  the `data.apiKey` field is absent.
- To detect whether a key has write access, probe a write endpoint
  (e.g. `documents.create`) and check for 401.

## Probing: 401 vs 403

- **401** (`authentication_required`): the API key's scope does not
  include this endpoint.  The authentication middleware rejects the
  request *before* the route handler runs.  This is what probing
  detects.
- **403** (`authorization_error`): the key is authenticated and
  in-scope, but the specific resource is inaccessible (e.g. the
  probed UUID doesn't match a real document).  Outline returns 403
  instead of 404 for non-existent resources to avoid leaking
  existence information.  Probing must **not** treat 403 as blocked.
