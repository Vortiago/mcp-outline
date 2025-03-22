"""
Common utilities for document outline features.

This module provides shared functionality used by both tools and resources.
"""
import os
from mcp_outline.utils.outline_client import OutlineClient, OutlineError

class OutlineClientError(Exception):
    """Exception raised for errors in document outline client operations."""
    pass

def get_outline_client() -> OutlineClient:
    """
    Get the document outline client.
    
    Returns:
        OutlineClient instance
        
    Raises:
        OutlineClientError: If client creation fails
    """
    try:
        # Get API credentials from environment variables
        api_key = os.getenv("OUTLINE_API_KEY")
        api_url = os.getenv("OUTLINE_API_URL")
        
        # Create an instance of the outline client
        client = OutlineClient(api_key=api_key, api_url=api_url)
        
        # Test the connection by attempting to get auth info
        auth_info = client.auth_info()
        user_name = auth_info.get('user', {}).get('name', 'Unknown')
        
        return client
    except OutlineError as e:
        raise OutlineClientError(f"Outline client error: {str(e)}")
    except Exception as e:
        raise OutlineClientError(f"Unexpected error: {str(e)}")
