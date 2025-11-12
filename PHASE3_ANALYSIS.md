# Critical Analysis: Phase 3.1 & 3.2 Feature Proposals

## Executive Summary

After researching production MCP servers (GitHub, Filesystem, etc.) and MCP design patterns, many Phase 3.1 and 3.2 proposals are **inappropriate for an MCP server**. This analysis identifies which features align with MCP best practices and which should be rejected.

---

## MCP Server Design Principles (from research)

1. **Automation-focused** - Enable AI to complete workflows, not replicate UI features
2. **Single clear purpose** - Don't try to expose every API endpoint
3. **Manage tool budget** - Too many tools increases complexity and cost
4. **Design around workflows** - Not API coverage for coverage's sake
5. **Avoid user-specific metadata** - LLMs work on content, not personal preferences

### Examples from Production Servers

**GitHub MCP Server:**
- ✅ Core workflows: search, read issues/PRs, create/update, CI/CD monitoring
- ❌ Does NOT expose: user profile settings, notification preferences, starring repos

**Filesystem MCP Server:**
- ✅ Core operations: read, write, search, directory operations
- ❌ Does NOT expose: file ownership changes, permission management, user preferences

---

## Phase 3.1: Document Features Analysis

### ✅ SHOULD IMPLEMENT

#### 1. Templates
```
- list_document_templates
- create_document_from_template
```

**Rationale:**
- ✅ Core workflow enabler
- ✅ Common use case: "Create a meeting notes document"
- ✅ Reduces boilerplate for AI
- ✅ Similar to GitHub MCP's template support

**Priority: HIGH**

---

#### 2. Search Pagination
```
- Add offset/limit to search_documents
```

**Rationale:**
- ✅ Essential for large workspaces
- ✅ Prevents truncated results
- ✅ Standard pattern in all MCP servers
- ✅ Low complexity

**Priority: CRITICAL** (should already exist)

---

### ⚠️ CONSIDER CAREFULLY

#### 3. Revision History (Read-Only)
```
- get_document_revisions (✅ maybe)
- get_document_revision (✅ maybe)
- restore_document_revision (❌ NO)
```

**Pros:**
- Could help with context: "What changed in last version?"
- Useful for auditing/understanding edits

**Cons:**
- Adds tool budget complexity
- LLM rarely needs version history
- Restoration is high-risk operation (requires manual decision)

**Recommendation:**
- ✅ Implement read-only tools if there's a clear workflow
- ❌ Do NOT implement `restore_document_revision` - too risky, too manual
- Consider as Phase 4/5 (low priority)

---

#### 4. File Attachments
```
- upload_attachment
- list_attachments
- download_attachment
- delete_attachment
```

**Pros:**
- Could enable workflows like "Attach this CSV to the report"
- Completes document management picture

**Cons:**
- **Binary file handling is complex in MCP** (base64 encoding)
- Unclear how LLM would effectively use this
- File operations might be better handled by Filesystem MCP
- Increases token usage significantly
- Security concerns with arbitrary file uploads

**Recommendation:**
- ❌ Do NOT implement in Phase 3
- Maybe explore in Phase 5 with clear use cases
- Filesystem MCP + Outline MCP coordination might be better pattern

---

### ❌ SHOULD NOT IMPLEMENT

#### 5. Favorites/Stars
```
- star_document
- unstar_document
- list_starred_documents
```

**Problems:**
- **Personal metadata, not content** - Stars are user preferences, not document data
- **LLM shouldn't manage user preferences** - "Should I star this doc?" makes no sense
- **No clear workflow** - When would AI star a document?
- **Wrong abstraction** - Stars are UI affordances, not API primitives

**Real-World Analogy:**
GitHub MCP does NOT expose starring repos because it's personal metadata.

**Recommendation:** ❌ **REJECT** - Remove from TODO entirely

---

## Phase 3.2: Collaboration Features Analysis

### ⚠️ CONSIDER CAREFULLY (Read-Only Only)

#### 1. Activity Tracking (Read-Only)
```
- get_document_viewers (⚠️ maybe)
- get_document_editors (⚠️ maybe)
- get_document_activity (⚠️ maybe)
```

**Pros:**
- Could provide context: "Who's been working on this?"
- Useful for understanding document ownership
- Read-only, low risk

**Cons:**
- Privacy implications (tracking users)
- Potentially high token usage for activity logs
- Unclear workflow benefit
- Most users don't need AI to tell them who edited what

**Recommendation:**
- Consider `get_document_editors` only - for ownership context
- Skip viewers/activity - information overload
- Phase 4/5 priority (low)

---

### ❌ SHOULD NOT IMPLEMENT

#### 2. Sharing & Permissions
```
- create_share_link
- revoke_share_link
- list_document_shares
```

**Problems:**
- **HIGH security risk** - LLM managing access control is dangerous
- **User should control sharing** - "AI, share this publicly" is scary
- **Permission-sensitive** - Wrong abstraction for automation
- **No clear workflow** - Sharing is deliberate human decision

**Real-World Example:**
No MCP server exposes permission/sharing management because it's too sensitive.

**Recommendation:** ❌ **REJECT** - Remove entirely

---

#### 3. User Mentions
```
- mention_user_in_comment
```

**Problems:**
- **Already supported** - Comments take markdown text with @mentions
- **No separate tool needed** - Just format comment text properly
- **Over-engineering** - LLM can write "@username" in comment text

**Recommendation:** ❌ **REJECT** - Already possible via existing comment tools

---

#### 4. Subscriptions
```
- subscribe_to_document
- unsubscribe_from_document
- list_subscriptions
```

**Problems:**
- **Personal notification preferences** - Not content, metadata
- **LLM shouldn't manage notifications** - "Should I subscribe?" makes no sense
- **User-specific** - Outside scope of document automation
- **No workflow** - When would AI subscribe user to notifications?

**Real-World Analogy:**
GitHub MCP does NOT expose subscription management.

**Recommendation:** ❌ **REJECT** - Remove entirely

---

## Summary Table

| Feature | Verdict | Priority | Reason |
|---------|---------|----------|--------|
| **3.1 Templates** | ✅ YES | HIGH | Core workflow |
| **3.1 Search Pagination** | ✅ YES | CRITICAL | Essential |
| **3.1 Revision History (read)** | ⚠️ MAYBE | LOW | Marginal value |
| **3.1 Revision History (restore)** | ❌ NO | - | Too risky |
| **3.1 Favorites/Stars** | ❌ NO | - | Personal metadata |
| **3.1 File Attachments** | ❌ NO | - | Too complex, unclear benefit |
| **3.2 Sharing & Permissions** | ❌ NO | - | Security risk |
| **3.2 User Mentions** | ❌ NO | - | Already supported |
| **3.2 Subscriptions** | ❌ NO | - | Personal metadata |
| **3.2 Activity Tracking** | ⚠️ MAYBE | LOW | Marginal value |

---

## Recommended TODO.md Changes

### Phase 3.1 - Revised

```markdown
### 3.1 Document Features
**Status**: Not Started

- [ ] **Templates** (HIGH PRIORITY):
  - [ ] Add tool: `list_document_templates`
  - [ ] Add tool: `create_document_from_template`
  - [ ] Add OutlineClient methods
  - [ ] Add tests

- [ ] **Search Pagination** (CRITICAL - should already exist):
  - [ ] Add `offset` and `limit` parameters to `search_documents`
  - [ ] Update OutlineClient.search_documents() to support pagination
  - [ ] Update formatter to show "Showing X-Y of Z results"
  - [ ] Add tests

- [ ] **Revision History - Read Only** (LOW PRIORITY - Phase 4/5):
  - [ ] Add tool: `get_document_revisions` - List versions with metadata
  - [ ] Add tool: `get_document_revision` - Retrieve specific version content
  - [ ] Add OutlineClient methods
  - [ ] Add tests
  - ❌ Do NOT implement `restore_document_revision` - too risky for automation

**Removed (Not Appropriate for MCP):**
- ❌ Favorites/Stars - Personal metadata, not content operations
- ❌ File Attachments - Complex binary handling, unclear LLM workflow benefit
```

### Phase 3.2 - Revised

```markdown
### 3.2 Collaboration Features
**Status**: Not Started

- [ ] **Activity Context - Read Only** (LOW PRIORITY - Phase 4/5):
  - [ ] Add tool: `get_document_editors` - Recent editors for ownership context
  - [ ] Add OutlineClient method
  - [ ] Add tests
  - Note: Only implement if clear workflow emerges

**Removed (Not Appropriate for MCP):**
- ❌ Sharing & Permissions - Security-sensitive, user should control manually
- ❌ User Mentions - Already supported in comment text with @username
- ❌ Subscriptions - Personal notification preferences, not content operations
- ❌ Document Viewers/Activity Logs - Information overload, privacy concerns
```

---

## Key Principles Applied

1. **Content operations, not metadata** - MCP servers work on content (docs, code), not user preferences (stars, subscriptions)

2. **Security through permissions, not abstraction** - Sharing/permissions should be handled by API key scopes, not exposed to LLM

3. **Clear workflows only** - If you can't articulate a specific workflow where the LLM uses the tool, don't implement it

4. **Avoid UI feature replication** - Just because Outline's UI has a feature doesn't mean the MCP server needs it

5. **Token budget management** - Every tool added increases prompt size and LLM decision complexity

---

## Conclusion

**Original proposal: 12 feature groups**
**Recommended: 2 high-priority + 2 low-priority**

**Rejected: 8 feature groups** that are either:
- Personal metadata (stars, subscriptions)
- Security-sensitive (sharing/permissions)
- Already supported (mentions)
- Overcomplicated (attachments)
- Low workflow value (activity tracking)

This aligns the server with production MCP patterns and focuses on **content automation**, not **UI feature parity**.
