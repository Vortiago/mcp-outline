# Plan: Edit 'Tokens expire after 24 hours' to '72 hours' in API Reference

Following the skill's "Edit specific content" workflow:

## Step 1: Find the document ID

**Tool:** `get_document_id_from_title`
**Arguments:**
```json
{
  "query": "API Reference"
}
```

**Why:** The user gave us the exact document title, so `get_document_id_from_title` is the most direct way to resolve the ID. No need for a broader keyword search.

## Step 2: Read the Authentication section to confirm the text

**Tool:** `read_document_section`
**Arguments:**
```json
{
  "doc_id": "<document_id from step 1>",
  "heading": "Authentication"
}
```

**Why:** Before editing, we should verify the exact text that exists in the document. The skill recommends reading the relevant section first (TOC/section approach) rather than loading the full document. This confirms the precise string we need to replace.

## Step 3: Apply the edit

**Tool:** `edit_document`
**Arguments:**
```json
{
  "doc_id": "<document_id from step 1>",
  "edits": [
    {
      "old_string": "Tokens expire after 24 hours",
      "new_string": "Tokens expire after 72 hours"
    }
  ]
}
```

**Why:** The skill recommends `edit_document` over `update_document` for changing specific text passages. It operates server-side, applies the replacement, and saves in one call. Since this is a single small edit, there is no need to stage changes with `save=False`.

## Summary

Three tool calls total, executed sequentially since each depends on the prior result. The workflow matches the skill's documented "Edit specific content" pattern exactly.
