"""
Client for interacting with Outline API.

A simple client for making requests to the Outline API.
"""
import os
import requests
from typing import Any, Dict, Optional, List, Union

class OutlineError(Exception):
    """Exception for all Outline API errors."""
    pass

class OutlineClient:
    """Simple client for Outline API services."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_url: Optional[str] = None
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
        self.api_url = api_url or os.getenv("OUTLINE_API_URL", "https://app.getoutline.com/api")
        
        # Ensure API key is provided
        if not self.api_key:
            raise OutlineError("Missing API key. Set OUTLINE_API_KEY env var.")
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to the Outline API.
        
        Args:
            endpoint: The API endpoint to call.
            data: The request payload.
            
        Returns:
            The parsed JSON response.
            
        Raises:
            OutlineError: If the request fails.
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data or {})
            # Raise exception for 4XX/5XX responses
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OutlineError(f"API request failed: {str(e)}")
    
    def auth_info(self) -> Dict[str, Any]:
        """
        Verify authentication and get user information.
        
        Returns:
            Dict containing user and team information.
        """
        response = self.post("auth.info")
        return response.get("data", {})
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID.
            
        Returns:
            Document information.
        """
        response = self.post("documents.info", {"id": document_id})
        return response.get("data", {})
    
    def search_documents(
        self, 
        query: str, 
        collection_id: Optional[str] = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using keywords.
        
        Args:
            query: Search terms
            collection_id: Optional collection to search within
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with context
        """
        data: Dict[str, Any] = {"query": query, "limit": limit}
        if collection_id:
            data["collectionId"] = collection_id
            
        response = self.post("documents.search", data)
        return response.get("data", [])
    
    def list_collections(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all available collections.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of collections
        """
        response = self.post("collections.list", {"limit": limit})
        return response.get("data", [])
    
    def get_collection_documents(self, collection_id: str) -> List[Dict[str, Any]]:
        """
        Get document structure for a collection.
        
        Args:
            collection_id: The collection ID.
            
        Returns:
            List of document nodes in the collection.
        """
        response = self.post("collections.documents", {"id": collection_id})
        return response.get("data", [])
    
    def list_documents(
        self, 
        collection_id: Optional[str] = None, 
        limit: int = 20
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
            
        response = self.post("documents.list", data)
        return response.get("data", [])
