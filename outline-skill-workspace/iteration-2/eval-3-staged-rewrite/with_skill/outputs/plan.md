# Staged Rewrite Plan for a Large Deployment Guide

## The Problem

Rewriting 5 sections of a long document risks hitting API limits or losing
intermediate work if something fails partway through. Sending the entire
document body on every edit is wasteful and error-prone.

## Recommended Approach: Staged Edits with Deferred Save

The `edit_document` tool supports a `save=False` parameter that stages changes
in a server-side cache without writing them to Outline. You accumulate as many
edit batches as needed, then call `save_document` once at the end. This uses
exactly 1 API read and 1 API write, regardless of how many edit calls were
made.

## Step-by-Step Workflow

### 1. Find the document ID

```
search_documents(query="deployment guide")
```

or, if you know the exact title:

```
get_document_id_from_title(query="Deployment Guide")
```

This returns the document UUID (e.g. `abc123-def456`).

### 2. Get the table of contents

```
get_document_toc(doc_id="abc123-def456")
```

This returns the heading structure with line numbers. Use it to identify the
exact heading names of the 5 sections you need to rewrite. Reading the TOC
avoids loading the entire document into context.

### 3. Read each section you plan to rewrite

For each of the 5 sections, read just that section:

```
read_document_section(doc_id="abc123-def456", heading="Prerequisites")
read_document_section(doc_id="abc123-def456", heading="Installation")
read_document_section(doc_id="abc123-def456", heading="Configuration")
read_document_section(doc_id="abc123-def456", heading="Networking")
read_document_section(doc_id="abc123-def456", heading="Monitoring")
```

Replace the heading values with the actual section names from the TOC. Each
call returns only that section and its nested subsections, keeping context
usage low.

### 4. Stage edits for each section (save=False)

For each section, build an `edits` array of `old_string`/`new_string` pairs
and call `edit_document` with `save=False`. This stages the changes without
writing to Outline.

**Section 1:**
```
edit_document(
    doc_id="abc123-def456",
    edits=[
        {"old_string": "<exact text from Prerequisites>",
         "new_string": "<rewritten Prerequisites text>"}
    ],
    save=False
)
```

**Section 2:**
```
edit_document(
    doc_id="abc123-def456",
    edits=[
        {"old_string": "<exact text from Installation>",
         "new_string": "<rewritten Installation text>"}
    ],
    save=False
)
```

**Section 3:**
```
edit_document(
    doc_id="abc123-def456",
    edits=[
        {"old_string": "<exact text from Configuration>",
         "new_string": "<rewritten Configuration text>"}
    ],
    save=False
)
```

**Section 4:**
```
edit_document(
    doc_id="abc123-def456",
    edits=[
        {"old_string": "<exact text from Networking>",
         "new_string": "<rewritten Networking text>"}
    ],
    save=False
)
```

**Section 5:**
```
edit_document(
    doc_id="abc123-def456",
    edits=[
        {"old_string": "<exact text from Monitoring>",
         "new_string": "<rewritten Monitoring text>"}
    ],
    save=False
)
```

Each `old_string` must match exactly one location in the document. Include
enough surrounding context (a few lines) to ensure uniqueness.

You can also batch multiple replacements within a single section into one
`edits` array -- put all the `old_string`/`new_string` pairs for that section
together.

### 5. Save all changes at once

```
save_document(doc_id="abc123-def456")
```

This pushes every staged edit to Outline in a single API write. All 5 sections
are updated atomically.

## Why This Approach Works

| Concern                  | How staged edits address it              |
|--------------------------|------------------------------------------|
| Losing intermediate work | Changes accumulate in server-side cache; nothing is lost between edit calls |
| API rate limits          | Only 1 read + 1 write to Outline, no matter how many edit_document calls |
| Context window pressure  | read_document_section loads only the section you need, not the whole doc |
| Atomicity                | All changes land in one save, so the document is never in a half-updated state |
| Error recovery           | If an edit_document call fails, previously staged edits are still intact; fix and retry the failed batch |

## Key Parameter Reference

| Tool                    | Parameter   | Value / Purpose                              |
|-------------------------|-------------|----------------------------------------------|
| `search_documents`      | `query`     | Keywords to find the document                |
| `get_document_id_from_title` | `query` | Exact document title                        |
| `get_document_toc`      | `doc_id`    | Document UUID                                |
| `read_document_section` | `doc_id`    | Document UUID                                |
| `read_document_section` | `heading`   | Case-insensitive substring of a heading      |
| `edit_document`         | `doc_id`    | Document UUID                                |
| `edit_document`         | `edits`     | Array of `{old_string, new_string}` pairs    |
| `edit_document`         | `save`      | `False` to stage without writing to Outline  |
| `save_document`         | `doc_id`    | Document UUID; pushes all staged edits       |

## Summary

The complete call sequence is:

1. `search_documents(query="deployment guide")` -- get the doc ID
2. `get_document_toc(doc_id=...)` -- understand the structure
3. `read_document_section(doc_id=..., heading="...")` -- x5, one per section
4. `edit_document(doc_id=..., edits=[...], save=False)` -- x5, staged
5. `save_document(doc_id=...)` -- single atomic write

Total Outline API calls: 1 read + 1 write (the edit_document staging calls
operate on the server-side cache, not the Outline API directly).
