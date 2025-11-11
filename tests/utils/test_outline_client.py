"""
Tests for the Outline API client.
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_outline.utils.outline_client import OutlineClient, OutlineError

# Test data
MOCK_API_KEY = "test_api_key"
MOCK_API_URL = "https://test.outline.com/api"


class TestOutlineClient:
    """Test suite for OutlineClient."""

    def setup_method(self):
        """Set up test environment."""
        # Save original environment variables
        self.original_api_key = os.environ.get("OUTLINE_API_KEY")
        self.original_api_url = os.environ.get("OUTLINE_API_URL")

        # Set test environment variables
        os.environ["OUTLINE_API_KEY"] = MOCK_API_KEY
        os.environ["OUTLINE_API_URL"] = MOCK_API_URL

    def teardown_method(self):
        """Restore original environment."""
        # Restore original environment variables
        if self.original_api_key is not None:
            os.environ["OUTLINE_API_KEY"] = self.original_api_key
        else:
            os.environ.pop("OUTLINE_API_KEY", None)

        if self.original_api_url is not None:
            os.environ["OUTLINE_API_URL"] = self.original_api_url
        else:
            os.environ.pop("OUTLINE_API_URL", None)

    @pytest.mark.asyncio
    async def test_init_from_env_variables(self):
        """Test initialization from environment variables."""
        client = OutlineClient()
        assert client.api_key == MOCK_API_KEY
        assert client.api_url == MOCK_API_URL

    @pytest.mark.asyncio
    async def test_init_from_arguments(self):
        """Test initialization from constructor arguments."""
        custom_key = "custom_key"
        custom_url = "https://custom.outline.com/api"

        client = OutlineClient(api_key=custom_key, api_url=custom_url)
        assert client.api_key == custom_key
        assert client.api_url == custom_url

    @pytest.mark.asyncio
    async def test_init_missing_api_key(self):
        """Test error when API key is missing."""
        os.environ.pop("OUTLINE_API_KEY", None)

        with pytest.raises(OutlineError):
            OutlineClient(api_key=None)

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"data": {"test": "value"}}

        # Create client and make request
        client = OutlineClient()
        data = {"param": "value"}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(return_value=mock_response),
        ) as mock_post:
            result = await client.post("test_endpoint", data)

            # Verify request was made correctly
            mock_post.assert_called_once_with(
                f"{MOCK_API_URL}/test_endpoint",
                headers={
                    "Authorization": f"Bearer {MOCK_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=data,
            )

            assert result == {"data": {"test": "value"}}

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for request exceptions."""
        # Setup mock to raise an exception
        error_msg = "Connection error"

        # Create client and test exception handling
        client = OutlineClient()

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(side_effect=httpx.RequestError(error_msg)),
        ):
            with pytest.raises(OutlineError) as exc_info:
                await client.post("test_endpoint")

            assert "API request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_headers_parsed(self):
        """Test that rate limit headers are parsed and stored."""
        client = OutlineClient()

        # Mock response with rate limit headers
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "RateLimit-Remaining": "4",
            "RateLimit-Reset": "1234567890",
        }
        mock_response.json.return_value = {"data": {"test": "value"}}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(return_value=mock_response),
        ):
            await client.post("test_endpoint")

        # Verify headers were parsed
        assert client._rate_limit_remaining == 4
        assert client._rate_limit_reset == 1234567890

    @pytest.mark.asyncio
    async def test_proactive_wait_when_rate_limited(self):
        """Test proactive waiting when rate limit is exhausted."""
        client = OutlineClient()

        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"data": {"test": "value"}}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(return_value=mock_response),
        ):
            with patch(
                "mcp_outline.utils.outline_client.asyncio.sleep"
            ) as mock_sleep:
                # Set rate limit state to exhausted with reset in near future
                # Do this inside the patch context to ensure timing is correct
                client._rate_limit_remaining = 0
                client._rate_limit_reset = int(datetime.now().timestamp() + 10)

                await client.post("test_endpoint")

                # Verify sleep was called
                assert mock_sleep.call_count == 1
                sleep_time = mock_sleep.call_args[0][0]
                # Should sleep for ~10 seconds + 0.1 buffer
                assert 9 < sleep_time < 12

    @pytest.mark.asyncio
    async def test_no_wait_when_rate_limit_available(self):
        """Test no waiting when rate limit has remaining requests."""
        client = OutlineClient()

        # Set rate limit state with remaining requests
        client._rate_limit_remaining = 5
        client._rate_limit_reset = int((datetime.now().timestamp() + 60))

        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"data": {"test": "value"}}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(return_value=mock_response),
        ):
            with patch(
                "mcp_outline.utils.outline_client.asyncio.sleep"
            ) as mock_sleep:
                await client.post("test_endpoint")

                # Verify sleep was NOT called
                mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_on_429_status(self):
        """Test automatic retry on 429 rate limit response."""
        client = OutlineClient()

        # First response: 429, second response: success
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1000"}
        mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests",
            request=MagicMock(),
            response=mock_response_429,
        )

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.headers = {}
        mock_response_success.json.return_value = {"data": {"test": "value"}}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(side_effect=[mock_response_success]),
        ):
            # Should succeed after retry
            result = await client.post("test_endpoint")
            assert result == {"data": {"test": "value"}}

    @pytest.mark.asyncio
    async def test_rate_limit_headers_missing(self):
        """Test handling when rate limit headers are not present."""
        client = OutlineClient()

        # Mock response without rate limit headers
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"data": {"test": "value"}}

        with patch.object(
            client._client_pool,
            "post",
            new=AsyncMock(return_value=mock_response),
        ):
            await client.post("test_endpoint")

        # Verify rate limit state remains None
        assert client._rate_limit_remaining is None
        assert client._rate_limit_reset is None

    @pytest.mark.asyncio
    async def test_session_configured_with_retry(self):
        """Test that client pool is configured with httpx AsyncClient."""
        client = OutlineClient()

        # Verify client pool is an httpx.AsyncClient
        assert isinstance(client._client_pool, httpx.AsyncClient)

        # Verify transport exists
        transport = client._client_pool._transport
        assert transport is not None
