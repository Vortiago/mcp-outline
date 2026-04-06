# Plan: Read the Database Layer Section from "Platform Architecture Overview"

This plan follows the skill's recommended "Find and read a specific section" workflow, which is the optimal approach for reading a single section from a large document. Using the TOC-then-section strategy avoids loading the entire document into context.

## Tool Call Sequence

### Step 1: Find the document ID by title

**Tool:** `get_document_id_from_title`
**Arguments:**
```
query: "Platform Architecture Overview"
```

**Rationale:** Since we know the exact document title, `get_document_id_from_title` is the most direct way to get the document ID. It returns just the ID, which is all we need for subsequent calls.

### Step 2: Inspect the document's heading structure

**Tool:** `get_document_toc`
**Arguments:**
```
doc_id: <document_id from Step 1>
```

**Rationale:** The document is described as "really long," so we should not load it in full. The TOC reveals all headings and their hierarchy, letting us identify the exact heading name for the database layer section. The heading might be called "Database Layer", "Database Architecture", "Data Layer", or something similar -- we need to see the actual TOC to know.

### Step 3: Read the specific database layer section

**Tool:** `read_document_section`
**Arguments:**
```
doc_id: <document_id from Step 1>
heading: "<exact heading text from TOC, e.g. 'Database Layer'>"
```

**Rationale:** `read_document_section` extracts only the content under the specified heading (including any sub-headings), avoiding the need to load the entire large document. The exact heading value used here must match what the TOC returned in Step 2.

## Summary

This three-step plan (title lookup, TOC inspection, section read) follows the skill's recommended pattern for navigating large documents. It minimizes context token usage by never loading the full document body, and it handles the ambiguity of the exact heading name by consulting the TOC before requesting the section.
