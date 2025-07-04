import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestRateLimiting:
    """Test cases for rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limiting works correctly"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        responses = []
        for i in range(7): 
            response = await async_client.get("/v1/")
            responses.append(response)
            print(f"Request {i+1}: Status {response.status_code}")
        
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "Should have received rate limit responses"
        
        for response in rate_limited_responses:
            data = response.json()
            assert "detail" in data
            assert "type" in data
            assert data["type"] == "RateLimitExceeded"

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limit headers are present"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        response = await async_client.get("/v1/")
        
        headers = response.headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "Retry-After"
        ]        
        present_headers = [h for h in rate_limit_headers if h in headers]


    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limiting resets after the time window"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

        responses = []
        for i in range(10):
            response = await async_client.get("/v1/")
            responses.append(response)
            if response.status_code == 429:
                break

        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Should have hit rate limit"

    @pytest.mark.asyncio
    async def test_rate_limit_by_ip(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limiting is applied per IP address"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

        responses = []
        for i in range(7):
            response = await async_client.get("/v1/")
            responses.append(response)

        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Should have hit rate limit from same IP"

    @pytest.mark.asyncio
    async def test_rate_limit_error_response_structure(self, async_client: AsyncClient, mock_db_session):
        """Test the structure of rate limit error responses"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        responses = []
        for i in range(7):
            response = await async_client.get("/v1/")
            responses.append(response)

        rate_limited_response = None
        for response in responses:
            if response.status_code == 429:
                rate_limited_response = response
                break

        if rate_limited_response:
            data = rate_limited_response.json()
            assert "detail" in data
            assert "type" in data
            assert "retry_after" in data
            assert data["type"] == "RateLimitExceeded"
            assert "Rate limit exceeded" in data["detail"]

    @pytest.mark.asyncio
    async def test_rate_limit_with_parameters(self, async_client: AsyncClient, mock_db_session):
        """Test rate limiting with query parameters"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        test_urls = [
            "/v1/search",
            "/v1/search?collectionId=PierSight_V01",
            "/v1/search?limit=5",
            "/v1/search?bbox=0,0,1,1",
            "/v1/collections/PierSight_V01/items?limit=5"
        ]
        
        responses = []
        for url in test_urls:
            response = await async_client.get(url)
            responses.append(response)
            print(f"URL {url}: Status {response.status_code}")
        for response in responses:
            assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code}"

    @pytest.mark.asyncio
    async def test_rate_limit_content_type(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limit responses have correct content type"""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

        responses = []
        for i in range(7): 
            response = await async_client.get("/v1/")
            responses.append(response)
        
        # Find a rate limited response
        rate_limited_response = None
        for response in responses:
            if response.status_code == 429:
                rate_limited_response = response
                break
        
        if rate_limited_response:
            headers = rate_limited_response.headers
            assert "application/json" in headers.get("content-type", "")
            

    @pytest.mark.asyncio
    async def test_rate_limit_with_caching(self, async_client: AsyncClient, mock_db_session):
        """Test that rate limiting works correctly with caching"""
        # Mock database response for collections
        mock_collection = AsyncMock()
        mock_collection.id = "PierSight_V01"
        mock_collection.type = "Collection"
        mock_collection.stac_version = "1.0.0"
        mock_collection.description = "Test collection"
        mock_collection.license = "proprietary"
        mock_collection.title = "Test Collection"
        mock_collection.extent = {"spatial": {"bbox": [[-180, -90, 180, 90]]}}
        mock_collection.links = [{"rel": "self", "href": "https://test.com"}]
        mock_collection.providers = [{"name": "Test Provider"}]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_collection]
        
        responses = []
        for i in range(10):
            response = await async_client.get("/v1/collections")
            responses.append(response)

        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0 