# Outline API Implementation Gap Analysis

**Generated**: 2025-11-06
**API Version**: Outline v3 OpenAPI Specification
**Repository**: github.com/outline/openapi

---

## Executive Summary

The MCP Outline server currently implements approximately **35% (25/71)** of the available Outline API endpoints. This analysis identifies 46 missing endpoints across 13 feature categories, with prioritized recommendations for future development.

### Quick Stats
- **Total API Endpoints**: 71
- **Currently Implemented**: ~25 endpoints (35%)
- **Missing/Not Implemented**: ~46 endpoints (65%)
- **Fully Implemented Categories**: 0 out of 13
- **Partially Implemented Categories**: 4 (Auth, Documents, Collections, Comments)
- **Not Implemented Categories**: 9 (Attachments, Groups, Revisions, Shares, Stars, Users, Views, Events, File Operations)

---

## Currently Implemented Features ✓

### Auth (1/2 endpoints - 50%)
- ✓ `auth.info` - Verify authentication and get user/team info

### Documents (11/19 endpoints - 58%)
- ✓ `documents.info` - Get document by ID
- ✓ `documents.search` - Full-text search
- ✓ `documents.list` - List documents with filtering
- ✓ `documents.create` - Create new documents
- ✓ `documents.update` - Modify existing documents
- ✓ `documents.move` - Relocate between collections
- ✓ `documents.archive` - Archive documents
- ✓ `documents.restore` - Recover from trash
- ✓ `documents.delete` - Delete documents
- ✓ `documents.export` - Export as markdown
- ✓ `documents.answerQuestion` - AI-powered Q&A

### Collections (8/16 endpoints - 50%)
- ✓ `collections.list` - List all collections
- ✓ `collections.documents` - Get document hierarchy
- ✓ `collections.create` - Create collection
- ✓ `collections.update` - Modify collection
- ✓ `collections.delete` - Delete collection
- ✓ `collections.export` - Export single collection
- ✓ `collections.export_all` - Bulk export

### Comments (3/5 endpoints - 60%)
- ✓ `comments.create` - Add comments/replies
- ✓ `comments.info` - Get comment details
- ✓ `comments.list` - List document comments

### Custom Implementations
- ✓ Document backlinks - Find documents linking to a target
- ✓ List archived documents - Custom filtering
- ✓ List trash - Custom filtering
- ✓ Unarchive document - Wrapper around restore

---

## Missing API Endpoints (46 endpoints)

### 1. ATTACHMENTS - 0/3 endpoints (0%) 🔴
**Priority: MEDIUM** | **Complexity: HIGH** | **User Impact: HIGH**

All attachment functionality is missing:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `attachments.create` | Upload files to documents | Image/file embedding |
| `attachments.redirect` | Retrieve attachment URLs | Display uploaded media |
| `attachments.delete` | Remove attachments | Cleanup unused files |

**Implementation Notes**:
- Requires multipart form handling for file uploads
- Need signed URL generation for cloud storage
- Must handle various content types (images, PDFs, etc.)
- Size limits and validation required

---

### 2. AUTHENTICATION & CONFIG - 1/2 endpoints (50%) 🟢
**Priority: LOW** | **Complexity: LOW** | **User Impact: LOW**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `auth.config` | Get workspace auth options | Unauthenticated config discovery |

**Implementation Notes**:
- Unauthenticated endpoint
- Returns available SSO providers
- Useful for building login UIs

---

### 3. COLLECTIONS - ACCESS CONTROL - 0/8 endpoints (0%) 🔴
**Priority: HIGH** | **Complexity: MEDIUM** | **User Impact: HIGH**

Missing all permission management:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `collections.info` | Get single collection | Collection details without listing all |
| `collections.add_user` | Grant user access | Share collection with team member |
| `collections.remove_user` | Revoke user access | Remove user from collection |
| `collections.memberships` | List user permissions | Audit collection access |
| `collections.add_group` | Grant group access | Share with entire team/department |
| `collections.remove_group` | Revoke group access | Remove group permissions |
| `collections.group_memberships` | List group permissions | Audit group access |

**Implementation Notes**:
- Critical for enterprise/team usage
- Requires understanding of Permission enum (read, read_write)
- Should support both individual and group-based access
- Need to handle membership pagination

---

### 4. COMMENTS - MANAGEMENT - 0/2 endpoints (0%) 🟡
**Priority: MEDIUM** | **Complexity: LOW** | **User Impact: MEDIUM**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `comments.update` | Edit existing comment | Fix typos, update content |
| `comments.delete` | Remove comment | Delete inappropriate/outdated comments |

**Implementation Notes**:
- Simple CRUD completion
- Should maintain thread integrity when deleting
- Consider cascade behavior for replies

---

### 5. DOCUMENTS - ACCESS CONTROL - 0/4 endpoints (0%) 🔴
**Priority: HIGH** | **Complexity: MEDIUM** | **User Impact: HIGH**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `documents.add_user` | Grant user access | Share specific document |
| `documents.remove_user` | Revoke user access | Remove document access |
| `documents.users` | List all accessible users | See who can access |
| `documents.memberships` | List direct permissions | Audit document-level permissions |

**Implementation Notes**:
- Granular access control below collection level
- Essential for sensitive document sharing
- Different from collection permissions

---

### 6. DOCUMENTS - ADDITIONAL FEATURES - 0/5 endpoints (0%) 🟡
**Priority: MEDIUM-HIGH** | **Complexity: VARIES** | **User Impact: HIGH**

| Endpoint | Description | Complexity | Priority |
|----------|-------------|------------|----------|
| `documents.drafts` | List all drafts | LOW | HIGH |
| `documents.viewed` | Recently viewed docs | LOW | MEDIUM |
| `documents.import` | Import Word/MD files | HIGH | HIGH |
| `documents.templatize` | Convert to template | LOW | MEDIUM |
| `documents.unpublish` | Revert to draft | LOW | MEDIUM |

**Implementation Notes**:
- `documents.import` requires file parsing (DOCX, HTML, MD)
- `documents.drafts` complements existing `documents.list`
- Templates are important for standardized workflows

---

### 7. EVENTS - AUDIT LOGGING - 0/1 endpoint (0%) 🟡
**Priority: MEDIUM** | **Complexity: LOW** | **User Impact: HIGH**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `events.list` | Retrieve audit log | Compliance, security monitoring, activity tracking |

**Implementation Notes**:
- Supports filtering by actor, document, collection, event name
- Critical for enterprise compliance (SOC 2, GDPR)
- Large result sets require pagination
- Event types include: `documents.create`, `users.signin`, etc.

---

### 8. GROUPS - 0/8 endpoints (0%) 🔴
**Priority: HIGH** | **Complexity: MEDIUM** | **User Impact: CRITICAL**

Complete category missing - essential for enterprise team management:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `groups.create` | Create user group | Organize by department/team |
| `groups.list` | List all groups | View organizational structure |
| `groups.info` | Get group details | View group metadata |
| `groups.update` | Modify group | Rename, update description |
| `groups.delete` | Remove group | Clean up unused groups |
| `groups.memberships` | List group members | See who's in the group |
| `groups.add_user` | Add member | Include user in group |
| `groups.remove_user` | Remove member | Exclude user from group |

**Implementation Notes**:
- Foundational for scalable permission management
- Groups can be granted access to collections/documents
- Must integrate with collections.add_group/remove_group
- External ID support for SSO/directory sync

---

### 9. REVISIONS - VERSION HISTORY - 0/2 endpoints (0%) 🔴
**Priority: CRITICAL** | **Complexity: MEDIUM** | **User Impact: CRITICAL**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `revisions.list` | List document history | View all versions |
| `revisions.info` | Get specific revision | Compare/restore old versions |

**Implementation Notes**:
- Essential for document management systems
- Supports pagination and sorting
- Can restore to specific revision via `documents.restore`
- Shows who made changes and when

---

### 10. SHARES - PUBLIC LINKS - 0/5 endpoints (0%) 🔴
**Priority: HIGH** | **Complexity: MEDIUM** | **User Impact: HIGH**

Complete sharing functionality missing:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `shares.create` | Create public link | Share with external users |
| `shares.info` | Get share details | View share settings |
| `shares.list` | List all shares | Audit public documents |
| `shares.update` | Modify share settings | Change expiration/permissions |
| `shares.revoke` | Disable public link | Revoke external access |

**Implementation Notes**:
- Core Outline feature for external collaboration
- Supports expiration dates
- Different permission levels (read, write)
- Must handle `shareId` parameter in `documents.info`

---

### 11. STARS - FAVORITES - 0/4 endpoints (0%) 🟢
**Priority: LOW** | **Complexity: LOW** | **User Impact: MEDIUM**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `stars.create` | Favorite doc/collection | Bookmark important items |
| `stars.delete` | Unfavorite | Remove bookmark |
| `stars.list` | List starred items | Quick access to favorites |
| `stars.update` | Modify star | Update star metadata |

**Implementation Notes**:
- Quality-of-life feature
- User-specific, not workspace-wide
- Simple CRUD operations

---

### 12. USERS - TEAM MANAGEMENT - 0/8 endpoints (0%) 🔴
**Priority: HIGH** | **Complexity: MEDIUM** | **User Impact: CRITICAL**

Complete user administration missing:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `users.info` | Get user details | View profile information |
| `users.list` | List all users | Browse team members |
| `users.invite` | Invite via email | Onboard new team members |
| `users.update` | Modify profile | Update name, avatar, etc. |
| `users.update_role` | Change role | Promote to admin, change to viewer |
| `users.suspend` | Deactivate account | Temporarily disable access |
| `users.activate` | Reactivate account | Restore suspended user |
| `users.delete` | Remove user | Permanently delete from workspace |

**Implementation Notes**:
- Essential for workspace administration
- Roles: admin, member, viewer
- Suspend vs delete (soft vs hard delete)
- Email invitation flow

---

### 13. VIEWS - ANALYTICS - 0/2 endpoints (0%) 🟡
**Priority: MEDIUM** | **Complexity: LOW** | **User Impact: MEDIUM**

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `views.create` | Record document view | Track document access |
| `views.list` | Get view statistics | Analytics and reporting |

**Implementation Notes**:
- Useful for understanding document usage
- Can track who viewed what and when
- Supports filtering and aggregation

---

## Implementation Priority Matrix

### 🔴 CRITICAL PRIORITY (Implement First)
**High business value + High user demand + Core functionality**

1. **Revisions** (2 endpoints) - Version control is non-negotiable
2. **Shares** (5 endpoints) - Public sharing is a core Outline feature
3. **Users** (8 endpoints) - Cannot manage workspace without this
4. **Groups** (8 endpoints) - Essential for scalable permissions
5. **Document Permissions** (4 endpoints) - Granular access control

**Estimated Effort**: 4-6 weeks | **Endpoints**: 27

---

### 🟡 HIGH PRIORITY (Implement Soon)
**Medium business value + Useful features + Enhance core functionality**

1. **Collection Permissions** (7 endpoints) - Complete access control
2. **Attachments** (3 endpoints) - Multimedia support
3. **Events** (1 endpoint) - Audit logging
4. **Documents.import** (1 endpoint) - File import
5. **Documents.drafts** (1 endpoint) - Draft management
6. **Comments Management** (2 endpoints) - Complete CRUD

**Estimated Effort**: 3-4 weeks | **Endpoints**: 15

---

### 🟢 MEDIUM PRIORITY (Nice to Have)
**Lower urgency + Quality-of-life improvements**

1. **Views** (2 endpoints) - Analytics
2. **Documents.templatize** (1 endpoint) - Templates
3. **Documents.unpublish** (1 endpoint) - Draft reversion
4. **Documents.viewed** (1 endpoint) - Recently viewed
5. **Stars** (4 endpoints) - Bookmarking

**Estimated Effort**: 1-2 weeks | **Endpoints**: 9

---

### 🔵 LOW PRIORITY (Future Enhancement)
**Minimal impact + Configuration/convenience features**

1. **auth.config** (1 endpoint) - Config discovery
2. **stars.update** (part of stars) - Star metadata

**Estimated Effort**: < 1 week | **Endpoints**: 1

---

## Suggested Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3) - CRITICAL
**Goal**: Enable version control and public sharing

- [ ] Revisions (revisions.list, revisions.info)
- [ ] Shares (all 5 endpoints)
- [ ] Basic users (users.list, users.info)

**Deliverable**: Users can track document history and share publicly

---

### Phase 2: Access Control (Weeks 4-7) - CRITICAL
**Goal**: Implement enterprise permission management

- [ ] Groups (full CRUD + memberships - 8 endpoints)
- [ ] Document permissions (4 endpoints)
- [ ] Collection permissions (7 endpoints)

**Deliverable**: Full team and permission management

---

### Phase 3: User Management (Weeks 8-9) - HIGH
**Goal**: Complete user administration

- [ ] User admin (invite, update, update_role, suspend, activate, delete)

**Deliverable**: Complete workspace administration

---

### Phase 4: Content Enhancement (Weeks 10-12) - HIGH
**Goal**: Enhance content creation and management

- [ ] Attachments (all 3 endpoints)
- [ ] Documents.import
- [ ] Documents.drafts
- [ ] Comments (update, delete)

**Deliverable**: Full multimedia and import support

---

### Phase 5: Monitoring & Templates (Week 13) - MEDIUM
**Goal**: Add audit logging and templates

- [ ] Events.list
- [ ] Documents.templatize
- [ ] Documents.unpublish

**Deliverable**: Compliance and workflow improvements

---

### Phase 6: Analytics & UX (Week 14) - MEDIUM
**Goal**: Usage tracking and quality-of-life features

- [ ] Views (create, list)
- [ ] Stars (all 4 endpoints)
- [ ] Documents.viewed

**Deliverable**: Better user experience and insights

---

## Category Coverage Summary

| Category | Implemented | Missing | Total | Coverage | Priority |
|----------|-------------|---------|-------|----------|----------|
| **Attachments** | 0 | 3 | 3 | 0% | 🟡 Medium |
| **Auth** | 1 | 1 | 2 | 50% | 🟢 Low |
| **Collections** | 8 | 8 | 16 | 50% | 🔴 High |
| **Comments** | 3 | 2 | 5 | 60% | 🟡 Medium |
| **Documents** | 11 | 8 | 19 | 58% | 🔴 High |
| **Events** | 0 | 1 | 1 | 0% | 🟡 Medium |
| **Groups** | 0 | 8 | 8 | 0% | 🔴 Critical |
| **Revisions** | 0 | 2 | 2 | 0% | 🔴 Critical |
| **Shares** | 0 | 5 | 5 | 0% | 🔴 Critical |
| **Stars** | 0 | 4 | 4 | 0% | 🟢 Low |
| **Users** | 0 | 8 | 8 | 0% | 🔴 Critical |
| **Views** | 0 | 2 | 2 | 0% | 🟡 Medium |
| **File Operations** | 0 | 0 | 4* | N/A | 🟢 Low |
| **TOTAL** | **25** | **46** | **71** | **35%** | - |

*File Operations endpoints are utility endpoints for checking export/import status

---

## Technical Implementation Considerations

### Rate Limiting
- Current implementation ✓ Already supports rate limiting with exponential backoff
- No additional work needed for new endpoints

### Error Handling
- Current pattern: Raise `OutlineError` in client, catch in tools
- Continue using this pattern for consistency

### Pagination
- Many missing endpoints support pagination (limit/offset)
- Implement consistent pagination helper utilities

### Permissions Model
- Need to understand Outline's permission enum: `read`, `read_write`
- Group vs individual permissions
- Collection-level vs document-level access

### Authentication Scopes
- Some endpoints require specific OAuth scopes
- Document scope requirements for each endpoint

### Testing Strategy
- Continue mocking `OutlineClient` in tests
- Add integration tests for permission-related endpoints
- Test cascade behavior (e.g., deleting groups affects memberships)

---

## Business Impact Analysis

### Current Limitations

**For End Users**:
- ❌ Cannot view document history or restore old versions
- ❌ Cannot share documents publicly with external stakeholders
- ❌ Cannot organize users into groups/teams
- ❌ Cannot manage permissions at scale
- ❌ No audit trail for compliance
- ❌ Cannot upload images or attachments
- ❌ Cannot import existing documents

**For Administrators**:
- ❌ No user management (invite, suspend, delete)
- ❌ No role-based access control
- ❌ No audit logging
- ❌ Limited permission management

**For Developers/API Users**:
- ❌ Missing 65% of API surface area
- ❌ Cannot build complete Outline integrations
- ❌ Limited automation capabilities

### Post-Implementation Benefits

**After Critical Priority (Phases 1-2)**:
- ✅ Complete version control with revision history
- ✅ Public document sharing for external collaboration
- ✅ Enterprise-grade permission management
- ✅ User and group administration
- ✅ 70%+ API coverage

**After All Priorities**:
- ✅ 100% API coverage
- ✅ Feature parity with Outline web application
- ✅ Full automation and integration capabilities
- ✅ Compliance-ready (audit logs, access controls)

---

## Next Steps

1. **Review & Prioritize**: Validate priority assignments with stakeholders
2. **Spike Research**:
   - Study Outline's permission model in detail
   - Review attachment upload flow (signed URLs)
   - Understand revision restore behavior
3. **Create Issues**: Break down each phase into GitHub issues
4. **Start with Phase 1**: Begin with revisions and shares (highest impact)
5. **Iterative Delivery**: Ship each phase independently for faster value delivery

---

## References

- **Outline OpenAPI Spec**: https://github.com/outline/openapi
- **Outline API Docs**: https://www.getoutline.com/developers
- **Current Implementation**: `/src/mcp_outline/`
- **This Analysis**: Generated via automated comparison on 2025-11-06

---

## Changelog

- **2025-11-06**: Initial gap analysis covering all 71 API endpoints
