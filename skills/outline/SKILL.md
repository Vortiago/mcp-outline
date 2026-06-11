---
name: outline
description: Conventions and efficient workflows for Outline knowledge bases via mcp-outline tools. Use when creating, editing, restructuring, or diagramming Outline documents — covers Outline markdown quirks (mermaidjs code fences), document and collection structure, string-match editing, staged rewrites, batch operations, and search status filters.
---

# Working with Outline

Outline is a wiki/knowledge base. The mcp-outline tools map onto its
REST API. This skill covers the conventions and intricacies that are
not obvious from the tool descriptions alone.

## Outline-specific markdown

- **Mermaid diagrams need `mermaidjs` fences.** Use ` ```mermaidjs `,
  NOT ` ```mermaid `. With the wrong fence the diagram silently
  renders as a plain code block.
- Everything else is standard markdown. ATX headings (`#` through
  `######`) power the TOC and section tools — prefer them over bold
  text as pseudo-headings.

## How content is structured

- **Collections** (name, description, color) contain **documents**;
  documents nest under a `parent_document_id` to form trees. Browse
  with `list_collections` and `get_collection_structure`.
- **Lifecycle**: draft → published → archived → trash. Trashed
  documents are recoverable for 30 days (`restore_document`);
  `delete_document(permanent=True)` skips the trash and is
  unrecoverable.
- **Templates**: `create_document(template=True)` or
  `update_document(template=True)` makes a document appear in
  Outline's "New from template" picker.
- **Backlinks**: `get_document_backlinks` finds documents linking to
  a given one — useful before restructuring or deleting.
- Documents are addressed by ID, and titles are not unique. Resolve
  titles with `get_document_id_from_title` or `search_documents`.

## Search returns only published documents by default

`search_documents` defaults to `status_filter=["published"]`. Drafts
and archived documents are invisible unless you widen it:

```
search_documents(query="...", status_filter=["draft", "published", "archived"])
```

For thorough searches across a whole workspace, always consider
whether drafts and archived content matter.

## Reading large documents without wasting context

1. `get_document_toc(document_id)` — heading structure with 0-based
   line numbers.
2. `read_document_section(document_id, heading=...)` — one section
   including nested subsections. The heading argument is a
   case-insensitive substring and accepts headings exactly as the
   TOC prints them (e.g. `"## Background"`).
3. `read_document(document_id, offset=N, limit=M)` — line ranges;
   TOC line numbers are valid offsets.

Only call `read_document` without parameters when you genuinely need
the entire document and it is small.

## Editing documents

- **`edit_document` is the default editing tool.** Each edit's
  `old_string` must match exactly one location — include surrounding
  context to disambiguate. Edits apply sequentially (a later edit may
  target text created by an earlier one) and all-or-nothing: if any
  edit fails, nothing is written.
- Batch all edits to one document into a single call.
- Use `update_document` only for full content replacement (sends the
  whole text), title changes, or appending (`append=True` sends just
  the new chunk).

### Staged rewrites (large multi-step edits)

For rewrites spanning several calls, stage with `save=False` and push
once at the end:

```
edit_document(id, edits=[...], save=False)   # stage section 1
edit_document(id, edits=[...], save=False)   # stage section 2
edit_document(id, edits=[...], save=True)    # final batch + push all
edit_document(id, edits=[], save=True)       # or: flush with no new edits
```

This costs one API write regardless of how many staging calls you
make. Staged changes live in server memory only: flush before the
session ends (a server restart discards them). `read_document`,
`get_document_toc`, and `read_document_section` show staged text and
append a "staged unsaved changes" notice while edits are pending;
`export_document` bypasses staging and always returns the last saved
server-side content.

## Multi-document operations

Prefer the batch tools over loops of single calls:
`batch_create_documents`, `batch_update_documents`,
`batch_move_documents`, `batch_archive_documents`,
`batch_delete_documents`. Recommended batch size is 10–50; results
report per-document success/failure.

## Tools may be missing — adapt

Deployments can run read-only (`OUTLINE_READ_ONLY`), with deletes
disabled, or with per-user scoped API keys that filter the tool list.
Work with the tools actually present; if an editing tool is absent,
report that instead of trying alternatives.

## Delegating exploration

For broad search-and-summarize work across the wiki, delegate to the
`outline-explorer` agent (bundled with this plugin) instead of doing
many searches in the main conversation.
