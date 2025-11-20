# MCP Outline Server - Enhancement Roadmap

This document tracks quality-of-life enhancements and new features based on the latest MCP 2025 specifications and capabilities.

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

- [ ] **MCP Prompts** (Core MCP feature):
  - **Status**: Not Started
  - **What**: Reusable message templates that guide AI interactions
  - **FastMCP Support**: Built-in via `@mcp.prompt()` decorator
  - **Benefits**: Better UX (users select pre-built workflows), standardized interactions
  - **Complexity**: ⭐ Low (simple decorator pattern)
  - **Priority**: MEDIUM - Nice UX improvement
  - **Use Cases**:
    - "Document Summary" prompt - Read doc and summarize
    - "Search and Synthesize" - Search topic, read results, synthesize
    - "Create Meeting Notes" - Template for structured note-taking
  - **Example**:
    ```python
    @mcp.prompt(title="Document Summary")
    def summarize_document(document_id: str):
        return f"Read document {document_id} and provide a concise summary"
    ```
  - **Next Steps**: Define 3-5 useful prompts for common Outline workflows

- [ ] **Progress Notifications** (Core MCP feature):
  - **Status**: Not Started
  - **What**: Report progress for long-running operations
  - **FastMCP Support**: Built-in via `ctx.report_progress(progress, total, message)`
  - **Benefits**: Better UX for batch operations, exports, large collections
  - **Complexity**: ⭐ Low (FastMCP handles protocol details)
  - **Priority**: MEDIUM - Good for batch operations
  - **Relevant Tools**: `batch_archive_documents`, `batch_delete_documents`, `export_collection`
  - **Example**:
    ```python
    @mcp.tool()
    async def batch_export(collection_id: str, ctx: Context):
        docs = await get_documents(collection_id)
        for i, doc in enumerate(docs):
            await ctx.report_progress(progress=i, total=len(docs))
            await export_document(doc)
    ```
  - **Next Steps**: Add to batch operations and collection export

- [ ] **Elicitation** (June 2025 MCP spec):
  - **Status**: Not Started - Needs research
  - **What**: Server requests user input during tool execution (human-in-the-loop)
  - **FastMCP Support**: Requires MCP SDK 2025-06-18+ and client support
  - **Benefits**: Interactive workflows, disambiguation, confirmation dialogs
  - **Complexity**: ⭐⭐ Medium (requires SDK upgrade, not all clients support)
  - **Priority**: LOW - Nice for interactive workflows but adds complexity
  - **Use Cases**:
    - Ask which document when title search has multiple matches
    - Confirm destructive operations
    - Request missing parameters dynamically
  - **Security**: Must NOT request PII, credentials, or sensitive data
  - **Example**:
    ```python
    @mcp.tool()
    async def delete_document(title: str, ctx: Context):
        matches = await search_by_title(title)
        if len(matches) > 1:
            choice = await ctx.elicit("Multiple matches", matches)
    ```
  - **Next Steps**: Research FastMCP support level, check client compatibility

- [ ] **Sampling** (Core MCP feature):
  - **Status**: Not Started - Needs research
  - **What**: Server requests LLM completions from client (server-initiated AI calls)
  - **FastMCP Support**: Built-in via `ctx.sample(messages)`
  - **Benefits**: Agentic behaviors, AI-powered features without API keys
  - **Complexity**: ⭐⭐ Medium
  - **Priority**: LOW - Overkill for basic document management
  - **Use Cases**:
    - Auto-generate document summaries
    - Suggest document titles based on content
    - Auto-categorize documents
  - **Example**:
    ```python
    @mcp.tool()
    async def suggest_title(content: str, ctx: Context):
        result = await ctx.sample([
            UserMessage(f"Suggest a title for: {content[:500]}")
        ])
        return result.content
    ```
  - **Next Steps**: Evaluate if use cases justify complexity

- [ ] **Argument Completions** (March 2025 MCP spec):
  - **Status**: Not Started - Low priority
  - **What**: Autocomplete suggestions for tool arguments (IDE-like experience)
  - **FastMCP Support**: Partial - Client supports, server handlers not available (Issue #1670)
  - **Benefits**: Better UX in IDEs (type-ahead for collection names, document titles)
  - **Complexity**: ⭐⭐ Medium (FastMCP limitation, not all clients support)
  - **Priority**: LOW - Nice to have, limited client support
  - **Use Cases**:
    - Collection name autocomplete
    - Document title suggestions
    - User name completions
  - **Next Steps**: Wait for FastMCP server-side completion handler support

- [ ] **Security Enhancements**:
  - Audit for security vulnerabilities
  - Implement request validation
  - Add rate limiting per client
  - Research API key scoping

---
