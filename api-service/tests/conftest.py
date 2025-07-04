import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import redis.asyncio as redis

# Import your app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch FastAPI cache globally before anything else is imported
patcher_init = patch("fastapi_cache.FastAPICache.init", return_value=None)
patcher_prefix = patch("fastapi_cache.FastAPICache.get_prefix", return_value="test-prefix")
patcher_cache = patch("fastapi_cache.decorator.cache", side_effect=lambda *a, **kw: lambda f: f)
patcher_coder = patch("fastapi_cache.FastAPICache.get_coder", return_value=None)
patcher_init.start()
patcher_prefix.start()
patcher_cache.start()
patcher_coder.start()

try:
    from main import app
    from database.postgre import get_db
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

@pytest.fixture
def test_app():
    """Test app instance"""
    return app

@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client():
    """Async test client"""
    try:
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
            yield ac
    except Exception as e:
        print(f"Error creating async client: {e}")
        raise

class FakeResult:
    def __init__(self, all_value=None, scalar_one_or_none_value=None):
        self._all_value = all_value or []
        self._scalar_one_or_none_value = scalar_one_or_none_value
    def scalars(self):
        class FakeScalarResult:
            def __init__(self, all_value):
                self._all_value = all_value
            def all(self):
                return self._all_value
        return FakeScalarResult(self._all_value)
    def fetchall(self):
        return self._all_value
    def keys(self):
        return [
            'id', 'type', 'geom_type', 'bounding_box_wkb', 'browse', 'bytes',
            'center_lat', 'center_lon', 'product_name', 'product_file',
            'orbit_direction', 'md5_sum', 'orbit_absolute_number',
            'processor_version', 'satellite_name', 'polarization',
            'processing_time', 'product_level', 'acquisition_start_utc',
            'acquisition_end_utc', 'assets'
        ]
    def scalar_one_or_none(self):
        return self._scalar_one_or_none_value

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = FakeResult()
    return mock_session

@pytest.fixture(autouse=True)
def mock_redis_and_cache():
    """Mock Redis and FastAPI cache for all tests"""
    with patch('fastapi_cache.FastAPICache.init') as mock_init:
        with patch('redis.asyncio.from_url') as mock_redis:
            with patch('fastapi_cache.decorator.cache') as mock_cache:
                mock_cache.side_effect = lambda *args, **kwargs: lambda func: func
                yield mock_redis

@pytest.fixture
def mock_s3_client():
    """Mock S3 client"""
    with patch('boto3.client') as mock_client:
        yield mock_client

@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing"""
    return {
        "id": "test_collection",
        "type": "Collection",
        "stac_version": "1.0.0",
        "title": "Test Collection",
        "description": "A test collection for unit testing",
        "license": "proprietary",
        "extent": {
            "spatial": {
                "bbox": [[-180, -90, 180, 90]]
            },
            "temporal": {
                "interval": [["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]]
            }
        },
        "links": [
            {
                "rel": "self",
                "href": "https://test.com/collections/test_collection"
            }
        ],
        "providers": [
            {
                "name": "Test Provider",
                "url": "https://test.com"
            }
        ]
    }

@pytest.fixture
def sample_stac_item_data():
    """Sample STAC item data for testing"""
    return {
        "id": "test_item_001",
        "type": "Feature",
        "geom_type": "Polygon",
        "bounding_box_wkb": {
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        "satellite_name": "PierSight_V01",
        "product_name": "test_item_001",
        "acquisition_start_utc": "2024-01-01T00:00:00Z",
        "acquisition_end_utc": "2024-01-01T00:01:00Z"
    }

@pytest.fixture(autouse=True)
def override_db_dependency(mock_db_session):
    """
    Before every test, override FastAPI’s get_db to return the test’s mock_db_session.
    """
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield
    app.dependency_overrides.pop(get_db, None)
    
async def override_get_db():
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
                'id', 'type', 'geom_type', 'bounding_box_wkb', 'browse', 'bytes',
                'center_lat', 'center_lon', 'product_name', 'product_file',
                'orbit_direction', 'md5_sum', 'orbit_absolute_number',
                'processor_version', 'satellite_name', 'polarization',
                'processing_time', 'product_level', 'acquisition_start_utc',
                'acquisition_end_utc', 'assets'
            ]
        def scalar_one_or_none(self):
            return self._scalar_one_or_none_value
        
    mock_session = AsyncMock()
    mock_session.execute.return_value = FakeResult()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = AsyncMock()
    yield mock_session

    app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def clear_redis():
    """Clear Redis database before each test to reset rate limiter state"""
    try:
        client = redis.from_url("redis://127.0.0.1:6379", encoding="utf8", decode_responses=True)
        await client.flushdb()
        await client.close()
    except Exception as e:
        print(f"Warning: Could not clear Redis: {e}")
    yield