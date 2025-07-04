import pytest
from httpx import AsyncClient
from unittest.mock import patch


class TestCatalogEndpoints:
    """Test cases for catalog endpoints"""

    @pytest.mark.asyncio
    async def test_get_catalog_root(self, async_client: AsyncClient):
        """Test GET /v1/ - Root catalog endpoint"""
        response = await async_client.get("/v1/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["type"] == "Catalog"
        assert data["id"] == "PierSight Space Maritime Servilliance Data"
        assert data["title"] == "PierSight Catalog"
        assert data["stac_version"] == "1.0.0"
        assert "links" in data
        assert "stac_extensions" in data
        
        links = data["links"]
        assert any(link["rel"] == "self" for link in links)
        assert any(link["rel"] == "root" for link in links)
        assert any(link["rel"] == "service-desc" for link in links)
        assert any(link["rel"] == "service-doc" for link in links)
        assert any(link["rel"] == "conformance" for link in links)
        assert any(link["rel"] == "data" for link in links)
        assert any(link["rel"] == "search" for link in links)
        
        child_links = [link for link in links if link["rel"] == "child"]
        assert len(child_links) == 32 

    @pytest.mark.asyncio
    async def test_get_conformance(self, async_client: AsyncClient):
        """Test GET /v1/conformance - Conformance endpoint"""
        response = await async_client.get("/v1/conformance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "conformsTo" in data
        conforms_to = data["conformsTo"]
        
        assert "https://api.stacspec.org/v1.0.0/core" in conforms_to
        assert "https://api.stacspec.org/v1.0.0/collections" in conforms_to
        assert "https://api.stacspec.org/v1.0.0/search" in conforms_to
        
        assert "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core" in conforms_to
        assert "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30" in conforms_to
        assert "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html" in conforms_to
        assert "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson" in conforms_to

    @pytest.mark.asyncio
    async def test_catalog_caching(self, async_client: AsyncClient):
        """Test that catalog endpoints are cached"""
        response1 = await async_client.get("/v1/")
        assert response1.status_code == 200
        
        response2 = await async_client.get("/v1/")
        assert response2.status_code == 200
        
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_conformance_caching(self, async_client: AsyncClient):
        """Test that conformance endpoint is cached"""
        response1 = await async_client.get("/v1/conformance")
        assert response1.status_code == 200
        
        response2 = await async_client.get("/v1/conformance")
        assert response2.status_code == 200
        
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_catalog_response_headers(self, async_client: AsyncClient):
        """Test response headers for catalog endpoints"""
        response = await async_client.get("/v1/")
        
        assert response.status_code == 200
        headers = response.headers
        
        assert "application/json" in headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_conformance_response_headers(self, async_client: AsyncClient):
        """Test response headers for conformance endpoint"""
        response = await async_client.get("/v1/conformance")
        
        assert response.status_code == 200
        headers = response.headers
        
        assert "application/json" in headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_catalog_links_validation(self, async_client: AsyncClient):
        """Test that catalog links are properly formatted"""
        response = await async_client.get("/v1/")
        
        assert response.status_code == 200
        data = response.json()
        links = data["links"]
        
        for link in links:
            assert "rel" in link
            assert "href" in link
            assert isinstance(link["rel"], str)
            assert isinstance(link["href"], str)
            assert link["href"].startswith("http")

    @pytest.mark.asyncio
    async def test_child_collections_exist(self, async_client: AsyncClient):
        """Test that all child collection links point to valid collections"""
        response = await async_client.get("/v1/")
        
        assert response.status_code == 200
        data = response.json()
        links = data["links"]
        
        child_links = [link for link in links if link["rel"] == "child"]
        
        assert len(child_links) == 32
        
        for link in child_links:
            assert "title" in link
            assert link["title"].startswith("PierSight-V")

    @pytest.mark.asyncio
    async def test_catalog_description_content(self, async_client: AsyncClient):
        """Test that catalog description contains expected content"""
        response = await async_client.get("/v1/")
        
        assert response.status_code == 200
        data = response.json()
        description = data["description"]
        
        assert "PierSight" in description
        assert "SAR" in description
        assert "maritime" in description
        assert "satellite" in description 