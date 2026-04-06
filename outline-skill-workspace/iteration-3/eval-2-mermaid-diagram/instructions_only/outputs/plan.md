# Plan: Add Mermaid Architecture Diagram to System Overview Document

## Step 1: Find the document

**Tool:** `get_document_id_from_title`
**Arguments:**
```json
{
  "query": "system overview"
}
```

**Purpose:** Locate the system overview document and retrieve its `document_id`.

## Step 2: Read the document to understand its structure

**Tool:** `get_document_toc`
**Arguments:**
```json
{
  "document_id": "<document_id from step 1>"
}
```

**Purpose:** See the heading structure so we know where to insert the diagram (e.g., after an "Architecture" section or at the end of the document).

## Step 3: Read the relevant section for insertion context

**Tool:** `read_document`
**Arguments:**
```json
{
  "document_id": "<document_id from step 1>"
}
```

**Purpose:** Read the full document (or a targeted section via `read_document_section` if the TOC reveals a clear insertion point like an "Architecture" heading) to identify the exact text surrounding where the diagram should go.

## Step 4: Insert the Mermaid diagram

**Tool:** `edit_document`
**Arguments:**
```json
{
  "document_id": "<document_id from step 1>",
  "edits": [
    {
      "old_string": "<text at the insertion point, e.g., the end of the Architecture section or a suitable location identified in steps 2-3>",
      "new_string": "<same text>\n\n## Architecture Diagram\n\nThe following diagram shows the request flow from the API Gateway through authentication to the backend services and database:\n\n```mermaidjs\nflowchart LR\n    Client([Client]) -->|HTTP Request| Gateway[API Gateway]\n    Gateway -->|Authenticate| Auth[Auth Service]\n    Auth -->|Token Valid| Gateway\n    Gateway -->|Forward Request| Backend[Backend Service]\n    Backend -->|Query / Write| DB[(Database)]\n    DB -->|Result| Backend\n    Backend -->|Response| Gateway\n    Gateway -->|HTTP Response| Client\n```\n"
    }
  ],
  "save": true
}
```

**Purpose:** Add the architecture diagram to the document. The `old_string` anchors the edit at the correct location; the `new_string` includes that same anchor text plus the new diagram section appended after it.

## Key Details

### Mermaid Diagram Code

```mermaidjs
flowchart LR
    Client([Client]) -->|HTTP Request| Gateway[API Gateway]
    Gateway -->|Authenticate| Auth[Auth Service]
    Auth -->|Token Valid| Gateway
    Gateway -->|Forward Request| Backend[Backend Service]
    Backend -->|Query / Write| DB[(Database)]
    DB -->|Result| Backend
    Backend -->|Response| Gateway
    Gateway -->|HTTP Response| Client
```

### Important Notes

- The code fence language is `mermaidjs` (not `mermaid`), as required by Outline's markdown renderer.
- The diagram uses `flowchart LR` (left-to-right) to show the request flow linearly.
- Node shapes convey meaning: `([...])` for the external client, `[...]` for services, `[(...)]` for the database.
- Edge labels describe the interaction at each step.
- All changes are batched into a single `edit_document` call with `save: true` so the document is updated atomically.

### Total MCP Tool Calls

| Order | Tool                      | Purpose                          |
|-------|---------------------------|----------------------------------|
| 1     | `get_document_id_from_title` | Find the system overview doc ID |
| 2     | `get_document_toc`         | Understand document structure    |
| 3     | `read_document`            | Get content around insertion point |
| 4     | `edit_document`            | Insert the Mermaid diagram       |
