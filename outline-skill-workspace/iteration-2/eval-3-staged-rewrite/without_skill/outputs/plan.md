# Recommended Approach: Staged Section-by-Section Rewrite

## Problem

Rewriting 5 sections of a long deployment guide in a single `update_document` call
is risky: if the call fails or the replacement text has issues, you could lose the
entire document or end up with a corrupted state. There is no built-in undo.

## Recommended Strategy

Use `edit_document` to make targeted, section-level edits rather than replacing the
entire document at once. This tool lets you pass multiple edits in a single call and
optionally defer saving, which gives you a review step before committing changes.

If `edit_document` is unavailable or unsuitable (e.g., you need full-text replacement),
fall back to `export_document` for a backup, then `update_document` for each section
change.

## Exact Tool Call Sequence

### Step 1: Find the document

```
get_document_id_from_title(query="deployment guide")
```

This returns the `document_id` you will use in every subsequent call.
Assume the returned ID is `DOC_ID` below.

### Step 2: Read the full document to understand its structure

```
read_document(document_id="DOC_ID")
```

If the document is very long and gets truncated, paginate:

```
read_document(document_id="DOC_ID", offset=0, limit=5000)
read_document(document_id="DOC_ID", offset=5000, limit=5000)
```

### Step 3: Get the table of contents to identify section headings

```
get_document_toc(document_id="DOC_ID")
```

This tells you the exact heading names for the 5 sections you need to rewrite.

### Step 4: Export a backup copy before making any changes

```
export_document(document_id="DOC_ID")
```

Save this output locally. If anything goes wrong, you can restore the document
content using `update_document` with the exported text.

### Step 5: Rewrite sections one at a time using edit_document

For each of the 5 sections, use `edit_document` with `save=false` first to preview,
then `save=true` to commit.

**Section 1 -- preview (do not save yet):**

```
edit_document(
  document_id="DOC_ID",
  edits=[
    {
      "old_text": "<exact text of section 1 you want to replace>",
      "new_text": "<your rewritten section 1 content>"
    }
  ],
  save=false
)
```

Review the result. If it looks correct, save:

```
save_document(document_id="DOC_ID")
```

**Section 2:**

```
edit_document(
  document_id="DOC_ID",
  edits=[
    {
      "old_text": "<exact text of section 2>",
      "new_text": "<rewritten section 2>"
    }
  ],
  save=false
)
```

Review, then:

```
save_document(document_id="DOC_ID")
```

Repeat this pattern for sections 3, 4, and 5.

### Step 6: Verify the final document

```
read_document(document_id="DOC_ID")
```

Read through the full document to confirm all 5 sections were rewritten correctly
and no surrounding content was damaged.

## Alternative: Batch all 5 edits in one call

If you are confident in all the replacements, you can batch them:

```
edit_document(
  document_id="DOC_ID",
  edits=[
    {"old_text": "<section 1 old>", "new_text": "<section 1 new>"},
    {"old_text": "<section 2 old>", "new_text": "<section 2 new>"},
    {"old_text": "<section 3 old>", "new_text": "<section 3 new>"},
    {"old_text": "<section 4 old>", "new_text": "<section 4 new>"},
    {"old_text": "<section 5 old>", "new_text": "<section 5 new>"}
  ],
  save=false
)
```

Review the combined result, then `save_document(document_id="DOC_ID")`.

## Alternative: read_document_section for targeted reading

If the document is very long and you only need to see specific sections before
rewriting, you can read individual sections:

```
read_document_section(document_id="DOC_ID", heading="Prerequisites")
read_document_section(document_id="DOC_ID", heading="Docker Setup")
```

This avoids loading the entire document when you only need specific parts.

## Why NOT use update_document for this

`update_document` replaces the entire document text. For a long document where you
are only changing 5 sections:

- You must reconstruct the full document text including unchanged sections
- A single mistake wipes out all content
- No preview step -- changes are immediate
- Higher risk of accidental data loss

`edit_document` with `save=false` is safer because it targets only the text you
want to change and lets you review before committing.

## Summary of key safety measures

1. **Export a backup first** with `export_document`
2. **Use `save=false`** to preview each edit before committing
3. **Edit one section at a time** to isolate failures
4. **Verify at the end** by reading the full document
5. **Keep the exported backup** until you are satisfied with all changes
