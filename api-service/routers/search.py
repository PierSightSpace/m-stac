# Imports
# Standard Library Imports
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, urlencode

# Third-Party Imports
from fastapi import Depends, HTTPException, Query, Request, APIRouter, status
from fastapi_cache.decorator import cache
from sqlalchemy.engine import Result
from sqlalchemy.sql import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

# Local Imports
from database.postgre import get_db
from schemas import stac
from utils import convert_to_datetime, build_products, serialize_rows, validate_inputs, my_key_builder
from config.settings import LIMIT, OFFSET, COLLECTIONS


router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


@router.get(
    "/search", 
    response_model=stac.StacOutputBase,
    summary="Search STAC Items",
    description="""
    Search for STAC items based on spatial, temporal, and collection criteria.
    
    This endpoint implements the STAC API Item Search specification, allowing clients to:
    - Filter items by collection ID
    - Search within a geographic bounding box
    - Filter by time range
    - Paginate through results
    
    The response is a GeoJSON FeatureCollection containing STAC Items that match the query parameters.
    """,
    response_description="A GeoJSON FeatureCollection of STAC Items matching the search criteria",
    status_code=200,
    responses={
        200: {
            "description": "Successfully retrieved matching STAC items",
            "content": {
                "application/json": {
                    "example": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geom_type": "Polygon",
                                "bounding_box_wkb": {
                                    "coordinates": [[]]
                                },
                                # Other fields
                            }
                        ],
                        "next": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid input parameters.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "acquisition_start_utc: 2023-01-01T00:00:00 is exceeding acquisition_end_utc: 2022-12-31T23:59:59"
                    }
                }
            }
        },
        404: {
            "description": "No data found for the given input.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No data found for given input"
                    }
                }
            }
        },
        422: {
            "description": "Invalid coordinates or time format.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid coordinates; Must be in WKT format"
                    }
                }
            }
        },
        429: {
            "description": "Too many requests",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Try again later."
                    }
                }
            }
        }
    }
)
@cache(expire=3600, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_all_stacs(
    request: Request,
    response : Response,
    collectionId: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None, min_items=4, max_items=6),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=50),
    offset: Optional[int] = Query(OFFSET, ge=0),
    db:AsyncSession = Depends(get_db)
):
    """
    Search for STAC items based on various filtering criteria.

    This endpoint implements the STAC API Item Search specification, allowing filtering
    by collection, spatial extent, and temporal extent. Results are paginated and
    cached for improved performance.

    Args:
        request (Request): The incoming HTTP request
        response (Response): The outgoing HTTP response
        collectionId (str, optional): Filter by specific collection
        bbox (str, optional): Bounding box coordinates (minLon,minLat,maxLon,maxLat)
        start_time (str, optional): Start of temporal filter (ISO 8601)
        stop_time (str, optional): End of temporal filter (ISO 8601)
        limit (int, optional): Maximum number of items to return (default: 10)
        offset (int, optional): Number of items to skip (default: 0)
        db (AsyncSession): Database session dependency

    Returns:
        StacOutputBase: A GeoJSON FeatureCollection containing matching STAC Items
                       and pagination links

    Raises:
        HTTPException: 
            - 400: Invalid parameters (e.g., invalid time range)
            - 404: No matching items found
            - 422: Invalid parameter format
    """
    if collectionId and collectionId not in COLLECTIONS:                  
        raise HTTPException(status_code=400, detail=f"Invalid collection ID. Must be one of: {', '.join(COLLECTIONS)}")

    if bbox:
        try:
            bbox = [float(x) for x in bbox.split(",")]
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid bounding box format. Must be comma-separated numbers.")
        
    validate_inputs(bbox, start_time, stop_time)
    
    if start_time and stop_time: 
        if start_time > stop_time:
            raise HTTPException(status_code=400, detail=f"acquisition_start_utc: {start_time} is exceeding acquisition_end_utc: {stop_time}")
        else:
            start_time = convert_to_datetime(start_time)
            stop_time = convert_to_datetime(stop_time)
    
    
    collectionId_query = "SELECT * FROM piersight_stac.stac WHERE TRUE"
    params = {}
    if collectionId:
        collectionId_query += " AND satellite_name = :collectionId"
        params = {"collectionId": collectionId}
    
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox[:4]
        collectionId_query += (" AND ST_Intersects(ST_GeomFromWKB(decode(bounding_box_wkb, 'hex'), 4326),ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326))")
        params["min_lon"] = min_lon
        params["max_lon"] = max_lon
        params["min_lat"] = min_lat        
        params["max_lat"] = max_lat

    if start_time and stop_time:
        collectionId_query += " AND acquisition_start_utc >= :start_time AND acquisition_end_utc <= :stop_time ORDER BY acquisition_start_utc"
        params["start_time"] = start_time
        params["stop_time"] = stop_time
                
    if limit:
        collectionId_query += " LIMIT :limit"
        params["limit"] = limit
    if offset:
        collectionId_query += " OFFSET :offset"
        params["offset"] = offset

    result: Result = await db.execute(sql_text(collectionId_query), params)
    keys = result.keys()
    rows = result.fetchall()
    data = serialize_rows(rows, keys)
                    
    if not data:
        raise HTTPException(status_code=404, detail="No data found matching the search criteria")
    
    products = [build_products(stac_obj) for stac_obj in data]
    next_url = None
    if len(products) == limit:
        parsed_url = urlparse(str(request.url))
        params = parse_qs(parsed_url.query)
        if not params:
            params = {}
        if bbox:
            params['bbox'] = [str(bbox)]   
        if start_time and stop_time:
            params['start_time'] = [str(start_time)]
            params['stop_time'] = [str(stop_time)]  
        if limit:
            params['limit'] = [str(limit)]
        if offset:
            params['offset'] = [str(limit+offset)]
        else:
            params['offset'] = [str(limit)]
        
        base_url = parsed_url._replace(query="") 
        next_url = base_url.geturl() + "?" + urlencode(params, doseq=True)
            
    return stac.StacOutputBase(total_count=len(products), products=products, next=next_url)