# Pull Request: Batch Operations

## Title
```
feat: implement batch operations for efficient bulk document management (#3.3)
```

## Description

### Summary
Implements batch operation tools for efficient bulk document management, completing TODO Phase 3, Section 3.3. These tools enable users to perform operations on multiple documents in a single call with robust error handling and detailed reporting.

### New Tools Added
- **`batch_archive_documents`** - Archive multiple documents at once
- **`batch_move_documents`** - Move documents to different collections/parents in bulk
- **`batch_delete_documents`** - Delete or trash multiple documents (with permanent option)
- **`batch_update_documents`** - Update multiple documents with different changes
- **`batch_create_documents`** - Create multiple documents in one operation

### Key Features
✅ **Partial Failure Handling** - Operations continue even if individual items fail, providing complete status for each document
✅ **Detailed Reporting** - Clear success/failure breakdown with document IDs and specific error messages
✅ **Automatic Rate Limiting** - Leverages existing `OutlineClient` rate limit handling
✅ **Input Validation** - Comprehensive checks for required fields and edge cases
✅ **Pattern Consistency** - Follows existing codebase architecture exactly (synchronous tools, error handling patterns)
✅ **User-Friendly Output** - Formatted results with ✓/✗ indicators and grouped success/failure sections

### Example Output
```
Batch Archive Results:
- Total: 10
- Succeeded: 8
- Failed: 2

Details:
  ✓ doc123 - My Document
  ✓ doc456 - Another Document
  ...
  ✗ doc789 - Error: Document not found
  ✗ doc012 - Error: Permission denied
```

### Implementation Details
- **Module**: `src/mcp_outline/features/documents/batch_operations.py` (665 lines)
- **Tests**: `tests/features/documents/test_batch_operations.py` (664 lines, 31 comprehensive tests)
- **Integration**: Registered in `features/documents/__init__.py`
- **Recommended batch size**: 10-50 documents per operation
- **Sequential processing** with automatic rate limit respect

### Testing Coverage
- ✅ All success scenarios
- ✅ All failure scenarios
- ✅ Partial success/failure mixing
- ✅ Edge cases (empty lists, single items, missing required fields)
- ✅ Error propagation (OutlineClientError, generic exceptions)
- ✅ Helper function validation

**Test Results**: 31/31 batch operation tests pass, 150/150 total suite tests pass

### Code Quality
- ✅ All `ruff` linting checks pass
- ✅ PEP 8 compliant
- ✅ Type hints throughout
- ✅ Comprehensive docstrings with usage examples
- ✅ DRY principles with helper functions
- ✅ Consistent with all existing tool patterns

### Documentation
- Updated TODO.md to mark Section 3.3 as completed
- Detailed docstrings for each tool with use cases
- Batch size recommendations included
- Error handling behavior documented

### Breaking Changes
None - This is a pure feature addition with no changes to existing APIs.

### Benefits
- **Time savings** for bulk operations
- **Better user experience** with clear feedback
- **Robust error handling** prevents data loss
- **Rate limit friendly** via sequential processing

---

**Closes**: TODO Section 3.3 - Batch Operations
