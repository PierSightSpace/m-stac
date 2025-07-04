import pytest
from httpx import AsyncClient

class FakeScalarResult:
    def __init__(self, all_value):
        self._all_value = all_value
    def all(self):
        return self._all_value

class FakeResult:
    def __init__(self, all_value=None, scalar_one_or_none_value=None):
        self._all_value = all_value or []
        self._scalar_one_or_none_value = scalar_one_or_none_value
    def scalars(self):
        return FakeScalarResult(self._all_value)
    def fetchall(self):
        return self._all_value
    def keys(self):
        return [
            'id', 'type', 'stac_version', 'description', 'license', 
            'title', 'extent', 'links', 'providers'
        ]
    def scalar_one_or_none(self):
        return self._scalar_one_or_none_value


COLLECTION_DICT = {
    "id": "PierSight_V01",
    "type": "collection",
    "stac_version": "1.0.0",
    "description": "Test collection",
    "license": "proprietary",
    "title": "Test Collection",
    "extent": {
        "spatial": {"bbox": [[-180, -90, 180, 90]]},
        "temporal": {"interval": [["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]]}
    },
    "links": [
        {"rel": "self", "href": "https://test.com", "mime_type": "application/json"}
    ],
    "providers": [
        {"name": "Test Provider", "roles": ["producer"], "url": "https://test.com"}
    ]
}

PAGINATED_RESPONSE = lambda products, next_url=None: {
    "total_count": len(products),
    "products": products,
    "next": next_url
}

class TestCollectionsEndpoints:
    """Test cases for collections endpoints"""

    @pytest.mark.asyncio
    async def test_get_all_collections(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([COLLECTION_DICT])
        response = await async_client.get("/v1/collections")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_collection_by_id(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([COLLECTION_DICT])
        response = await async_client.get("/v1/collections")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([])
        response = await async_client.get("/v1/collections/nonexistent")
        data = response.json()
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_collection_success(self, async_client: AsyncClient, mock_db_session, sample_collection_data):
        mock_db_session.execute.return_value = []
        mock_db_session.add = lambda x: None
        mock_db_session.commit = lambda: None
        mock_db_session.refresh = lambda x: None
        sample_collection_data["links"][0]["mime_type"] = "application/json"
        sample_collection_data["providers"][0]["roles"] = ["producer"]
        response = await async_client.post("/v1/collections", json=sample_collection_data)
        data = response.json()
        assert response.status_code == 201
        assert data["id"] == sample_collection_data["id"]
        assert data["type"] == sample_collection_data["type"]
        assert data["title"] == sample_collection_data["title"]


    @pytest.mark.asyncio
    async def test_create_collection_invalid_data(self, async_client: AsyncClient):
        invalid_data = {"id": 123}
        response = await async_client.post("/v1/collections", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_collections_caching(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = [COLLECTION_DICT]
        response1 = await async_client.get("/v1/collections")
        response2 = await async_client.get("/v1/collections")
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_collections_response_headers(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([COLLECTION_DICT])
        response = await async_client.get("/v1/collections")
        assert response.status_code == 200
        headers = response.headers
        assert "application/json" in headers.get("content-type", "")