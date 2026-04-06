# Staged Rewrite Plan for a Large Deployment Guide

## Recommended Approach: Staged Edits with Deferred Save

For a massive rewrite of 5 sections in a long document, the best approach is to use
`edit_document` with `save=False` for each section, staging all changes without
writing to the server on every call. Once all 5 sections are rewritten, call
`save_document` once to persist everything. This avoids partial saves, reduces API
calls, and ensures you do not lose work from an intermediate failure — either all
changes land or none do.

## Step-by-Step Tool Call Sequence

### Step 1: Find the document ID

```
get_document_id_from_title(query="deployment guide")
```

This returns the document ID needed for all subsequent calls. If you know the
collection, add `collection_id` to narrow results.

### Step 2: Get the table of contents to identify the 5 target sections

```
get_document_toc(document_id="<doc_id>")
```

This returns the heading structure so you can identify exact heading names for
the sections you need to rewrite.

### Step 3: Read each section you plan to rewrite

For each of the 5 sections, read its current content so you have the exact
`old_string` text needed for edits:

```
read_document_section(document_id="<doc_id>", heading="Section 1 Heading")
read_document_section(document_id="<doc_id>", heading="Section 2 Heading")
read_document_section(document_id="<doc_id>", heading="Section 3 Heading")
read_document_section(document_id="<doc_id>", heading="Section 4 Heading")
read_document_section(document_id="<doc_id>", heading="Section 5 Heading")
```

### Step 4: Stage edits for each section WITHOUT saving

Make one `edit_document` call per section with `save=False`. Each call can contain
multiple edits within that section if needed. The key parameter is `save=False`,
which stages the changes in memory without persisting them.

**Section 1:**
```
edit_document(
    document_id="<doc_id>",
    edits=[
        {"old_string": "<exact text from section 1>", "new_string": "<rewritten text>"}
    ],
    save=False
)
```

**Section 2:**
```
edit_document(
    document_id="<doc_id>",
    edits=[
        {"old_string": "<exact text from section 2>", "new_string": "<rewritten text>"}
    ],
    save=False
)
```

**Section 3:**
```
edit_document(
    document_id="<doc_id>",
    edits=[
        {"old_string": "<exact text from section 3>", "new_string": "<rewritten text>"}
    ],
    save=False
)
```

**Section 4:**
```
edit_document(
    document_id="<doc_id>",
    edits=[
        {"old_string": "<exact text from section 4>", "new_string": "<rewritten text>"}
    ],
    save=False
)
```

**Section 5:**
```
edit_document(
    document_id="<doc_id>",
    edits=[
        {"old_string": "<exact text from section 5>", "new_string": "<rewritten text>"}
    ],
    save=False
)
```

### Step 5: Save all staged changes at once

```
save_document(document_id="<doc_id>")
```

This single call persists all 5 section rewrites to Outline in one operation.

## Why This Approach Works

1. **Atomic commit**: All 5 sections are saved together. You avoid a half-rewritten
   document if something fails midway.
2. **Accurate matching**: `read_document_section` gives you the exact current text
   for each heading, so `old_string` values will match precisely.
3. **Handles large documents**: By reading section-by-section instead of loading the
   entire document, you stay within output limits for very long docs.
4. **Batching within sections**: If a single section needs multiple distinct edits
   (e.g., changing a paragraph and a code block), you can pass multiple objects in
   the `edits` array of one `edit_document` call.
5. **Minimal API writes**: Only one write operation hits the Outline API (the final
   `save_document`), reducing the chance of rate limiting or conflicts.

## Summary of Calls

| Order | Tool                    | Key Parameters                          | Purpose                        |
|-------|-------------------------|-----------------------------------------|--------------------------------|
| 1     | get_document_id_from_title | query="deployment guide"             | Find the document ID           |
| 2     | get_document_toc        | document_id                             | Map the heading structure      |
| 3-7   | read_document_section   | document_id, heading (one per section)  | Get exact text for each section|
| 8-12  | edit_document           | document_id, edits=[...], save=False    | Stage rewrites without saving  |
| 13    | save_document           | document_id                             | Persist all changes at once    |
