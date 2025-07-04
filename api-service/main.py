# Imports
import time

# Third-Party Imports
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Local Imports
from database.postgre import engine
from models import log_entry as log_model
from models import collection as collection_model
from schemas import catalog
from middlewares.jwt_auth_middleware import JWTAuthMiddleware
from middlewares.logg_middleware import LoggMiddleware
from routers import catalog, collections, search, items


duckdb_conn = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Handles startup and shutdown events:
    - Initializes the database schema on startup.
    - Creates the tables if they do not exist on PostgreSQL.
   
    Parameters:
        app: The FastAPI application instance.
 
    Returns:
        None. Used as a context manager for FastAPI lifespan events.
    '''
    redis_client = redis.from_url("redis://127.0.0.1:6379", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    async with engine.begin() as conn:
        await conn.run_sync(log_model.Base.metadata.create_all)
        await conn.run_sync(collection_model.Base.metadata.create_all)
        print("🏪Database is ready")
    yield
    await engine.dispose()

# OpenAPI Documentation Metadata
tags_metadata = [
    {
        "name": "Catalog",
        "description": "Operations for retrieving STAC catalog information and conformance details.",
    },
    {
        "name": "Collections",
        "description": "Access and manage STAC collections containing satellite imagery data.",
    },
    {
        "name": "Search",
        "description": "Search and filter STAC items based on temporal, spatial, and collection criteria.",
    },
    {
        "name": "Items",
        "description": "Retrieve detailed information about individual STAC items.",
    }
]

app = FastAPI(
    lifespan=lifespan,
    title='STAC APIs',
    description='''
    STAC APIs for PierSight Space Maritime Servilliance Data
    
    ## Features
    - STAC Compliant: Implements STAC API specification version 1.0.0
    - Rate Limiting: Ensure fair usage of the API
    - Caching: Optimized response times through Redis caching
    - Rich Filtering: Search by temporal, spatial and collection parameters.
    - Authentication: Secure access through JWT authentication
    
    ## Rate Limits
    - Default rate limit: 5 requests per minute
    - Cache duration: 1 hour for search results, 24 hours for staic content
    
    ## Authentication
    Most endpoint require JWT authentication. Include the JWT token in the authorization header:
    ```
    Authorization: Bearer <your_token>
    ```
    
    ## Contact
    - Website: https://piersight.space
    ''',
    version='1.0.0',
    openapi_tags=tags_metadata,
    docs_url='/api',
    terms_of_service="https://piersight.space/terms/",
    contact={
        "name": "PierSight API Support",
        "url": "https://piersight.space/support",
        "email": "support@piersight.space",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }    
)

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


############################################################################################################
# Middlewares
############################################################################################################
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["0.0.0.0", "127.0.0.1", "localhost"])   # stac.eodata.piersight.space - Hostname for production
# app.add_middleware(JWTAuthMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={
        "detail": "Rate limit exceeded. Try again later.",
        "type": "RateLimitExceeded",
        "retry_after": getattr(exc, "retry_after", None)
    }
))
# app.add_middleware(LoggMiddleware)
  
############################################################################################################
# API End-Points
############################################################################################################
app.include_router(catalog.router, prefix="/v1", tags=["Catalog"])
app.include_router(collections.router, prefix="/v1", tags=["Collections"])
app.include_router(search.router, prefix="/v1", tags=["Search"])
app.include_router(items.router, prefix="/v1", tags=["Items"])

