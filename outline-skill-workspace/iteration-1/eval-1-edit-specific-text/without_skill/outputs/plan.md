# Plan: Edit "Tokens expire after 24 hours" to "Tokens expire after 72 hours"

## Step-by-step tool calls

1. **`get_document_id_from_title(query="API Reference")`**
   - Purpose: Look up the document ID for the document titled "API Reference".

2. **`read_document_section(document_id=<id from step 1>, heading="Authentication")`**
   - Purpose: Read the Authentication section to confirm it contains the exact text "Tokens expire after 24 hours" before making any edits.

3. **`edit_document(document_id=<id from step 1>, edits=[{"old_text": "Tokens expire after 24 hours", "new_text": "Tokens expire after 72 hours"}], save=true)`**
   - Purpose: Perform a find-and-replace of the specific text, changing "24 hours" to "72 hours", and save the document immediately.
