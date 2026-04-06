# Plan: Move API-Related Docs from Engineering to a New API Documentation Collection

## Step-by-Step Tool Calls

### Phase 1: Discovery -- Find the Engineering Collection and Its Contents

**1. List all collections to get the Engineering collection ID.**

```
list_collections()
```

No arguments needed. Returns all collections with their IDs, names, and descriptions. From the results, note the `id` of the "Engineering" collection (e.g., `abc123-...`).

**2. Get the full document tree of the Engineering collection.**

```
get_collection_structure(collection_id="<engineering_collection_id>")
```

This returns the hierarchical document tree showing every document (with its ID and title) inside the Engineering collection. Review the titles to identify which documents are API-related (e.g., "REST API Reference", "API Authentication", "API Rate Limiting", "Webhook API", "GraphQL Endpoints", etc.).

### Phase 2: Create the Target Collection

**3. Create the new "API Documentation" collection.**

```
create_collection(
    name="API Documentation",
    description="Central collection for all API-related documentation including references, guides, and specifications."
)
```

Note the returned `id` of the newly created collection (e.g., `def456-...`).

### Phase 3: Move Documents in Bulk

**4. Batch-move all identified API-related documents into the new collection.**

```
batch_move_documents(
    document_ids=[
        "<api_doc_id_1>",
        "<api_doc_id_2>",
        "<api_doc_id_3>",
        ...
    ],
    collection_id="<api_documentation_collection_id>"
)
```

Use the document IDs identified in step 2 and the collection ID from step 3. `batch_move_documents` moves multiple documents in a single call, which is more efficient than calling `move_document` individually for each one.

If any of the API documents had a parent-child hierarchy in the Engineering collection that should be preserved, use `move_document` individually with the `parent_document_id` argument to re-establish nesting within the new collection:

```
move_document(
    document_id="<child_doc_id>",
    collection_id="<api_documentation_collection_id>",
    parent_document_id="<parent_doc_id_in_new_collection>"
)
```

### Phase 4: Verify the Result

**5. Verify the new API Documentation collection has the correct documents.**

```
get_collection_structure(collection_id="<api_documentation_collection_id>")
```

Confirm all moved documents appear in the new collection's tree.

**6. Verify the Engineering collection no longer contains the moved documents.**

```
get_collection_structure(collection_id="<engineering_collection_id>")
```

Confirm the API-related documents are gone from Engineering and only non-API documents remain.

## Summary

| Step | Tool                       | Purpose                                      |
|------|----------------------------|----------------------------------------------|
| 1    | `list_collections`         | Find the Engineering collection ID           |
| 2    | `get_collection_structure` | See all documents in Engineering              |
| 3    | `create_collection`        | Create the new "API Documentation" collection |
| 4    | `batch_move_documents`     | Move all API docs to the new collection       |
| 5    | `get_collection_structure` | Verify docs landed in the new collection      |
| 6    | `get_collection_structure` | Verify docs removed from Engineering          |

## Notes

- **Bulk vs. individual moves**: `batch_move_documents` is preferred for efficiency. Fall back to individual `move_document` calls only if parent-child nesting needs to be explicitly set during the move.
- **No deletion needed**: `move_document` and `batch_move_documents` relocate documents -- they do not leave copies behind in the source collection.
- **Hierarchy preservation**: If the API docs were nested (e.g., "API Reference" with children "Endpoints" and "Authentication"), the batch move places them at the root of the new collection. Use individual `move_document` with `parent_document_id` afterward to restore the hierarchy if needed.
