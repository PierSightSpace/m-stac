import pytest
from httpx import AsyncClient
from unittest.mock import Mock


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

    
class TestSearchEndpoints:
    """Test cases for search endpoints"""

    @pytest.mark.asyncio
    async def test_search_all_items(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search all items with all fields"""
        mock_db_session.execute.return_value = FakeResult(test_data)
        response = await async_client.get("/v1/search")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        product = data["products"][0]
        assert product["id"] == "1FN2LK"
        assert product["type"] == "Feature"
        assert product["geom_type"] == "Polygon"
        assert product["bounding_box_wkb"] == {
            "coordinates": [
                [60.700849, -45.604186],
                [64.881107, -45.604186],
                [64.881107, -44.054565],
                [60.700849, -44.054565],
                [60.700849, -45.604186]
            ]
        }
        assert product["beam_mode"] is None
        assert product["browse"] == "s3://piersight-data/ps_sample/PS_V01_GRD_ICE_1FN2LK_20200111T155800Z.png"
        assert product["bytes"] == 0
        assert product["center_lat"] == -44.8293755
        assert product["center_lon"] == 62.790978
        assert product["product_name"] == "PS_V01_GRD_ICE_1FN2LK_20200111T155800Z"
        assert product["product_file"] == "PS_V01_GRD_ICE_1FN2LK_20200111T155800Z.tif"
        assert product["orbit_direction"] == "ASCENDING"
        assert product["md5_sum"] == "d41d8cd98f00b204e9800998ecf8427e"
        assert product["orbit_absolute_number"] == 1092
        assert product["processor_version"] == "3.9"
        assert product["satellite_name"] == "PierSight_V01"
        assert product["polarization"] == "VV"
        assert product["processing_time"] == "2025-06-04T12:57:31"
        assert product["product_level"] == "GRD"
        assert product["acquisition_start_utc"] == "2020-01-11T15:58:00"
        assert product["acquisition_end_utc"] == "2020-01-11T16:02:14"
        assert product["assets"] == "http://localhost:8000/v1/collection/PierSight_V01/items/PS_V01_GRD_ICE_1FN2LK_20200111T155800Z"


    @pytest.mark.asyncio
    async def test_search_with_collection_filter(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search with collection filter"""
        mock_db_session.execute.return_value = FakeResult(test_data)        
        response = await async_client.get("/v1/search?collectionId=PierSight_V01")    
        assert response.status_code == 200
        data = response.json()    
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        assert data["products"][0]["satellite_name"] == "PierSight_V01"

    @pytest.mark.asyncio
    async def test_search_with_bbox_filter(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search with bounding box filter"""
        mock_db_session.execute.return_value = FakeResult(test_data)        
        response = await async_client.get("/v1/search?bbox=0,0,1,1")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1

    @pytest.mark.asyncio
    async def test_search_with_time_filter(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search with time filter"""
        mock_db_session.execute.return_value = FakeResult(test_data)        
        response = await async_client.get("/v1/search?start_time=2024-01-01T00:00:00Z&stop_time=2024-01-31T23:59:59Z")        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search with pagination"""
        mock_db_session.execute.return_value = FakeResult(test_data*3)        
        response = await async_client.get("/v1/search?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        assert len(data["products"]) == 2
        assert data["next"] is not None

    @pytest.mark.asyncio
    async def test_search_no_results(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - No results found"""
        mock_db_session.execute.return_value = FakeResult([])        
        response = await async_client.get("/v1/search")        
        assert response.status_code == 404
        data = response.json()
        assert "No data found" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_invalid_collection(self, async_client: AsyncClient):
        """Test GET /v1/search - Invalid collection ID"""
        response = await async_client.get("/v1/search?collectionId=invalid_collection")        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid collection ID" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_invalid_bbox_format(self, async_client: AsyncClient):
        """Test GET /v1/search - Invalid bounding box format"""
        response = await async_client.get("/v1/search?bbox=invalid,bbox,format")        
        assert response.status_code == 422
        data = response.json()
        assert "Invalid bounding box format" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_invalid_time_range(self, async_client: AsyncClient):
        """Test GET /v1/search - Invalid time range (start > stop)"""
        response = await async_client.get("/v1/search?start_time=2024-12-31T23:59:59Z&stop_time=2024-01-01T00:00:00Z")        
        assert response.status_code == 400
        data = response.json()
        assert "exceeding" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_with_all_filters(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Search with all filters combined"""
        mock_db_session.execute.return_value = FakeResult(test_data)        
        response = await async_client.get(
            "/v1/search?collectionId=PierSight_V01&bbox=0,0,1,1&start_time=2024-01-01T00:00:00Z&stop_time=2024-01-31T23:59:59Z&limit=5&offset=0"
        )        
        assert response.status_code == 200
        data = response.json()        
        assert data["total_count"] == 1
        assert len(data["products"]) == 1

    @pytest.mark.asyncio
    async def test_search_pagination_next_url(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - Pagination next URL generation"""
        mock_db_session.execute.return_value = FakeResult(test_data*2)        
        response = await async_client.get("/v1/search?limit=2&offset=0")        
        assert response.status_code == 200
        data = response.json()        
        assert data["next"] is not None
        assert "limit=2" in data["next"]
        assert "offset=2" in data["next"]

    @pytest.mark.asyncio
    async def test_search_no_pagination_next_url(self, async_client: AsyncClient, mock_db_session):
        """Test GET /v1/search - No next URL when fewer results than limit"""
        mock_db_session.execute.return_value = FakeResult(test_data)        
        response = await async_client.get("/v1/search?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["next"] is None

    @pytest.mark.asyncio
    async def test_search_caching(self, async_client: AsyncClient, mock_db_session):
        """Test that search endpoint is cached"""
        mock_db_session.execute.return_value = FakeResult(test_data)
        response1 = await async_client.get("/v1/search")
        assert response1.status_code == 200
        response2 = await async_client.get("/v1/search")
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_search_response_headers(self, async_client: AsyncClient, mock_db_session):
        """Test response headers for search endpoint"""
        mock_db_session.execute.return_value = FakeResult(test_data)
        response = await async_client.get("/v1/search")
        assert response.status_code == 200
        headers = response.headers
        assert "application/json" in headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_search_database_error(self, async_client: AsyncClient, mock_db_session):
        """Test database error handling in search"""
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        response = await async_client.get("/v1/search")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_search_limit_validation(self, async_client: AsyncClient):
        """Test search limit parameter validation"""
        response = await async_client.get("/v1/search?limit=100")
        assert response.status_code == 422        
        response = await async_client.get("/v1/search?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_offset_validation(self, async_client: AsyncClient):
        """Test search offset parameter validation"""
        response = await async_client.get("/v1/search?offset=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_bbox_validation(self, async_client: AsyncClient):
        """Test search bbox parameter validation"""
        response = await async_client.get("/v1/search?bbox=0,0,1")
        assert response.status_code == 422        
        response = await async_client.get("/v1/search?bbox=0,0,1,1,,2")
        assert response.status_code == 422