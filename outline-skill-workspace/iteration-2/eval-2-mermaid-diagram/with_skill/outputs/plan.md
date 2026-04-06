# Plan: Add Mermaid Architecture Diagram to System Overview Doc

## Step-by-step MCP Tool Calls

### 1. Find the document ID for the system overview doc

**Tool:** `search_documents`
**Arguments:**
```json
{
  "query": "system overview"
}
```

This returns a list of matching documents with their IDs. Identify the correct document from the results (e.g., document ID `abc123-def4-5678-ghij-klmnopqrstuv`).

### 2. Get the table of contents to understand document structure

**Tool:** `get_document_toc`
**Arguments:**
```json
{
  "doc_id": "<document_id from step 1>"
}
```

This reveals the heading structure and line numbers so we know where to insert the diagram. We look for an appropriate section such as "Architecture", "System Design", or the end of the document.

### 3. Read the target section to see existing content

**Tool:** `read_document_section`
**Arguments:**
```json
{
  "doc_id": "<document_id from step 1>",
  "heading": "architecture"
}
```

If no architecture section exists, read the full document (or the section closest to where the diagram should go) to find the exact text surrounding the insertion point.

### 4. Insert the Mermaid diagram using edit_document

**Tool:** `edit_document`
**Arguments:**
```json
{
  "doc_id": "<document_id from step 1>",
  "edits": [
    {
      "old_string": "<text at the insertion point, e.g. the end of the architecture section or a heading we want to insert after>",
      "new_string": "<same text>\n\n## Architecture Diagram\n\nThe following diagram shows the request flow from the API Gateway through authentication to the backend services and database:\n\n```mermaidjs\ngraph LR\n    Client([Client]) -->|HTTP Request| APIGateway[API Gateway]\n    APIGateway -->|Authenticate| AuthService[Auth Service]\n    AuthService -->|Token Valid| APIGateway\n    APIGateway -->|Authorized Request| Backend[Backend Service]\n    Backend -->|Query / Write| Database[(Database)]\n    Database -->|Result| Backend\n    Backend -->|Response| APIGateway\n    APIGateway -->|HTTP Response| Client\n```\n"
    }
  ]
}
```

## Key Detail: Mermaid Code Fence Language

Outline uses `` ```mermaidjs `` (not `` ```mermaid ``). This is called out in the skill file under "Markdown Notes" and is critical for the diagram to render correctly.

## Full Mermaid Diagram Code

```mermaidjs
graph LR
    Client([Client]) -->|HTTP Request| APIGateway[API Gateway]
    APIGateway -->|Authenticate| AuthService[Auth Service]
    AuthService -->|Token Valid| APIGateway
    APIGateway -->|Authorized Request| Backend[Backend Service]
    Backend -->|Query / Write| Database[(Database)]
    Database -->|Result| Backend
    Backend -->|Response| APIGateway
    APIGateway -->|HTTP Response| Client
```

## Summary

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `search_documents` | Find the system overview document ID |
| 2 | `get_document_toc` | Understand the document's heading structure |
| 3 | `read_document_section` | Read the target section to get exact text for the edit |
| 4 | `edit_document` | Insert the Mermaid diagram at the right location |

Total API calls: 4 (1 search + 1 TOC + 1 section read + 1 edit). All edits are batched into a single `edit_document` call.
