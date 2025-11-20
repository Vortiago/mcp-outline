# MCP Outline Server - Enhancement Roadmap

This document tracks quality-of-life enhancements and new features based on the latest MCP 2025 specifications and capabilities.

## Phase 1: Core MCP Features (High Priority)

### 1.1 Add MCP Resources Support
**Complexity**: Moderate
**Status**: ✅ COMPLETE (2025-11-16)

Implemented resource handlers to expose Outline data via MCP URIs using FastMCP's `@mcp.resource()` decorator.

### 1.2 Add Read-Only Mode and Tool Annotations
**Complexity**: Low-Moderate
**Status**: Not Started
**Priority**: HIGH (safety feature for self-hosted instances)

Implement environment variables to restrict destructive operations and add MCP tool annotations for better client UX.

**Why**:
- Self-hosted Outline instances may need read-only access for AI agents
- Users may want to prevent accidental deletions while allowing creates/updates
- MCP spec (March 2025) introduced tool annotations for better client behavior
- Clients can show warnings/confirmations for destructive operations
- Follows pattern from `OUTLINE_DISABLE_AI_TOOLS` feature

**Environment Variables to Add**:

1. **`OUTLINE_READ_ONLY`** (default: false)
   - When `true`: Disables ALL write operations (create, update, delete, archive, move, comments)
   - Use case: Viewer-only access, search and read documents without modification
   - Blocks registration of: document_content, document_lifecycle, document_organization, document_collaboration, collection_tools, batch_operations
   - Allows: document_search, document_reading, list operations

2. **`OUTLINE_DISABLE_DESTRUCTIVE`** (default: false)
   - When `true`: Disables only destructive delete/permanent operations
   - Use case: Allow create/update workflows but prevent data loss
   - Blocks only: `delete_document`, `delete_collection` (and their permanent variants)
   - Allows: create, update, archive, move, comment operations

**Tool Annotations to Add**:

Use `from mcp.types import ToolAnnotations` and apply to ALL tools:

**`readOnlyHint=True`** (doesn't modify environment):
- `search_documents`
- `get_document`
- `get_document_as_markdown`
- `list_collections`
- `get_collection_structure`
- `list_archived_documents`
- `list_trash`
- `get_document_backlinks`
- `list_comments`
- `get_comment`

**`readOnlyHint=False, destructiveHint=False`** (additive updates):
- `create_document`
- `add_comment`
- `create_collection`
- `archive_document` (reversible)
- `unarchive_document` (reversible)

**`readOnlyHint=False, destructiveHint=True`** (destructive updates):
- `update_document` (overwrites content)
- `delete_document`
- `move_document` (changes hierarchy)
- `update_collection`
- `delete_collection`
- `export_collection` (potentially destructive based on MCP spec - removes on export? Check API)
- `batch_archive_documents`
- `batch_delete_documents`

**`idempotentHint`**: Add where relevant
- `True`: delete (calling twice = same result), get/read operations, archive
- `False`: create (calling twice = two items), update (may change each time)

**`openWorldHint`**: SKIP or use sparingly
- Based on research: GitHub MCP only uses this on search tools, not all API calls
- Consider using `openWorldHint=True` only on: `search_documents`, `ask_ai_about_documents`
- All other tools: omit or use `False` (controlled operations on known entities)

**Implementation Steps**:

1. **Update `src/mcp_outline/features/documents/__init__.py`**:
   - Add env var checks for `OUTLINE_READ_ONLY` and `OUTLINE_DISABLE_DESTRUCTIVE`
   - Conditionally register tool modules based on flags
   - Follow existing pattern from `OUTLINE_DISABLE_AI_TOOLS`

2. **Add annotations to each tool registration**:
   - `document_search.py` - All readOnlyHint=True
   - `document_reading.py` - All readOnlyHint=True
   - `document_content.py` - create=additive, update=destructive, comment=additive
   - `document_lifecycle.py` - delete=destructive, archive=additive
   - `document_organization.py` - move=destructive
   - `document_collaboration.py` - Mixed (read comments vs add comments)
   - `collection_tools.py` - create=additive, update/delete=destructive
   - `batch_operations.py` - All destructive

3. **Update documentation**:
   - Add to `.env.example`
   - Update `README.md` configuration table
   - Update `CLAUDE.md` configuration section
   - Add examples of when to use each mode

4. **Add tests**:
   - Test tool registration with `OUTLINE_READ_ONLY=true`
   - Test tool registration with `OUTLINE_DISABLE_DESTRUCTIVE=true`
   - Test annotations are properly set on tools
   - Follow pattern from `test_ai_tools_disabled_via_env_var`

**Benefits**:
- Actual enforcement via env variables (security/safety)
- Better UX via annotations (client can show warnings)
- Defense in depth approach
- Flexibility for different use cases (read-only vs. no-deletes)
- MCP spec compliance (March 2025 annotations)

**Reference**:
- MCP spec tool annotations: https://modelcontextprotocol.io/docs/concepts/tools
- GitHub MCP server issue #1100 for openWorldHint usage patterns
- Existing implementation: `OUTLINE_DISABLE_AI_TOOLS` in `__init__.py:38-44`

## Phase 3: API Coverage Expansion

### 3.1 Document Features
**Status**: Mostly Complete

**Search Pagination** (✅ COMPLETE):
- [x] ✅ `offset` and `limit` parameters already implemented
- [x] ✅ OutlineClient.search_documents() supports pagination
- [x] ✅ Formatter shows pagination info in document_search.py:141-146
- [x] ✅ Tests exist in tests/features/test_document_search.py
- No further work needed for pagination!

**Templates** (Limited Support):
- [ ] Add tool: `list_document_templates` - List templates via documents.list with template=true
- [ ] Add tool: `create_template_from_document` - Convert document to template via documents.templatize
- [ ] Add OutlineClient methods: `list_templates()`, `create_template_from_document()`
- [ ] Add tests
- ❌ Do NOT implement `create_document_from_template` - This endpoint doesn't exist in Outline API

**Revision History** (Low Priority - Nice to Have):
- [ ] Add tool: `get_document_revisions` - List document versions with metadata
- [ ] Add tool: `get_document_revision` - Get specific revision content
- [ ] Add OutlineClient methods: `list_revisions()`, `get_revision()`
- [ ] Add tests
- ❌ Do NOT implement `restore_document_revision` - too risky for automation

**Benefits**:
- Proper handling of large result sets (pagination - DONE!)
- Core workflow automation (templates)
- Focus on content operations, not UI feature parity

---

### 4.2 Tooling Improvements
**Complexity**: Simple to Moderate (per item)
**Status**: Not Started

Enhance development tools and error handling (hobby-project scope):

- [ ] **Configuration Validation**:
  - [ ] Add Pydantic models for configuration
  - [ ] Validate env vars on startup
  - [ ] Provide clear error messages for missing/invalid config
  - [ ] Add configuration schema documentation
- [ ] **Error Messages**:
  - [ ] Create error code system (e.g., OUTLINE_001, OUTLINE_002)
  - [ ] Add troubleshooting hints to error messages
  - [ ] Link to documentation from errors
  - [ ] Improve exception messages with context
- [ ] **MCP Inspector Integration**:
  - [ ] Add detailed MCP Inspector setup guide
  - [ ] Create example inspector configurations
  - [ ] Document debugging workflow
  - [ ] Add inspector screenshot/demo
- [ ] **Debugging Tools**:
  - [ ] Add `--debug` flag for verbose logging
  - [ ] Create diagnostic tool: `mcp-outline diagnose`
  - [ ] Add connection test tool: `mcp-outline test-connection`
  - [ ] Add API key validation tool
- [ ] **Development Scripts**:
  - [ ] Improve start_server.sh with better error handling
  - [ ] Add setup script for first-time setup

**Benefits**:
- Better debugging experience
- Faster issue resolution
- Clearer error messages
- Easier onboarding for users

---

### 4.3 Testing Enhancements
**Complexity**: Moderate
**Status**: Not Started

Expand test coverage and quality (hobby-project scope - only meaningful tests):

- [ ] **Integration Tests**:
  - [ ] Set up test Outline instance (Docker-based)
  - [ ] Create integration test suite with real API calls
  - [ ] Test all tools end-to-end
  - [ ] Add to CI/CD (optional, on-demand)
- [ ] **Performance Tests**:
  - [ ] Create benchmark suite using pytest-benchmark
  - [ ] Benchmark tool execution times
  - [ ] Benchmark with/without connection pooling
  - [ ] Add performance regression detection
- [ ] **Transport-Specific Tests**:
  - [ ] Test stdio transport in isolation
  - [ ] Test Streamable HTTP transport
  - [ ] Test rate limiting behavior across transports
- [ ] **Coverage Improvements**:
  - [ ] Increase coverage to 95%+
  - [ ] Add edge case tests (malformed input, empty results, API errors)
  - [ ] Add error path tests (authentication failures, timeouts, rate limiting)
  - [ ] Add concurrent operation tests (parallel requests, connection pool usage)
- [ ] **Test Fixtures**:
  - [ ] Add test fixtures for common scenarios
  - [ ] Create test data generators for realistic Outline data

**Benefits**:
- Higher confidence in releases
- Catch regressions early
- Performance visibility
- Meaningful edge case coverage

---

### 4.4 Docker & CI/CD Infrastructure
**Complexity**: Moderate
**Status**: Partially Complete

Improve Docker infrastructure and automated builds:

- [ ] **Multi-Architecture Docker Builds**
  - [ ] Add GitHub Actions workflow for automated builds
  - [ ] Support AMD64 and ARM64 architectures
  - [ ] Publish to GitHub Container Registry (GHCR)
  - [ ] Use QEMU for cross-platform compilation
  - [ ] Enable deployment on Apple Silicon, Raspberry Pi, ARM servers
  - [ ] Add version tagging strategy (latest, semver, outline-version)
  - [ ] Update README with pre-built image usage

**Benefits**:
- Easy local testing without external dependencies
- Multi-platform deployment support
- Enhanced security and supply chain trust
- Automated Docker image publishing


---

## Phase 5: Advanced Features (Future)

### 5.2 Enhanced Search Parameters
**Complexity**: Low
**Status**: Not Started

**Note**: Parameter additions to existing `search_documents` tool (not a separate phase)

Add optional parameters matching Outline API capabilities:
- [ ] `user_id` - Filter by document editor (Outline API: userId)
- [ ] `document_id` - Search within specific document (Outline API: documentId)
- [ ] `status_filter` - Enum: "draft", "published", "archived"
- [ ] `date_filter` - Enum: "day", "week", "month", "year" (relative date ranges)
- [ ] Update OutlineClient.search_documents() to pass filters to API
- [ ] Update formatter to show applied filters
- [ ] Add tests for filtered searches

**Do NOT implement**:
- ❌ `tags` - Not supported by Outline API
- ❌ `author` - Use `user_id` instead (Outline uses editor, not author)
- ❌ `sort_by` - API only supports relevance sorting
- ❌ `date_from`, `date_to` - Use `date_filter` enum instead

**Reference**: Outline API `documents.search` endpoint supports userId, documentId, statusFilter, dateFilter parameters

---

## Research & Investigation

### Topics to Explore

- [x] **Structured Data Support / Output Schemas** (June 2025 MCP spec):
  - **Status**: ✅ Researched - Ready for implementation
  - **FastMCP Support**: v2.10.0+ with automatic schema generation
  - **What**: Tools return TypedDict/Pydantic models instead of strings; FastMCP auto-generates JSON schemas
  - **Benefits**: Better AI integration, token efficiency, type safety, backward compatible (dual output)
  - **Complexity**: ⭐⭐ Low-Medium (can migrate tools incrementally)
  - **Priority**: HIGH - Should implement in Phase 2/3
  - **Next Steps**: Verify FastMCP version, create output models, refactor formatters to return dicts
  - **Example**: `async def search_documents() -> list[SearchResult]:` instead of `-> str`

- [ ] **MCP Context Features**:
  - Research additional FastMCP context capabilities
  - Explore server-to-client requests
  - Investigate notification systems

- [ ] **Security Enhancements**:
  - Audit for security vulnerabilities
  - Implement request validation
  - Add rate limiting per client
  - Research API key scoping

---
