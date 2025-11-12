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

## Phase 3: API Coverage Expansion

### 3.1 Document Features
**Status**: Not Started

**High Priority:**
- [ ] **Templates**:
  - [ ] Add tool: `list_document_templates` - List available templates
  - [ ] Add tool: `create_document_from_template` - Create from template
  - [ ] Add OutlineClient methods: `list_templates()`, `create_from_template()`
  - [ ] Add tests

- [ ] **Search Pagination** (CRITICAL):
  - [ ] Add `offset` and `limit` parameters to `search_documents` tool
  - [ ] Update OutlineClient.search_documents() to support pagination
  - [ ] Update formatter: "Showing X-Y of Z results"
  - [ ] Add tests

**Low Priority (Phase 4/5):**
- [ ] **Revision History** (read-only):
  - [ ] Add tool: `get_document_revisions` - List versions with metadata
  - [ ] Add tool: `get_document_revision` - Get specific version content
  - [ ] Add OutlineClient methods
  - [ ] Add tests
  - ❌ Do NOT implement `restore_document_revision` - too risky for automation

**Benefits**:
- Core workflow automation (templates)
- Proper handling of large result sets (pagination)
- Focus on content operations, not UI feature parity

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
**Complexity**: Low-Moderate
**Status**: Not Started

**Note**: These are just parameter additions to existing `search_documents` tool, not a separate phase

- [ ] Add optional parameters to `search_documents` tool:
  - [ ] `date_from`, `date_to` - Date range filtering
  - [ ] `author` - Filter by document author
  - [ ] `tags` - Filter by tags
  - [ ] `sort_by` - Ranking options (relevance, date, title)
- [ ] Update OutlineClient.search_documents() to pass filters to API
- [ ] Update formatter to show applied filters
- [ ] Add tests for filtered searches

**Do NOT implement**: Separate tools for each filter type - just enhance existing tool

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

## Notes

### Prioritization Criteria

Items are prioritized based on:
1. **Impact**: How much value does this add to users?
2. **Complexity**: How difficult is implementation?
3. **Dependencies**: What must be done first?
4. **MCP Compliance**: Does this use core MCP features?
