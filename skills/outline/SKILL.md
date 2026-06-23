---
name: outline
description: Conventions and efficient workflows for Outline knowledge bases via mcp-outline tools. Use when creating, editing, restructuring, or diagramming Outline documents — covers Outline markdown quirks (mermaidjs code fences), document and collection structure, string-match editing, staged rewrites, batch operations, and search status filters.
---

# Working with Outline

## Markdown

- **Mermaid diagrams need ` ```mermaidjs ` fences, NOT ` ```mermaid `**
  — the wrong fence silently renders as a plain code block.
- Otherwise standard markdown. Use ATX headings (`#`–`######`); they
  power the TOC and section tools.

## Structure

- Collections contain documents; documents nest via
  `parent_document_id`. Browse: `list_collections`,
  `get_collection_structure`.
- Lifecycle: draft → published → archived → trash (30-day recovery
  via `restore_document`; `delete_document(permanent=True)` is
  unrecoverable).
- `create_document(template=True)` / `update_document(template=True)`
  adds to the "New from template" picker.
- Titles are not unique; resolve to IDs with
  `get_document_id_from_title` or `search_documents`. Check
  `get_document_backlinks` before restructuring or deleting.

## Search defaults to published only

Drafts and archived docs are invisible to `search_documents` and
`list_recently_updated_documents` unless widened:
`status_filter=["draft", "published", "archived"]`.

## Reading large documents

1. `get_document_toc` — headings with 0-based line numbers.
2. `read_document_section(heading=...)` — case-insensitive substring;
   accepts headings as the TOC prints them (e.g. `"## Background"`).
3. `search_document_content(query=...)` — grep within the document:
   matching lines with line numbers and context. Use it to locate
   text for `edit_document` old_strings or `read_document` offsets.
4. `read_document(offset=N, limit=M)` — TOC/grep line numbers are
   valid offsets.

Full `read_document` only for small documents.

## Editing

- Default to `edit_document`: each `old_string` must match exactly
  once (add surrounding context to disambiguate); edits apply
  sequentially, all-or-nothing. Batch all edits for one document into
  a single call.
- `update_document` only for full replacement, title changes, or
  `append=True` (sends just the chunk).

### Staged rewrites

```
edit_document(id, edits=[...], save=False)   # stage, repeat as needed
edit_document(id, edits=[...], save=True)    # final batch + push all
edit_document(id, edits=[], save=True)       # or: flush only
```

One API write total. Staged changes are server-memory only — flush
before ending; a restart discards them. Read tools show staged text
with an "unsaved changes" notice; `export_document` bypasses staging
and returns the last saved content.

## Many documents

Use `batch_create_documents`, `batch_update_documents`,
`batch_move_documents`, `batch_archive_documents`,
`batch_delete_documents` (10–50 per call; per-document results)
instead of loops.

## Missing tools

Deployments may be read-only, delete-disabled, or scope-filtered.
Use what's listed; if an editing tool is absent, say so.

## Exploration

For broad search-and-summarize, delegate to the `outline-explorer`
agent (bundled with this plugin).
