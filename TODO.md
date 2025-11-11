# MCP Outline Server - Enhancement Roadmap

This document tracks quality-of-life enhancements and new features based on the latest MCP 2025 specifications and capabilities.

## Current Status

- **MCP SDK Version**: FastMCP 1.20.0+
- **Tools Implemented**: 25
- **MCP Features Used**: Tools only (stdio, SSE, streamable-http transports)
- **MCP Features NOT Used**: Resources, Prompts, Sampling

---

## Phase 1: Core MCP Features (High Priority)

### 1.1 Add MCP Resources Support
**Complexity**: Moderate
**Status**: Not Started

Implement resource handlers to expose Outline data via MCP URIs:

- [ ] Implement `@mcp.resource()` decorators in new `resources/` module
- [ ] Create `list_resources()` handler
- [ ] Create `read_resource()` handler
- [ ] Add resource: `outline://collection/{id}` - Collection metadata and properties
- [ ] Add resource: `outline://document/{id}` - Full document content (markdown)
- [ ] Add resource: `outline://collection/{id}/tree` - Hierarchical document tree
- [ ] Add resource: `outline://collection/{id}/documents` - List of documents in collection
- [ ] Add resource: `outline://document/{id}/backlinks` - Documents linking to this document
- [ ] Add comprehensive tests for all resources
- [ ] Update README with resource examples

**Benefits**:
- Direct content access via URIs
- Enables AI to fetch context without explicit tool calls
- Better integration with MCP-aware clients

---


### 1.3 Add MCP Sampling Support
**Complexity**: Complex
**Status**: Not Started

Implement LLM sampling via `ctx.sample()` for AI-powered enhancements:

- [ ] Update FastMCP to ensure sampling support is available
- [ ] Create `ai_enhancements/` module for AI-powered tools
- [ ] Add tool: **`suggest_document_title`**
  - Takes: document_content (string), context (optional string)
  - Uses: ctx.sample() to generate 3-5 title suggestions
  - Returns: List of suggested titles with rationale
- [ ] Add tool: **`enhance_document_content`**
  - Takes: document_id (string), enhancement_type (enum: clarity|grammar|structure|all)
  - Uses: ctx.sample() to suggest improvements
  - Returns: Detailed suggestions with examples
- [ ] Add tool: **`auto_categorize_document`**
  - Takes: document_id (string)
  - Uses: ctx.sample() to analyze content and suggest collections/tags
  - Returns: Recommended collection and reasoning
- [ ] Add tool: **`generate_document_summary`**
  - Takes: document_id (string), length (enum: short|medium|long)
  - Uses: ctx.sample() to create summary
  - Returns: Formatted summary
- [ ] Add tool: **`suggest_related_documents`**
  - Takes: document_id (string), limit (optional int)
  - Uses: ctx.sample() to analyze and find semantically related docs
  - Returns: List of related documents with relevance scores
- [ ] Add comprehensive tests (mock ctx.sample())
- [ ] Update README with sampling examples

**Benefits**:
- AI-powered content enhancement
- Intelligent document organization
- Automated summarization and categorization

---

## Phase 2: Transport & Performance Upgrades

### 2.1 Streamable HTTP Transport (2025-03-26 Spec)
**Complexity**: Moderate
**Status**: Not Started

Update to the new Streamable HTTP transport specification:

- [ ] Research Streamable HTTP spec from MCP docs (2025-03-26 revision)
- [ ] Update FastMCP to latest version supporting Streamable HTTP
- [ ] Implement Streamable HTTP transport mode
- [ ] Add health check endpoints: `/health`, `/ready`, `/metrics`
- [ ] Update transport configuration in server.py
- [ ] Update README with Streamable HTTP examples
- [ ] Add transport-specific tests
- [ ] Mark old SSE transport as deprecated with migration guide
- [ ] Update docker-compose.yml for new transport
- [ ] Update CI/CD to test all transport modes

**Benefits**:
- Better performance than SSE
- Simpler implementation
- Standards-compliant with latest spec
- Multiple client connection support

---

### 2.2 Async HTTP Client Migration
**Complexity**: Moderate
**Status**: Not Started

Replace synchronous `requests` library with async HTTP client:

- [ ] Choose async HTTP library: `httpx` (recommended) or `aiohttp`
- [ ] Update requirements in pyproject.toml
- [ ] Refactor OutlineClient to use async methods:
  - [ ] Convert all HTTP methods to async (get, post, delete, etc.)
  - [ ] Add async context manager support (`async with OutlineClient()`)
  - [ ] Implement connection pooling
  - [ ] Add configurable timeout settings
- [ ] Update all tool functions to await OutlineClient calls
- [ ] Add connection lifecycle management
- [ ] Configure connection pool size and limits
- [ ] Update all tests to use async patterns
- [ ] Run performance benchmarks (async vs sync)
- [ ] Update README with async usage examples

**Benefits**:
- True async operations (non-blocking)
- Better performance under load
- Connection pooling for efficiency
- Scalable for multiple concurrent requests


## Phase 3: API Coverage Expansion

### 3.1 Document Features
**Complexity**: Moderate (per feature)
**Status**: Not Started

Expand Outline API coverage with missing document features:

- [ ] **Templates**:
  - [ ] Add tool: `list_document_templates` - List available templates
  - [ ] Add tool: `create_document_from_template` - Create from template
  - [ ] Add OutlineClient methods: `list_templates()`, `create_from_template()`
  - [ ] Add tests
- [ ] **Revision History**:
  - [ ] Add tool: `get_document_revisions` - List document versions
  - [ ] Add tool: `get_document_revision` - Get specific revision content
  - [ ] Add tool: `restore_document_revision` - Revert to old version
  - [ ] Add OutlineClient methods: `get_revisions()`, `get_revision()`, `restore_revision()`
  - [ ] Add tests
- [ ] **Favorites/Stars**:
  - [ ] Add tool: `star_document` - Bookmark a document
  - [ ] Add tool: `unstar_document` - Remove bookmark
  - [ ] Add tool: `list_starred_documents` - List user's starred documents
  - [ ] Add OutlineClient methods: `star()`, `unstar()`, `list_starred()`
  - [ ] Add tests
- [ ] **Search Pagination**:
  - [ ] Add `offset` and `limit` parameters to `search_documents` tool
  - [ ] Update OutlineClient.search_documents() to support pagination
  - [ ] Update search result formatter to show pagination info
  - [ ] Add tests
- [ ] **File Attachments**:
  - [ ] Add tool: `upload_attachment` - Upload file to document
  - [ ] Add tool: `list_attachments` - List document attachments
  - [ ] Add tool: `download_attachment` - Download attachment
  - [ ] Add tool: `delete_attachment` - Remove attachment
  - [ ] Add OutlineClient methods for attachment operations
  - [ ] Handle file encoding/decoding
  - [ ] Add tests

**Benefits**:
- Complete Outline API coverage
- Better document management capabilities
- Enhanced collaboration features

---

### 3.2 Collaboration Features
**Complexity**: Moderate (per feature)
**Status**: Not Started

Add advanced collaboration tools:

- [ ] **Sharing & Permissions**:
  - [ ] Add tool: `create_share_link` - Generate public/team share link
  - [ ] Add tool: `revoke_share_link` - Remove share link
  - [ ] Add tool: `list_document_shares` - List active shares
  - [ ] Add OutlineClient methods for share operations
  - [ ] Add tests
- [ ] **User Mentions**:
  - [ ] Add tool: `mention_user_in_comment` - @ mention in comment
  - [ ] Update comment tools to support mentions
  - [ ] Add OutlineClient support for mentions API
  - [ ] Add tests
- [ ] **Subscriptions**:
  - [ ] Add tool: `subscribe_to_document` - Get notifications
  - [ ] Add tool: `unsubscribe_from_document` - Stop notifications
  - [ ] Add tool: `list_subscriptions` - List user's subscriptions
  - [ ] Add OutlineClient methods for subscription operations
  - [ ] Add tests
- [ ] **Activity Tracking**:
  - [ ] Add tool: `get_document_viewers` - List recent viewers
  - [ ] Add tool: `get_document_editors` - List recent editors
  - [ ] Add tool: `get_document_activity` - Full activity log
  - [ ] Add OutlineClient methods for activity tracking
  - [ ] Add tests

**Benefits**:
- Enhanced team collaboration
- Better visibility into document activity
- Improved notification management

---

### 3.3 Batch Operations
**Complexity**: Moderate
**Status**: ✅ Completed

Implement batch operations for efficiency:

- [x] Create `features/documents/batch_operations.py` module
- [x] Add tool: **`batch_create_documents`**
  - Takes: List of document specifications
  - Returns: List of created document IDs
  - Handles partial failures gracefully
- [x] Add tool: **`batch_move_documents`**
  - Takes: List of document IDs, target collection ID
  - Returns: Success/failure status for each
- [x] Add tool: **`batch_archive_documents`**
  - Takes: List of document IDs
  - Returns: Archive status for each
- [x] Add tool: **`batch_update_documents`**
  - Takes: List of document IDs with updates
  - Returns: Update status for each
- [x] Add tool: **`batch_delete_documents`**
  - Takes: List of document IDs, permanent flag
  - Returns: Deletion status for each
- [x] Implement rate limit awareness (leverages existing OutlineClient)
- [x] Add comprehensive tests with partial failure scenarios
- [x] Document batch operation limits and best practices (in tool docstrings)

**Benefits**:
- Efficient bulk operations
- Reduced API calls
- Better rate limit management
- Time savings for large-scale operations

---

## Phase 4: Developer Experience

### 4.1 Documentation Site
**Complexity**: Moderate
**Status**: Not Started

Create comprehensive API documentation:

- [ ] Choose documentation framework: MkDocs (recommended) or Sphinx
- [ ] Set up documentation structure in `docs/` directory
- [ ] Create documentation pages:
  - [ ] Getting Started guide
  - [ ] Installation & Configuration
  - [ ] Transport Modes (stdio, SSE, Streamable HTTP)
  - [ ] Tools Reference (auto-generated from docstrings)
  - [ ] Resources Reference
  - [ ] Prompts Reference
  - [ ] API Client Reference
  - [ ] Architecture Overview
  - [ ] Contributing Guide
  - [ ] Troubleshooting Guide
- [ ] Add interactive examples and code snippets
- [ ] Create architecture diagrams (using Mermaid or PlantUML)
- [ ] Add API authentication guide
- [ ] Document rate limiting behavior
- [ ] Set up GitHub Pages deployment
- [ ] Add documentation build to CI/CD
- [ ] Add "Edit on GitHub" links

**Benefits**:
- Better onboarding experience
- Reduced support burden
- Professional presentation
- Easier contribution process

---

### 4.2 Tooling Improvements
**Complexity**: Simple to Moderate (per item)
**Status**: Not Started

Enhance development tools and error handling:

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
  - [ ] Add version checker script
  - [ ] Add dependency update checker

**Benefits**:
- Better debugging experience
- Faster issue resolution
- Clearer error messages
- Easier onboarding

---

### 4.3 Testing Enhancements
**Complexity**: Moderate
**Status**: Not Started

Expand test coverage and quality:

- [ ] **Integration Tests**:
  - [ ] Set up test Outline instance (Docker-based)
  - [ ] Create integration test suite with real API calls
  - [ ] Test all tools end-to-end
  - [ ] Test all transport modes
  - [ ] Add to CI/CD (optional, on-demand)
- [ ] **Performance Tests**:
  - [ ] Create benchmark suite using pytest-benchmark
  - [ ] Benchmark tool execution times
  - [ ] Benchmark with/without caching
  - [ ] Benchmark async vs sync client
  - [ ] Add performance regression detection
- [ ] **Transport-Specific Tests**:
  - [ ] Test stdio transport in isolation
  - [ ] Test SSE transport with multiple clients
  - [ ] Test Streamable HTTP transport
  - [ ] Test transport switching
- [ ] **Coverage Improvements**:
  - [ ] Increase coverage to 95%+
  - [ ] Add edge case tests
  - [ ] Add error path tests
  - [ ] Add concurrent operation tests
- [ ] **Test Infrastructure**:
  - [ ] Add test fixtures for common scenarios
  - [ ] Create test data generators
  - [ ] Add test helper utilities
  - [ ] Improve test organization

**Benefits**:
- Higher confidence in releases
- Catch regressions early
- Performance visibility
- Better code quality

---

### 4.4 Docker & CI/CD Infrastructure
**Complexity**: Moderate
**Status**: Partially Complete

Improve Docker infrastructure and automated builds:

- [x] **Local Development Environment** ✓ COMPLETED
  - [x] Update docker-compose.yml with self-hosted Outline
  - [x] Add Dex OIDC authentication provider
  - [x] Add configuration examples (config/outline.env.example)
  - [x] Update README with local setup instructions
  - [x] Enable local testing without paid Outline account

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

### 5.2 Advanced Search
**Complexity**: Moderate
**Status**: Not Started

- [ ] Add date range filters to search
- [ ] Add author filtering
- [ ] Add tag filtering
- [ ] Add content type filtering
- [ ] Implement faceted search results
- [ ] Add search result ranking options

---

## Research & Investigation

### Topics to Explore

- [ ] **Structured Data Support** (June 2025 MCP spec):
  - Research returning dictionaries serialized to JSON
  - Evaluate if tools should return structured data vs strings
  - Assess compatibility with FastMCP

- [ ] **Structured Input Requests** (June 2025 MCP spec):
  - Research interactive tool workflows
  - Evaluate use cases (multi-step document creation, guided wizards)
  - Assess FastMCP support

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

## Completed Items

None yet - this is a fresh roadmap!

---

## Notes

### Prioritization Criteria

Items are prioritized based on:
1. **Impact**: How much value does this add to users?
2. **Complexity**: How difficult is implementation?
3. **Dependencies**: What must be done first?
4. **MCP Compliance**: Does this use core MCP features?

### Success Metrics

- All core MCP features (Resources, Prompts, Sampling) implemented
- Transport upgraded to Streamable HTTP
- Documentation site live
- Test coverage > 95%
- Performance benchmarks established
- Community adoption and feedback

---

Last Updated: 2025-11-06
