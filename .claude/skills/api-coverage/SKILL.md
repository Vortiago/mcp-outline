---
name: api-coverage
description: Scan all registered tools for their meta.endpoint values and report which Outline API endpoints are covered vs missing
---

# API Coverage Audit

Scan all MCP tools and report which Outline API endpoints are covered.

## Steps

1. Search all tool files for `meta=` declarations containing `"endpoint"`:

```
Grep for "endpoint" in src/mcp_outline/features/documents/*.py
```

2. Extract all unique endpoint values (e.g., `documents.search`, `collections.list`).

3. Group covered endpoints by namespace (documents, collections, comments, attachments, etc.).

4. Cross-reference against known Outline API endpoints:

**Documents**: documents.search, documents.list, documents.info, documents.create, documents.update, documents.delete, documents.archive, documents.unarchive, documents.restore, documents.move, documents.star, documents.unstar, documents.export, documents.import, documents.drafts, documents.viewed, documents.templatize, documents.unpublish, documents.add_user, documents.remove_user

**Collections**: collections.list, collections.info, collections.documents, collections.create, collections.update, collections.delete, collections.export, collections.export_all, collections.add_user, collections.remove_user, collections.memberships, collections.add_group, collections.remove_group, collections.group_memberships

**Comments**: comments.list, comments.create, comments.update, comments.delete

**Attachments**: attachments.redirect, attachments.create, attachments.delete

**Other**: views.list, views.create, shares.list, shares.create, shares.update, shares.revoke, stars.list, stars.create, stars.delete, users.list, users.info, groups.list, groups.info, events.list, searches.list, searches.delete, fileOperations.list, fileOperations.info, fileOperations.redirect

5. Also note which tools are conditionally registered:
   - Gated by `OUTLINE_READ_ONLY` (content, lifecycle, organization, batch_operations modules)
   - Gated by `OUTLINE_DISABLE_DELETE` (delete tools in document_lifecycle and collection_tools)
   - Gated by `OUTLINE_DISABLE_AI_TOOLS` (ai_tools module)

## Output Format

```
Outline API Coverage Report

Covered Endpoints (X total):
  documents: search, list, info, create, update, ...
  collections: list, documents, create, ...
  comments: list, create
  attachments: redirect

Missing Endpoints (Y total):
  documents: star, unstar, export, import, ...
  collections: add_user, remove_user, ...
  comments: update, delete
  ...

Conditionally Registered:
  Read-only gated: documents.create, documents.update, ...
  Delete gated: documents.delete, collections.delete
  AI gated: documents.answer

Coverage: X / (X+Y) = Z%
```
