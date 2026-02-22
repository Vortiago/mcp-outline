"""Shared helpers for E2E tests.

Provides two categories of utilities:

- **Result parsing**: ``_text`` and ``_extract_id`` unwrap raw
  ``CallToolResult`` objects into the strings that assertions need.
- **Setup shortcuts**: ``_create_collection``, ``_create_document``,
  ``_create_documents``, and ``_upload_attachment`` reduce boilerplate
  in test bodies. Every test that needs a collection or document calls
  these rather than duplicating ``call_tool`` invocations inline.

``_upload_attachment`` bypasses MCP entirely and calls the Outline REST
API directly — this lets attachment tests seed real uploaded files
without depending on a (non-existent) MCP upload tool.
"""

import re

import httpx

OUTLINE_URL = "http://localhost:3031"


def _text(result):
    """Return the text content of the first item in a CallToolResult."""
    return result.content[0].text


def _extract_id(text):
    """Extract a UUID from an ``(ID: <uuid>)`` pattern in tool output.

    All MCP tools in this server embed the created or affected object's
    ID in their success message using this pattern. Raises ``AssertionError``
    if no match is found, which produces a clear failure message.
    """
    m = re.search(r"\(ID: ([^)]+)\)", text)
    assert m, f"No ID found in: {text}"
    return m.group(1)


async def _create_collection(session, name):
    """Create a collection via MCP and return its ID."""
    result = await session.call_tool(
        "create_collection",
        arguments={"name": name},
    )
    return _extract_id(_text(result))


async def _create_document(session, coll_id, title, text="Body."):
    """Create a document via MCP and return its ID."""
    result = await session.call_tool(
        "create_document",
        arguments={
            "title": title,
            "text": text,
            "collection_id": coll_id,
        },
    )
    return _extract_id(_text(result))


async def _create_documents(session, coll_id, count):
    """Create *count* documents in *coll_id* and return their IDs."""
    ids = []
    for i in range(count):
        doc_id = await _create_document(
            session,
            coll_id,
            title=f"Doc {i}",
            text=f"Content {i}.",
        )
        ids.append(doc_id)
    return ids


def _upload_attachment(
    api_key,
    filename="test.txt",
    content=b"hello from e2e",
    content_type="text/plain",
    document_id=None,
):
    """Upload a file attachment directly via the Outline REST API.

    Bypasses MCP entirely — used to seed real uploaded files for tests
    that exercise the read-only MCP attachment tools without needing an
    MCP upload path.

    Two-step flow:
    1. POST ``attachments.create`` to obtain a presigned upload URL and
       the required form fields.
    2. POST the file to that URL as multipart form data.

    Returns the attachment ID string.

    Guards against: attachment tool tests failing because no real
    attachment was uploaded before the MCP session was opened.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    # Step 1: Create attachment record
    payload = {
        "name": filename,
        "contentType": content_type,
        "size": len(content),
    }
    if document_id:
        payload["documentId"] = document_id
    resp = httpx.post(
        f"{OUTLINE_URL}/api/attachments.create",
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    upload_url = data["uploadUrl"]
    form_fields = data["form"]
    attachment = data["attachment"]

    # Step 2: Upload file to storage
    # For local storage, uploadUrl is a relative path
    if upload_url.startswith("/"):
        upload_url = f"{OUTLINE_URL}{upload_url}"
    resp = httpx.post(
        upload_url,
        headers=headers,
        data=form_fields,
        files={"file": (filename, content, content_type)},
        timeout=30.0,
    )
    resp.raise_for_status()

    return attachment["id"]
