# Imports
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

# Swagger UI Metadata
tags_metadata = [
    {
        "name": "STAC APIs",
        "description": "Endpoints for accessing STAC data, including collections",
    }
]

app = FastAPI(
    lifespan=lifespan,
    title='STAC APIs',
    description='STAC APIs for PierSight Space Maritime Servilliance Data',
    version='1.0.0',
    openapi_tags=tags_metadata,
    docs_url='/api',    
)
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

############################################################################################################
# Middlewares
############################################################################################################
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])   # stac.eodata.piersight.space - Hostname for production
# app.add_middleware(JWTAuthMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded. Try again later."}
))
app.add_middleware(LoggMiddleware)

  
############################################################################################################
# API End-Points
############################################################################################################
app.include_router(catalog.router, tags=["Catalog"])
app.include_router(collections.router, tags=["Collections"])
app.include_router(search.router, tags=["Search"])
app.include_router(items.router, tags=["Items"])

