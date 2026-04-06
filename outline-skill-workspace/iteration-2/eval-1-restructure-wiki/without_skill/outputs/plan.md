# Plan: Move API-related docs from Engineering to a new API Documentation collection

## Step 1: Find the Engineering collection ID

**Tool:** `list_collections()`
**Arguments:** none (or `limit: 50` to ensure we get all collections)
**Purpose:** Get the collection ID for "Engineering" so we can browse its contents. Also confirm no "API Documentation" collection exists yet.

## Step 2: Get the full document structure of the Engineering collection

**Tool:** `get_collection_structure(collection_id: "<engineering_collection_id>")`
**Arguments:** `collection_id` from step 1
**Purpose:** See every document (and nested hierarchy) inside Engineering so we can identify which ones are API-related.

## Step 3: Read individual documents to confirm they are API-related

For each document whose title looks API-related (e.g., contains "API", "endpoint", "REST", "GraphQL", "authentication", "rate limiting", "webhook"), call:

**Tool:** `read_document(document_id: "<doc_id>")`
**Arguments:** the `document_id` from step 2
**Purpose:** Skim content to confirm the document genuinely belongs in the API Documentation collection. Repeat for every candidate document.

## Step 4: Create the new "API Documentation" collection

**Tool:** `create_collection(name: "API Documentation", description: "Documentation for all API endpoints, authentication, and integration guides.")`
**Arguments:**
- `name`: `"API Documentation"`
- `description`: `"Documentation for all API endpoints, authentication, and integration guides."`
**Purpose:** Create the target collection before moving documents into it.

## Step 5: Batch-move the confirmed API documents

**Tool:** `batch_move_documents(document_ids: ["<id1>", "<id2>", "<id3>", ...], collection_id: "<api_documentation_collection_id>")`
**Arguments:**
- `document_ids`: array of all document IDs confirmed as API-related in step 3
- `collection_id`: the ID of the newly created "API Documentation" collection from step 4
**Purpose:** Move all API-related documents in a single batch operation.

## Step 6: Verify the move

**Tool:** `get_collection_structure(collection_id: "<api_documentation_collection_id>")`
**Arguments:** the new collection's ID
**Purpose:** Confirm all moved documents now appear in the API Documentation collection.

## Step 7: Verify Engineering collection is cleaned up

**Tool:** `get_collection_structure(collection_id: "<engineering_collection_id>")`
**Arguments:** the original Engineering collection ID
**Purpose:** Confirm the API-related documents are no longer in Engineering and that no documents were accidentally left behind or incorrectly moved.

---

## Summary of tool calls (in order)

| # | Tool | Key arguments |
|---|------|---------------|
| 1 | `list_collections` | _(none)_ |
| 2 | `get_collection_structure` | `collection_id: "<engineering_id>"` |
| 3 | `read_document` (repeated N times) | `document_id: "<each candidate doc>"` |
| 4 | `create_collection` | `name: "API Documentation"` |
| 5 | `batch_move_documents` | `document_ids: [...]`, `collection_id: "<new_collection_id>"` |
| 6 | `get_collection_structure` | `collection_id: "<new_collection_id>"` |
| 7 | `get_collection_structure` | `collection_id: "<engineering_id>"` |

**Total minimum calls:** 5 (if all titles are unambiguous and no reading needed)
**Total likely calls:** 7 + N (where N is the number of documents needing content review)
