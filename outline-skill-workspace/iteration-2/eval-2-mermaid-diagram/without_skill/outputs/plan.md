# Plan: Add Mermaid Architecture Diagram to System Overview Doc

## Step-by-step tool calls

1. **Find the document ID for the system overview doc**

   Call `get_document_id_from_title(query="system overview")`

   This searches Outline for a document matching "system overview" and returns its document ID. Without knowing the exact title or ID, this is the necessary first step.

2. **Read the current document content**

   Call `read_document(document_id="<id from step 1>")`

   Read the full document so we can see its current structure and decide where to place the diagram (e.g., after an introduction section or before a components section).

3. **Update the document by appending the Mermaid diagram**

   Call `update_document(document_id="<id from step 1>", text="<full document with diagram inserted>")` or, if appending to the end is acceptable, call `update_document(document_id="<id from step 1>", append=true, text="<diagram section below>")`.

   The Mermaid diagram content to add:

   ~~~markdown
   ## Architecture Diagram

   ```mermaid
   graph LR
       Client([Client]) -->|HTTP Request| APIGateway[API Gateway]
       APIGateway -->|Authenticate| AuthService[Auth Service]
       AuthService -->|Token Valid| APIGateway
       APIGateway -->|Forward Request| Backend[Backend Service]
       Backend -->|Query/Write| Database[(Database)]
       Database -->|Result| Backend
       Backend -->|Response| APIGateway
       APIGateway -->|HTTP Response| Client
   ```
   ~~~

## Notes

- If the document title is not an exact match, `get_document_id_from_title` may return multiple results or a wrong match. I would need to verify the returned ID is correct before proceeding.
- If the diagram should be inserted at a specific location within the document rather than appended, I would need to use `update_document` with the full `text` parameter containing the entire document content with the diagram placed at the desired position, since there is no insert-at-position tool available.
- The `append=true` option on `update_document` is the simplest approach if adding to the end of the document is acceptable.
- There is no preview or dry-run capability, so the update is immediate.
