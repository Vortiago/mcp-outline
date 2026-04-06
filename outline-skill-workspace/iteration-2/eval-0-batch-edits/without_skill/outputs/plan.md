# Plan: Batch Edits to Onboarding Guide

## Step-by-step tool calls

1. **Find the document ID for the onboarding guide**

   Call `get_document_id_from_title` with:
   - `query`: `"onboarding guide"`

   This returns the document ID needed for all subsequent calls.

2. **Read the full document to understand its structure and locate the sections that need changes**

   Call `read_document` with:
   - `document_id`: (the ID returned from step 1)

   Since the document is described as "huge," the response may be truncated. If so, follow up with additional `read_document` calls using `offset` to paginate through the content until all three target sections are found:
   - The Slack channel reference (`#new-hires`)
   - The VPN setup instructions (OpenVPN references)
   - The laptop ordering section

3. **Update the document with all three changes in a single call**

   Call `update_document` with:
   - `document_id`: (the ID from step 1)
   - `text`: (the full updated markdown content with all three changes applied)

   The three changes embedded in the new text:
   - Replace `#new-hires` with `#onboarding-2026`
   - Replace OpenVPN setup instructions with Cloudflare Access portal references
   - Add/update the laptop ordering section to mention the M4 MacBook Pro option

4. **Read back the document to verify the changes were applied correctly**

   Call `read_document` with:
   - `document_id`: (the ID from step 1)

   Scan the output to confirm all three changes are present.

## Notes

- Step 2 may require multiple paginated reads if the document is large, using increasing `offset` values.
- Step 3 replaces the entire document text, which is risky for a large document -- any content not included in the replacement would be lost. However, without a targeted find-and-replace tool, `update_document` with the full `text` parameter is the only available option for making inline changes.
- An alternative approach would be to use `update_document` with `append=true` to add content, but that only appends and cannot modify existing text in-place, so it does not work for the Slack channel rename or the VPN instruction replacement.
