# Plan: Batch-Edit the Onboarding Guide in Outline

## Step 1 -- Find the document ID

Call `search_documents` to locate the onboarding guide:

```
search_documents(query="onboarding guide")
```

This returns a list of matching documents with their UUIDs. Identify the correct one from the results (e.g. `doc_id = "<UUID>"`).

## Step 2 -- Read the table of contents

Call `get_document_toc` to understand the document structure without loading the full content:

```
get_document_toc(doc_id="<UUID>")
```

This returns all headings with line numbers so we can identify the sections that contain the Slack channel reference, VPN setup instructions, and laptop ordering information.

## Step 3 -- Read the relevant sections

Read the three sections that need changes. These can be called in parallel since they are independent:

```
read_document_section(doc_id="<UUID>", heading="Slack")
read_document_section(doc_id="<UUID>", heading="VPN")
read_document_section(doc_id="<UUID>", heading="laptop")
```

The exact heading substrings depend on what the TOC returned in Step 2. The `heading` parameter is a case-insensitive substring match, so partial names work. Reading each section gives us the exact text needed to construct precise `old_string` values for the edit.

## Step 4 -- Apply all three edits in a single call

Call `edit_document` with all three changes batched into one `edits` array:

```
edit_document(
    doc_id="<UUID>",
    edits=[
        {
            "old_string": "#new-hires",
            "new_string": "#onboarding-2026"
        },
        {
            "old_string": "<exact text referencing OpenVPN guide>",
            "new_string": "<replacement text referencing the new Cloudflare Access portal>"
        },
        {
            "old_string": "<exact text from the laptop ordering section>",
            "new_string": "<updated text mentioning the new M4 MacBook Pro option>"
        }
    ]
)
```

All edits are sent in a single `edit_document` call because the skill guide says to "batch all edits for a document into one call when possible." Each `old_string` must match exactly one location in the document; we include enough surrounding context (read in Step 3) to ensure uniqueness.

## Why this approach

- **Steps 1-2** locate the document and understand its structure without loading the full body, saving context tokens as recommended by the skill guide for large documents.
- **Step 3** reads only the sections we need so we can grab the exact text for precise find-and-replace matching.
- **Step 4** uses `edit_document` with a single batched call. This is the correct tool for targeted changes (not `update_document`, which is for full-content replacement or appends). Because all three edits fit in one call, this requires only 1 API read and 1 API write on the server side.
- If the document were so large that the edits could not fit in a single call, we would use the staged-edit pattern: `edit_document(..., save=False)` for each batch, then `save_document(doc_id)` once at the end.

## Total tool calls

| # | Tool | Purpose |
|---|------|---------|
| 1 | `search_documents` | Find the document UUID |
| 2 | `get_document_toc` | Get heading structure and line numbers |
| 3-5 | `read_document_section` (x3, parallel) | Read Slack, VPN, and laptop sections |
| 6 | `edit_document` | Apply all three edits in one batch |
