"""
Client for interacting with Outline API.

An async client for making requests to the Outline API with connection
pooling and rate limiting.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import httpx


class OutlineError(Exception):
    """Exception for all Outline API errors."""

    pass


class OutlineClient:
    """Async client for Outline API services with connection pooling."""

    # Class-level connection pool shared across all instances
    _client_pool: ClassVar[Optional[httpx.AsyncClient]] = None
    _rate_limit_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(
        self, api_key: Optional[str] = None, api_url: Optional[str] = None
    ):
        """
        Initialize the Outline client.

        Args:
            api_key: Outline API key or from OUTLINE_API_KEY env var.
            api_url: Outline API URL or from OUTLINE_API_URL env var.

        Raises:
            OutlineError: If API key is missing.
        """
        # Load configuration from environment variables if not provided
        self.api_key = api_key or os.getenv("OUTLINE_API_KEY")
        self.api_url = api_url or os.getenv(
            "OUTLINE_API_URL", "https://app.getoutline.com/api"
        )

        # Ensure API key is provided
        if not self.api_key:
            raise OutlineError("Missing API key. Set OUTLINE_API_KEY env var.")

        # Rate limit tracking
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[int] = None

        # Initialize class-level connection pool if not exists
        if OutlineClient._client_pool is None:
            # Configure connection pooling
            max_connections = int(os.getenv("OUTLINE_MAX_CONNECTIONS", "100"))
            max_keepalive = int(os.getenv("OUTLINE_MAX_KEEPALIVE", "20"))
            timeout = float(os.getenv("OUTLINE_TIMEOUT", "30.0"))
            connect_timeout = float(
                os.getenv("OUTLINE_CONNECT_TIMEOUT", "5.0")
            )

            limits = httpx.Limits(
                max_keepalive_connections=max_keepalive,
                max_connections=max_connections,
                keepalive_expiry=30.0,
            )

            timeout_config = httpx.Timeout(
                connect=connect_timeout,
                read=timeout,
                write=10.0,
                pool=5.0,
            )

            OutlineClient._client_pool = httpx.AsyncClient(
                limits=limits,
                timeout=timeout_config,
                follow_redirects=True,
            )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Note: Don't close the shared pool here
        pass

    @classmethod
    async def close_pool(cls):
        """
        Close the shared connection pool.

        Should be called on application shutdown.
        """
        if cls._client_pool:
            await cls._client_pool.aclose()
            cls._client_pool = None

    async def _wait_if_rate_limited(self) -> None:
        """
        Proactively wait if we know we're rate limited.

        Uses stored rate limit headers to sleep until reset time if needed.
        """
        if self._rate_limit_remaining == 0 and self._rate_limit_reset:
            # Calculate wait time until reset
            now = datetime.now().timestamp()
            wait_seconds = max(0, self._rate_limit_reset - now)

            if wait_seconds > 0:
                # Add small buffer to account for clock skew
                await asyncio.sleep(wait_seconds + 0.1)

    def _update_rate_limits(self, response: httpx.Response) -> None:
        """
        Parse and store rate limit headers from API response.

        Args:
            response: The HTTP response object
        """
        if "RateLimit-Remaining" in response.headers:
            self._rate_limit_remaining = int(
                response.headers["RateLimit-Remaining"]
            )

        if "RateLimit-Reset" in response.headers:
            self._rate_limit_reset = int(response.headers["RateLimit-Reset"])

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an async POST request to the Outline API.

        Implements proactive rate limiting by checking stored rate limit
        headers before making requests, with automatic retry on 429.

        Args:
            endpoint: The API endpoint to call.
            data: The request payload.

        Returns:
            The parsed JSON response.

        Raises:
            OutlineError: If the request fails.
        """
        # Proactive: wait if we know we're rate limited (with lock)
        async with self._rate_limit_lock:
            await self._wait_if_rate_limited()

        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self._client_pool is None:
            raise OutlineError("Client pool not initialized")

        try:
            response = await self._client_pool.post(
                url, headers=headers, json=data or {}
            )

            # Update rate limit state from response headers
            self._update_rate_limits(response)

            # Raise exception for 4XX/5XX responses
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited - provide helpful error
                retry_after = e.response.headers.get("Retry-After", "unknown")
                raise OutlineError(
                    f"Rate limited. Retry after: {retry_after} seconds"
                )
            raise OutlineError(
                f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.TimeoutException as e:
            raise OutlineError(f"Request timeout: {str(e)}")
        except httpx.RequestError as e:
            raise OutlineError(f"API request failed: {str(e)}")

    async def auth_info(self) -> Dict[str, Any]:
        """
        Verify authentication and get user information.

        Returns:
            Dict containing user and team information.
        """
        response = await self.post("auth.info")
        return response.get("data", {})

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get a document by ID.

        Args:
            document_id: The document ID.

        Returns:
            Document information.
        """
        response = await self.post("documents.info", {"id": document_id})
        return response.get("data", {})

    async def search_documents(
        self,
        query: str,
        collection_id: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for documents using keywords.

        Args:
            query: Search terms
            collection_id: Optional collection to search within
            limit: Maximum number of results to return (default: 25)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            Dict containing 'data' (list of results) and 'pagination' metadata
        """
        data: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        if collection_id:
            data["collectionId"] = collection_id

        response = await self.post("documents.search", data)
        return response

    async def list_collections(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all available collections.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of collections
        """
        response = await self.post("collections.list", {"limit": limit})
        return response.get("data", [])

    async def get_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        Get a single collection by ID.

        Args:
            collection_id: The collection ID.

        Returns:
            Collection information.
        """
        response = await self.post("collections.info", {"id": collection_id})
        return response.get("data", {})

    async def get_collection_documents(
        self, collection_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get document structure for a collection.

        Args:
            collection_id: The collection ID.

        Returns:
            List of document nodes in the collection.
        """
        response = await self.post(
            "collections.documents", {"id": collection_id}
        )
        return response.get("data", [])

    async def list_documents(
        self, collection_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering.

        Args:
            collection_id: Optional collection to filter by
            limit: Maximum number of results to return

        Returns:
            List of documents
        """
        data: Dict[str, Any] = {"limit": limit}
        if collection_id:
            data["collectionId"] = collection_id

        response = await self.post("documents.list", data)
        return response.get("data", [])

    async def archive_document(self, document_id: str) -> Dict[str, Any]:
        """
        Archive a document by ID.

        Args:
            document_id: The document ID to archive.

        Returns:
            The archived document data.
        """
        response = await self.post("documents.archive", {"id": document_id})
        return response.get("data", {})

    async def unarchive_document(self, document_id: str) -> Dict[str, Any]:
        """
        Unarchive a document by ID.

        Args:
            document_id: The document ID to unarchive.

        Returns:
            The unarchived document data.
        """
        response = await self.post("documents.unarchive", {"id": document_id})
        return response.get("data", {})

    async def list_trash(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        List documents in the trash.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of documents in trash
        """
        response = await self.post(
            "documents.list", {"limit": limit, "deleted": True}
        )
        return response.get("data", [])

    async def restore_document(self, document_id: str) -> Dict[str, Any]:
        """
        Restore a document from trash.

        Args:
            document_id: The document ID to restore.

        Returns:
            The restored document data.
        """
        response = await self.post("documents.restore", {"id": document_id})
        return response.get("data", {})

    async def permanently_delete_document(self, document_id: str) -> bool:
        """
        Permanently delete a document by ID.

        Args:
            document_id: The document ID to permanently delete.

        Returns:
            Success status.
        """
        response = await self.post(
            "documents.delete", {"id": document_id, "permanent": True}
        )
        return response.get("success", False)

    # Collection management methods
    async def create_collection(
        self, name: str, description: str = "", color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new collection.

        Args:
            name: The name of the collection
            description: Optional description for the collection
            color: Optional hex color code for the collection

        Returns:
            The created collection data
        """
        data: Dict[str, Any] = {"name": name, "description": description}

        if color:
            data["color"] = color

        response = await self.post("collections.create", data)
        return response.get("data", {})

    async def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing collection.

        Args:
            collection_id: The ID of the collection to update
            name: Optional new name for the collection
            description: Optional new description
            color: Optional new hex color code

        Returns:
            The updated collection data
        """
        data: Dict[str, Any] = {"id": collection_id}

        if name is not None:
            data["name"] = name

        if description is not None:
            data["description"] = description

        if color is not None:
            data["color"] = color

        response = await self.post("collections.update", data)
        return response.get("data", {})

    async def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection and all its documents.

        Args:
            collection_id: The ID of the collection to delete

        Returns:
            Success status
        """
        response = await self.post("collections.delete", {"id": collection_id})
        return response.get("success", False)

    async def export_collection(
        self, collection_id: str, format: str = "outline-markdown"
    ) -> Dict[str, Any]:
        """
        Export a collection to a file.

        Args:
            collection_id: The ID of the collection to export
            format: The export format (outline-markdown, json, or html)

        Returns:
            FileOperation data that can be queried for progress
        """
        response = await self.post(
            "collections.export", {"id": collection_id, "format": format}
        )
        return response.get("data", {})

    async def export_all_collections(
        self, format: str = "outline-markdown"
    ) -> Dict[str, Any]:
        """
        Export all collections to a file.

        Args:
            format: The export format (outline-markdown, json, or html)

        Returns:
            FileOperation data that can be queried for progress
        """
        response = await self.post(
            "collections.export_all", {"format": format}
        )
        return response.get("data", {})

    async def answer_question(
        self,
        query: str,
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ask a natural language question about document content.

        Args:
            query: The natural language question to answer
            collection_id: Optional collection to search within
            document_id: Optional document to search within

        Returns:
            Dictionary containing AI answer and search results
        """
        data: Dict[str, Any] = {"query": query}

        if collection_id:
            data["collectionId"] = collection_id

        if document_id:
            data["documentId"] = document_id

        response = await self.post("documents.answerQuestion", data)
        return response
