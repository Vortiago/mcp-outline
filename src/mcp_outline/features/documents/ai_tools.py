"""
AI-powered tools for interacting with documents.

This module provides MCP tools for AI-powered features in Outline.
"""

from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.response_handler import create_tool_response


def _format_ai_answer(response: Dict[str, Any]) -> str:
    """Format AI answer into readable text."""
    # Check if the search field exists (indicates AI answer is available)
    if "search" not in response:
        return (
            "AI answering is not enabled for this workspace or "
            "no relevant information was found."
        )

    search = response.get("search", {})
    answer = search.get("answer", "")

    if not answer:
        return "No answer was found for your question."

    # Format the answer
    output = "# AI Answer\n\n"
    output += f"{answer}\n\n"

    # Add source documents
    documents = response.get("documents", [])
    if documents:
        output += "## Sources\n\n"
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled")
            doc_id = doc.get("id", "")
            output += f"{i}. {title} (ID: {doc_id})\n"

    return output


def register_tools(mcp) -> None:
    """
    Register AI tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, openWorldHint=True, idempotentHint=False
        )
    )
    async def ask_ai_about_documents(
        question: str,
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> CallToolResult:
        """
        Queries document content using natural language questions.

        Use this tool when you need to:
        - Find specific information across multiple documents
        - Get direct answers to questions about document content
        - Extract insights from your knowledge base
        - Answer questions like "What is our vacation policy?"
        - Answer "How do we onboard new clients?" and similar queries

        Args:
            question: The natural language question to ask
            collection_id: Optional collection to limit the search to
            document_id: Optional document to limit the search to

        Returns:
            AI-generated answer based on document content with sources
        """
        try:
            client = await get_outline_client()
            response = await client.answer_question(
                question, collection_id, document_id
            )

            # Extract structured data for the response
            search = response.get("search", {})
            answer = search.get("answer", "")
            documents = response.get("documents", [])

            # Build sources list for structured output
            sources: List[Dict[str, str]] = []
            for doc in documents:
                sources.append(
                    {
                        "document_id": doc.get("id", ""),
                        "title": doc.get("title", "Untitled"),
                    }
                )

            return create_tool_response(
                _format_ai_answer(response),
                {
                    "answer": answer,
                    "sources": sources,
                    "question": question,
                    "collection_id": collection_id,
                    "document_id": document_id,
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error getting answer: {str(e)}",
                {"error": str(e), "question": question},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "question": question},
            )
