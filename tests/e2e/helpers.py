"""Shared helpers for E2E tests."""

import re

import httpx

OUTLINE_URL = "http://localhost:3030"


def _text(result):
    """Extract text from a CallToolResult."""
    return result.content[0].text


def _extract_id(text):
    """Extract an ID from '(ID: <uuid>)' in tool output."""
    m = re.search(r"\(ID: ([^)]+)\)", text)
    assert m, f"No ID found in: {text}"
    return m.group(1)


async def _create_collection(session, name):
    """Create a collection, return its ID."""
    result = await session.call_tool(
        "create_collection",
        arguments={"name": name},
    )
    return _extract_id(_text(result))


async def _create_document(session, coll_id, title, text="Body."):
    """Create a document, return its ID."""
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
    """Create *count* documents, return list of IDs."""
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
    """Upload a file attachment via the Outline API.

    Uses a two-step flow:
    1. POST attachments.create → presigned upload URL + form fields
    2. POST to upload URL with multipart form data

    Returns the attachment ID.
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
