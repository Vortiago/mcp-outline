# Exploration Plan: Authentication and Authorization Documentation

## Thoroughness Level: Medium

Medium thoroughness calls for 2-3 search queries with different terms, browsing relevant
collection structures, and reading up to 5 documents.

---

## Step 1: Orient (parallel calls)

The agent instructions say to ALWAYS start by calling `list_collections` and
`search_documents` in parallel. Two tool calls fire simultaneously:

### Call 1a -- list_collections

```
tool: list_collections
args: (none)
```

**Why this tool:** The agent instructions mandate starting with `list_collections` to
understand the knowledge base structure. This reveals which collections exist (e.g.,
"Engineering", "Security", "Operations") so we can later browse the most relevant ones
for auth-related documents that keyword search might miss.

### Call 1b -- search_documents (first query)

```
tool: search_documents
args: { query: "authentication authorization" }
```

**Why this tool and these args:** `search_documents` is the primary discovery tool.
Using both "authentication" and "authorization" in a single query casts a wide net
across the two core concepts the user asked about. This is preferred over `read_document`
(we don't have document IDs yet) and over `get_collection_structure` (we haven't
identified the right collection yet).

**Assumed result:** 4 documents returned:

| Title                        | ID            | Lines |
|------------------------------|---------------|-------|
| Authentication Architecture  | doc-auth-arch | 450   |
| API Security Guide           | doc-api-sec   | 200   |
| SSO Integration Setup        | doc-sso       | 120   |
| User Permissions Model       | doc-perms     | 80    |

---

## Step 2: Search (second query, medium thoroughness)

Medium thoroughness requires 2-3 search queries with varied terms. After the first
search returns results, fire a second search with a synonym/related term:

### Call 2 -- search_documents (second query)

```
tool: search_documents
args: { query: "SSO OAuth login" }
```

**Why different terms:** The first query covers the broad concepts. This second query
targets specific auth mechanisms (SSO, OAuth, login flows) that might surface documents
the first search missed -- for example, an "OAuth2 Configuration" doc that doesn't
contain the word "authentication" prominently.

---

## Step 3: Browse collection structure

Based on `list_collections` results, identify the collection most likely to house
security/auth documentation (e.g., a "Security" or "Engineering" collection) and
browse its structure:

### Call 3 -- get_collection_structure

```
tool: get_collection_structure
args: { collection_id: "<id of Security or Engineering collection>" }
```

**Why this tool:** Collection browsing finds documents organized under auth-related
sections that may not rank highly in keyword search -- for example, a "Role-Based
Access Control" sub-page nested under a parent document. This complements keyword
search with structural discovery.

---

## Step 4: Read documents (parallel calls)

Now read the most relevant documents. Reading strategy:

- **Prioritize by relevance to the user's question.** "Authentication Architecture"
  and "User Permissions Model" map directly to "authentication" and "authorization"
  respectively.
- **Read all four search results** since medium thoroughness allows up to 5 documents
  and all four are directly relevant.
- **Read full documents** rather than relying on search snippets, per agent
  instructions ("Prefer reading full documents over relying on search snippets").

All four reads can fire in parallel since they are independent:

### Call 4a -- read_document (highest priority)

```
tool: read_document
args: { id: "doc-auth-arch" }
```

**Why first:** At 450 lines, "Authentication Architecture" is the most comprehensive
document and most directly answers "what's documented about our auth system." It likely
covers the overall auth design, flows, and technical decisions.

**Reading strategy for 450 lines:** Read the full document. Even at 450 lines this is
well within tool output limits. Scan for: auth flow diagrams, supported auth methods,
token lifecycle, session management, integration points.

### Call 4b -- read_document

```
tool: read_document
args: { id: "doc-perms" }
```

**Why:** "User Permissions Model" directly addresses the "authorization" half of the
user's question. At 80 lines it is concise and likely contains the role/permission
definitions.

**Reading strategy for 80 lines:** Read fully. Look for: role definitions, permission
levels, access control rules, how permissions are assigned.

### Call 4c -- read_document

```
tool: read_document
args: { id: "doc-api-sec" }
```

**Why:** "API Security Guide" likely covers how auth is applied at the API layer --
API keys, token validation, rate limiting tied to auth. This bridges authentication
concepts with practical API usage.

**Reading strategy for 200 lines:** Read fully. Focus on: API authentication methods,
header-based auth, token formats, security headers.

### Call 4d -- read_document

```
tool: read_document
args: { id: "doc-sso" }
```

**Why:** "SSO Integration Setup" covers a specific auth mechanism the org uses.
At 120 lines it is focused and practical.

**Reading strategy for 120 lines:** Read fully. Look for: supported SSO providers,
SAML/OIDC configuration, provisioning, troubleshooting.

---

## Step 5: Follow backlinks on the key document

For medium thoroughness, check backlinks on the most central document to discover
related content:

### Call 5 -- get_document_backlinks

```
tool: get_document_backlinks
args: { document_id: "doc-auth-arch" }
```

**Why this document:** "Authentication Architecture" is the most central auth document.
Other documents that link to it are likely auth-adjacent (e.g., "Deployment Security
Checklist", "New Developer Onboarding") and could contain additional auth context the
user would find valuable. If any backlinks look highly relevant and we haven't read
them yet, read up to 1 more document (staying within the 5-document budget).

---

## Step 6: Synthesize

Combine findings from all documents read into a structured answer:

1. **Authentication overview** -- from "Authentication Architecture"
2. **Authorization / permissions model** -- from "User Permissions Model"
3. **API-level auth** -- from "API Security Guide"
4. **SSO specifics** -- from "SSO Integration Setup"
5. **Related documents** -- mention any relevant backlinks found

Cite each document by title as a source. Flag if any area seems under-documented
or if the search may have missed content in collections that were not browsed.

---

## Tool Call Summary

| Order | Tool                      | Args                                          | Parallel? |
|-------|---------------------------|-----------------------------------------------|-----------|
| 1a    | list_collections          | (none)                                        | Yes (with 1b) |
| 1b    | search_documents          | query: "authentication authorization"         | Yes (with 1a) |
| 2     | search_documents          | query: "SSO OAuth login"                      | No (after 1) |
| 3     | get_collection_structure  | collection_id: (from step 1a)                 | No (after 1a) |
| 4a    | read_document             | id: "doc-auth-arch"                           | Yes (with 4b-4d) |
| 4b    | read_document             | id: "doc-perms"                               | Yes (with 4a,4c,4d) |
| 4c    | read_document             | id: "doc-api-sec"                             | Yes (with 4a,4b,4d) |
| 4d    | read_document             | id: "doc-sso"                                 | Yes (with 4a-4c) |
| 5     | get_document_backlinks    | document_id: "doc-auth-arch"                  | No (after 4a) |

**Total parallel rounds:** 4 (orient, second search + browse, read all docs, backlinks)

**Documents read:** 4 (with room for 1 more from backlinks if relevant)

## Key Design Decisions

1. **Why read all 4 documents instead of just 2-3:** All four are directly relevant to
   the auth topic. The user asked broadly about "authentication and authorization,"
   which spans architecture, API security, SSO, and permissions. Skipping any would
   leave a gap in the answer.

2. **Why full reads instead of partial reads:** The agent instructions say to prefer
   full documents over search snippets. None of these documents are excessively long
   (the largest is 450 lines), so full reads are practical and avoid missing important
   details buried in the middle or end of documents.

3. **Why backlinks only on doc-auth-arch:** It is the most central/architectural
   document, so other documents are most likely to reference it. Checking backlinks on
   all four documents would exceed medium thoroughness and yield diminishing returns.

4. **Why two search queries rather than three:** "authentication authorization" and
   "SSO OAuth login" together cover both the abstract concepts and the concrete
   mechanisms. A third query (e.g., "RBAC roles permissions") could be added for
   very thorough mode, but medium thoroughness keeps it efficient.
