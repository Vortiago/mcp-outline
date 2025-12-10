# Structured Output Reference

This document describes the `structuredContent` returned by each MCP tool in mcp-outline.

## Overview

All tools return a `CallToolResult` with two components:
- **`content[0].text`**: Human-readable formatted text for display
- **`structuredContent`**: Machine-parseable JSON for programmatic access

This dual-output approach follows the [MCP 2025-06-18 specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) for backwards compatibility while enabling structured data consumption.

## Configuration

Structured output is **disabled by default**. To enable it:

```bash
OUTLINE_STRUCTURED_OUTPUT=true
```

When disabled (the default), `structuredContent` will be `null` in all responses. The `content[0].text` field always contains the human-readable response.

## Common Patterns

### Success Responses
All successful responses include relevant IDs and metadata. The exact fields vary by tool category.

### Error Responses
All error responses follow this pattern:
```json
{
  "error": "Error message string",
  "document_id": "id-if-applicable",
  "collection_id": "id-if-applicable"
}
```

---

## Tools by Category

### Search & Discovery

#### `search_documents`
```json
{
  "results": [
    {
      "document_id": "doc-uuid",
      "title": "Document Title",
      "collection_id": "col-uuid",
      "context": "...matching text..."
    }
  ],
  "total": 42,
  "query": "search terms",
  "detail_level": "summary"
}
```

#### `list_collections`
```json
{
  "collections": [
    {
      "id": "col-uuid",
      "name": "Collection Name",
      "description": "Description text",
      "document_count": 15
    }
  ],
  "count": 5
}
```

#### `get_collection_structure`
```json
{
  "collection_id": "col-uuid",
  "collection_name": "Collection Name",
  "documents": [
    {
      "id": "doc-uuid",
      "title": "Document Title",
      "children": [...]
    }
  ],
  "total_documents": 25,
  "max_depth": -1
}
```

#### `get_document_id_from_title`
```json
{
  "results": [
    {
      "document_id": "doc-uuid",
      "title": "Exact or Similar Title",
      "collection_id": "col-uuid"
    }
  ],
  "query": "search title",
  "count": 3
}
```

---

### Document Reading

#### `read_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "text": "Full markdown content..."
}
```

#### `export_document`
```json
{
  "document_id": "doc-uuid",
  "content": "Raw markdown export...",
  "format": "markdown"
}
```

#### `get_document_outline`
For large documents (≥1000 chars):
```json
{
  "title": "Document Title",
  "headings": [
    {"level": 1, "text": "Introduction", "line": 1},
    {"level": 2, "text": "Overview", "line": 5}
  ],
  "word_count": 2500,
  "document_id": "doc-uuid"
}
```

For small documents (<1000 chars), returns full content:
```json
{
  "title": "Document Title",
  "full_content": true,
  "text": "Full document text...",
  "document_id": "doc-uuid"
}
```

#### `read_document_section`
Success:
```json
{
  "heading": "Section Name",
  "content": "Section content text...",
  "document_id": "doc-uuid"
}
```

Heading not found:
```json
{
  "error": "heading_not_found",
  "available_headings": ["Intro", "Setup", "Usage"],
  "document_id": "doc-uuid"
}
```

---

### Document Management

#### `create_document`
```json
{
  "document_id": "new-doc-uuid",
  "title": "New Document",
  "collection_id": "col-uuid",
  "url": "https://outline.example.com/doc/...",
  "published": true
}
```

#### `update_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Updated Title",
  "url": "https://outline.example.com/doc/...",
  "appended": false
}
```

#### `move_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "new_collection_id": "target-col-uuid",
  "new_parent_id": "parent-doc-uuid"
}
```
Note: `new_collection_id` and `new_parent_id` only present if specified in the request.

---

### Document Lifecycle

#### `archive_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "status": "archived"
}
```

#### `unarchive_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "status": "active"
}
```

#### `delete_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "status": "deleted",
  "permanent": false
}
```

#### `restore_document`
```json
{
  "document_id": "doc-uuid",
  "title": "Document Title",
  "status": "restored"
}
```

#### `list_archived_documents`
```json
{
  "documents": [
    {
      "document_id": "doc-uuid",
      "title": "Archived Doc",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 5
}
```

#### `list_trash`
```json
{
  "documents": [
    {
      "document_id": "doc-uuid",
      "title": "Deleted Doc",
      "deleted_at": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 3
}
```

---

### Comments & Collaboration

#### `add_comment`
```json
{
  "comment_id": "comment-uuid",
  "document_id": "doc-uuid",
  "created_at": "2025-01-15T10:30:00Z",
  "is_reply": false,
  "parent_comment_id": "parent-uuid"
}
```
Note: `parent_comment_id` only present for replies.

#### `list_document_comments`
```json
{
  "comments": [...],
  "document_id": "doc-uuid",
  "total": 15,
  "limit": 25,
  "offset": 0
}
```

#### `get_comment`
```json
{
  "comment": {...},
  "comment_id": "comment-uuid"
}
```

#### `get_document_backlinks`
```json
{
  "backlinks": [
    {
      "document_id": "linking-doc-uuid",
      "title": "Linking Document",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "document_id": "target-doc-uuid",
  "count": 3
}
```

---

### Collection Management

#### `create_collection`
```json
{
  "collection_id": "new-col-uuid",
  "name": "New Collection"
}
```

#### `update_collection`
```json
{
  "collection_id": "col-uuid",
  "name": "Updated Name"
}
```

#### `delete_collection`
```json
{
  "collection_id": "col-uuid",
  "deleted": true
}
```

#### `export_collection`
```json
{
  "file_operation": {
    "id": "op-uuid",
    "state": "complete",
    "type": "export",
    "name": "collection-export.zip"
  },
  "collection_id": "col-uuid",
  "format": "outline-markdown"
}
```

#### `export_all_collections`
```json
{
  "file_operation": {
    "id": "op-uuid",
    "state": "processing",
    "type": "export",
    "name": "workspace-export.zip"
  },
  "format": "outline-markdown"
}
```

---

### Batch Operations

All batch operations share a common structure:

```json
{
  "operation": "archive|move|delete|update|create",
  "total": 5,
  "succeeded": 4,
  "failed": 1,
  "results": [
    {
      "id": "doc-uuid",
      "status": "success",
      "title": "Document Title"
    },
    {
      "id": "doc-uuid-2",
      "status": "failed",
      "error": "Error message"
    }
  ]
}
```

#### `batch_create_documents`
Adds `created_ids` array:
```json
{
  "operation": "create",
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "results": [...],
  "created_ids": ["new-uuid-1", "new-uuid-2", "new-uuid-3"]
}
```

#### `batch_move_documents`
Adds target information:
```json
{
  "operation": "move",
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [...],
  "target_collection_id": "col-uuid",
  "target_parent_id": "parent-doc-uuid"
}
```

#### `batch_delete_documents`
Adds permanent flag:
```json
{
  "operation": "delete",
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "permanent": false,
  "results": [...]
}
```

---

### AI Tools

#### `ask_ai_about_documents`
```json
{
  "answer": "The AI-generated answer text...",
  "sources": [
    {
      "document_id": "doc-uuid",
      "title": "Source Document"
    }
  ],
  "question": "Original question asked",
  "collection_id": "col-uuid",
  "document_id": "doc-uuid"
}
```
Note: `collection_id` and `document_id` only present if specified in the request.

---

## Usage Examples

### Python - Extracting Structured Data
```python
result = await client.call_tool("read_document", {"document_id": "abc123"})

# Human-readable text
print(result.content[0].text)

# Structured data
data = result.structuredContent
print(f"Title: {data['title']}")
print(f"Content length: {len(data['text'])} chars")
```

### Checking for Errors
```python
result = await client.call_tool("read_document", {"document_id": "invalid"})

if result.structuredContent and "error" in result.structuredContent:
    print(f"Error: {result.structuredContent['error']}")
else:
    # Process successful result
    doc = result.structuredContent
```

### Processing Batch Results
```python
result = await client.call_tool("batch_archive_documents", {
    "document_ids": ["doc1", "doc2", "doc3"]
})

data = result.structuredContent
print(f"Archived {data['succeeded']} of {data['total']} documents")

for item in data['results']:
    if item['status'] == 'failed':
        print(f"Failed: {item['id']} - {item['error']}")
```
