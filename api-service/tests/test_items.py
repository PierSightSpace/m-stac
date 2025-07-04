import pytest
from httpx import AsyncClient
from main import app


test_data = [
    (
        "1FN2LK", "Feature", "Polygon",
        "010300000001000000050000009737876BB5594E40BC5983F755CD46C0B5519D0E64385040BC5983F755CD46C0B5519D0E64385040CC4065FCFB0646C09737876BB5594E40CC4065FCFB0646C09737876BB5594E40BC5983F755CD46C0",
        None,
        "s3://piersight-data/ps_sample/PS_V01_GRD_ICE_1FN2LK_20200111T155800Z.png",
        0,
        -44.8293755,
        62.790978,
        "PS_V01_GRD_ICE_1FN2LK_20200111T155800Z",
        "PS_V01_GRD_ICE_1FN2LK_20200111T155800Z.tif",
        "ASCENDING",
        "d41d8cd98f00b204e9800998ecf8427e",
        1092,
        "3.9",
        "PierSight_V01",
        "VV",
        "2025-06-04T12:57:31",
        "GRD",
        "2020-01-11T15:58:00",
        "2020-01-11T16:02:14",
        "http://localhost:8000/v1/collection/PierSight_V01/items/PS_V01_GRD_ICE_1FN2LK_20200111T155800Z"
    ),
]


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
            'id', 'type', 'geom_type', 'bounding_box_wkb', 'beam_mode', 'browse', 
            'bytes', 'center_lat', 'center_lon', 'product_name', 'product_file',
            'orbit_direction', 'md5_sum', 'orbit_absolute_number', 'processor_version', 
            'satellite_name', 'polarization', 'processing_time', 'product_level', 
            'acquisition_start_utc', 'acquisition_end_utc', 'assets'
        ]
    def scalar_one_or_none(self):
        return self._scalar_one_or_none_value
    
    
class TestItemsEndpoints:
    """Test cases for items endpoints"""

    @pytest.mark.asyncio
    async def test_get_collection_items(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult(test_data*2)
        response = await async_client.get("/v1/collections/PierSight_V01/items")
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "products" in data
        assert "next" in data
        assert data["total_count"] == 2
        assert len(data["products"]) == 2
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_collection_items_with_filters(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult(test_data)
        response = await async_client.get(
            "/v1/collections/PierSight_V01/items?bbox=0,0,1,1&start_time=2024-01-01T00:00:00Z&stop_time=2024-01-31T23:59:59Z&limit=5&offset=0"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_collection_items_invalid_collection(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/invalid_collection/items")
        assert response.status_code == 400
        data = response.json()
        assert "Invalid satellite" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_collection_items_no_results(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([])
        response = await async_client.get("/v1/collections/PierSight_V01/items")
        assert response.status_code == 404
        data = response.json()
        assert "No data found" in data["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_collection_items_invalid_bbox(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/PierSight_V01/items?bbox=invalid,bbox,format")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_collection_items_invalid_time_range(self, async_client: AsyncClient):
        response = await async_client.get(
            "/v1/collections/PierSight_V01/items?start_time=2024-12-31T23:59:59Z&stop_time=2024-01-01T00:00:00Z"
        )
        assert response.status_code == 400
        data = response.json()
        assert "exceeding" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_specific_item(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult(test_data)
        response = await async_client.get("/v1/collections/PierSight_V01/items/PS_V01_GRD_ICE_1FN2LK_20200111T155800Z")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        assert data["products"][0]["id"] == "1FN2LK"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_specific_item_not_found(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult([])
        response = await async_client.get("/v1/collections/PierSight_V01/items/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "No item" in data["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_specific_item_invalid_collection(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/invalid_collection/items/item1")
        assert response.status_code == 400
        data = response.json()
        assert "Invalid satellite" in data["detail"]

    @pytest.mark.asyncio
    async def test_items_database_error(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        with pytest.raises(Exception, match="Database connection failed"):
            await async_client.get("/v1/collections/PierSight_V01/items")

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_items_limit_validation(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/PierSight_V01/items?limit=20")
        assert response.status_code == 422
        response = await async_client.get("/v1/collections/PierSight_V01/items?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_items_offset_validation(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/PierSight_V01/items?offset=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_items_bbox_validation(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/PierSight_V01/items?bbox=0,0,1")
        assert response.status_code == 422
        response = await async_client.get("/v1/collections/PierSight_V01/items?bbox=0,0,1,1,2")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_items_time_validation(self, async_client: AsyncClient):
        response = await async_client.get("/v1/collections/PierSight_V01/items?start_time=invalid-time")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_items_pagination_next_url(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult(test_data*4)
        response = await async_client.get("/v1/collections/PierSight_V01/items?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        print(data)
        assert data["next"] is not None
        assert "limit=1" in data["next"]
        assert "offset=1" in data["next"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_items_no_pagination_next_url(self, async_client: AsyncClient, mock_db_session):
        mock_db_session.execute.return_value = FakeResult(test_data)
        response = await async_client.get("/v1/collections/PierSight_V01/items?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        print(data)
        assert data["next"] is None
        app.dependency_overrides.clear() 