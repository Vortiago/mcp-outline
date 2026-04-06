# Exploration Plan: Authentication and Authorization Documentation

## Task

"What does our wiki say about authentication and authorization? I need to understand what's documented about our auth system."

**Thoroughness level:** medium

---

## Step 1: Orient (parallel calls)

Launch two calls simultaneously to understand the knowledge base and find relevant documents.

### Call 1a: `list_collections`

**Arguments:** none

**Why:** The agent instructions say to always start with `list_collections` to understand the knowledge base structure. This helps identify which collections might contain auth-related docs (e.g., an "Engineering" or "Security" collection) and guides follow-up browsing in Step 3.

### Call 1b: `search_documents`

**Arguments:** `query: "authentication authorization"`

**Why:** `search_documents` is the fastest way to find relevant content. Using both terms in one query covers the core topic. Running this in parallel with `list_collections` saves a round trip.

**Assumed results (per the task):**
1. "Authentication Architecture" (id: `doc-auth-arch`, 450 lines)
2. "API Security Guide" (id: `doc-api-sec`, 200 lines)
3. "SSO Integration Setup" (id: `doc-sso`, 120 lines)
4. "User Permissions Model" (id: `doc-perms`, 80 lines)

---

## Step 2: Second search with alternate terms

### Call 2: `search_documents`

**Arguments:** `query: "SSO OAuth login access control"`

**Why:** Medium thoroughness calls for 2-3 search queries with different terms. The first search used "authentication authorization"; this second search uses synonyms and related concepts (SSO, OAuth, login, access control) to catch documents that might use different terminology. This may surface additional results that the first query missed.

---

## Step 3: Browse relevant collection structure

### Call 3: `get_collection_structure`

**Arguments:** `collection_id: <id of the most relevant collection from Step 1a, e.g. "Security" or "Engineering">`

**Why:** Medium thoroughness includes browsing relevant collection structures. Documents about auth may exist in a collection but not match keyword searches (e.g., a "Security Overview" doc that covers auth as a subsection). Browsing the collection tree reveals documents organized near the search hits.

---

## Step 4: Read documents (using TOC-first strategy)

This is where the reading strategy matters most. The four documents vary in size, and the agent instructions are clear: use `get_document_toc` first, then `read_document_section` for targeted reading, reserving full reads for small documents.

### Call 4a (parallel, all four documents): `get_document_toc`

**Documents:**
- `get_document_toc(document_id: "doc-auth-arch")`
- `get_document_toc(document_id: "doc-api-sec")`
- `get_document_toc(document_id: "doc-sso")`
- `get_document_toc(document_id: "doc-perms")`

**Why TOC first for all four:** Even for the smallest doc (80 lines), the TOC gives heading structure and line numbers, letting me decide which sections are relevant before committing context tokens to reading content. For the large 450-line doc, this is essential -- reading all 450 lines would consume context unnecessarily when only certain sections may be relevant.

**Why parallel:** These four calls are independent. Running them in parallel saves three round trips.

---

## Step 5: Targeted section reading

Based on the TOC results, read specific sections. The strategy differs by document size:

### "Authentication Architecture" (450 lines) -- Section reads only

**Tool:** `read_document_section`

**Example calls (depending on TOC headings):**
- `read_document_section(document_id: "doc-auth-arch", heading: "Overview")`
- `read_document_section(document_id: "doc-auth-arch", heading: "Authentication Flow")`
- `read_document_section(document_id: "doc-auth-arch", heading: "Token Management")`
- `read_document_section(document_id: "doc-auth-arch", heading: "Authorization Model")`

**Why `read_document_section` instead of `read_document`:** At 450 lines, this is the largest document. Reading it fully would consume significant context. The TOC from Step 4 reveals which sections are relevant to "auth system understanding." Sections like "Changelog" or "Appendix" can be skipped entirely. This is the primary use case for section-based reading.

**Why not `read_document` with offset/limit:** Section reading by heading name is semantically precise -- I get exactly "the Authentication Flow section" rather than guessing line ranges. `offset`/`limit` is better when I need a specific line range that does not align with headings.

### "API Security Guide" (200 lines) -- Section reads

**Tool:** `read_document_section`

**Example calls:**
- `read_document_section(document_id: "doc-api-sec", heading: "API Authentication")`
- `read_document_section(document_id: "doc-api-sec", heading: "Rate Limiting and Keys")`

**Why section reads:** At 200 lines, this document is mid-sized. Parts of it (e.g., CORS configuration, input validation) may not be relevant to auth. The TOC lets me pick only auth-related sections.

### "SSO Integration Setup" (120 lines) -- Section reads or full read

**Tool:** `read_document_section` for 2-3 key sections, OR `read_document` (full) if the TOC shows the entire document is auth-relevant.

**Why this might warrant a full read:** At 120 lines, the document is small enough that a full read is acceptable if most sections are relevant. The decision depends on the TOC: if 4 out of 5 sections are relevant, reading the full document in one call is more efficient than 4 separate section reads.

### "User Permissions Model" (80 lines) -- Full read

**Tool:** `read_document` (no offset/limit)

**Example call:** `read_document(document_id: "doc-perms")`

**Why full read:** At 80 lines, this is the smallest document and entirely on-topic (permissions are core to authorization). Reading the full document is the most efficient approach -- one call instead of multiple section reads. The TOC from Step 4 already confirmed its structure, so there are no surprises.

### Parallelism in Step 5

All section reads across different documents are independent and can run in parallel. For example, if I need 4 sections from "Authentication Architecture" and 2 from "API Security Guide" plus the full read of "User Permissions Model," all 7 calls can be dispatched simultaneously.

---

## Step 6: Follow backlinks on the primary document

### Call 6: `get_document_backlinks`

**Arguments:** `document_id: "doc-auth-arch"`

**Why:** The "Authentication Architecture" doc is the central auth document. Backlinks reveal which other documents reference it -- there may be runbooks, onboarding guides, or incident postmortems that link back to the auth architecture and contain additional useful context. Medium thoroughness warrants checking backlinks on the most important document (but not all four).

**Why only for `doc-auth-arch`:** Checking backlinks on all four documents would be "very thorough" level. For medium, one backlink check on the primary document is sufficient.

---

## Step 7: Synthesize and respond

Combine findings from all documents into a structured answer:

- Summarize the authentication architecture (from doc-auth-arch)
- Note API-specific auth mechanisms (from doc-api-sec)
- Outline SSO integration details (from doc-sso)
- Describe the permissions/authorization model (from doc-perms)
- Mention any related documents found via backlinks
- Cite all document titles as sources
- Flag any gaps (e.g., "No documentation found on MFA/2FA" or "Mobile auth flow is not covered")

---

## Decision Summary: When to use each reading tool

| Tool | When to use | Example in this plan |
|------|-------------|---------------------|
| `get_document_toc` | Always first, for every document, regardless of size. Gives heading structure and line numbers. | All 4 documents in Step 4 |
| `read_document_section` | For medium and large documents where only some sections are relevant. Preferred default. | "Authentication Architecture" (450 lines), "API Security Guide" (200 lines) |
| `read_document` (full) | For small documents (under ~100 lines) where most content is relevant. | "User Permissions Model" (80 lines) |
| `read_document` (offset/limit) | When you need a specific line range that does not align with a heading, or when section reading is unavailable. | Not needed in this plan, but would use if TOC showed a relevant block spanning parts of two sections. |

## Total estimated tool calls

| Step | Calls | Tools |
|------|-------|-------|
| 1 (Orient) | 2 (parallel) | `list_collections` + `search_documents` |
| 2 (Second search) | 1 | `search_documents` |
| 3 (Browse) | 1 | `get_collection_structure` |
| 4 (TOC) | 4 (parallel) | `get_document_toc` x4 |
| 5 (Read) | ~7 (parallel) | `read_document_section` x5-6 + `read_document` x1 |
| 6 (Backlinks) | 1 | `get_document_backlinks` |
| **Total** | **~16 calls in 6 round trips** | |
