# Plan: Batch-Edit the Onboarding Guide in Outline

## Step 1 -- Find the document ID

Call `get_document_id_from_title` to locate the onboarding guide:

```
get_document_id_from_title(query="onboarding guide")
```

This returns the document ID (UUID) needed for all subsequent calls.

## Step 2 -- Get the document structure

Since the document is described as huge, use `get_document_toc` to see the heading structure before reading content:

```
get_document_toc(document_id="<UUID>")
```

This returns headings so we can identify exactly which sections contain the Slack channel reference, VPN setup instructions, and laptop ordering information.

## Step 3 -- Read the relevant sections

Read the three sections that need changes. These calls are independent and can run in parallel:

```
read_document_section(document_id="<UUID>", heading="Slack")
read_document_section(document_id="<UUID>", heading="VPN")
read_document_section(document_id="<UUID>", heading="laptop")
```

The exact `heading` values depend on what the TOC returned in Step 2 -- use the actual heading text or a substring that matches. Reading each section gives us the exact text needed to construct precise `old_string` values for the edits.

## Step 4 -- Apply all three edits in a single call

Call `edit_document` with all three changes batched into one `edits` array:

```
edit_document(
    document_id="<UUID>",
    edits=[
        {
            "old_string": "#new-hires",
            "new_string": "#onboarding-2026"
        },
        {
            "old_string": "<exact text referencing the old OpenVPN guide>",
            "new_string": "<replacement text referencing the new Cloudflare Access portal>"
        },
        {
            "old_string": "<exact text from the laptop ordering section>",
            "new_string": "<updated text mentioning the new M4 MacBook Pro option>"
        }
    ],
    save=True
)
```

All three edits are sent in a single `edit_document` call. Each `old_string` must be an exact match of text found in the document (copied from the section reads in Step 3), with enough surrounding context to ensure uniqueness. The `new_string` fields contain the replacement text with the updated information.

## Step 5 -- Verify the changes

Read back the modified sections to confirm the edits were applied correctly:

```
read_document_section(document_id="<UUID>", heading="Slack")
read_document_section(document_id="<UUID>", heading="VPN")
read_document_section(document_id="<UUID>", heading="laptop")
```

## Why this approach

- **Step 1** locates the document by title without needing to know its UUID upfront.
- **Step 2** uses the TOC to understand structure without loading the entire huge document.
- **Step 3** reads only the sections we need, giving us exact text for find-and-replace matching.
- **Step 4** uses `edit_document` (not `update_document`) for targeted changes. All three edits are batched into one call since the server instructions say to "batch all changes into one call when possible."
- If the document were so large that edits couldn't fit in a single call, we would use `edit_document(..., save=False)` for each batch, then `save_document(document_id)` once at the end.

## Total tool calls

| # | Tool | Purpose |
|---|------|---------|
| 1 | `get_document_id_from_title` | Find the document UUID |
| 2 | `get_document_toc` | Get heading structure |
| 3-5 | `read_document_section` (x3, parallel) | Read Slack, VPN, and laptop sections |
| 6 | `edit_document` | Apply all three edits in one batch |
| 7-9 | `read_document_section` (x3, parallel) | Verify changes |
