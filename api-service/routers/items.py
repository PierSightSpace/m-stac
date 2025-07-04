# Imports
# Standard Library Imports
import os
import os
from typing import Optional

# Third-Party Imports
from fastapi import Depends, HTTPException, Query, Request, APIRouter
from fastapi_cache.decorator import cache
from sqlalchemy.engine import Result
from sqlalchemy.sql import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response, StreamingResponse
from urllib.parse import urlparse, parse_qs, urlencode
from slowapi import Limiter
from slowapi.util import get_remote_address
import boto3
from botocore.exceptions import ClientError
import boto3
from botocore.exceptions import ClientError

# Local Imports
from dotenv import load_dotenv
from database.postgre import get_db
from schemas import stac
from utils import convert_to_datetime, build_products, serialize_rows, validate_inputs, my_key_builder
from config.settings import LIMIT, OFFSET, COLLECTIONS


load_dotenv()

S3_BUCKET = os.getenv('S3_BUCKET')
S3_PREFIX = os.getenv('S3_PREFIX')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


@router.get(
    "/collections/{collectionId}/items",
    response_model=stac.StacOutputBase,
    summary="All STAC Items",
    description="Retrieves all STAC items from the database with optional filters.",
    tags=["Items"],
    responses={
        200: {
            "description": "A paginated response containing STAC items.",
            "content": {
                "application/json": {
                    "example": {
                        "total_count": 100,
                        "products": [
                            {
                                "id": "item1",
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
                        "detail": "start_time: 2023-01-01T00:00:00 is exceeding stop_time: 2022-12-31T23:59:59"
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
        }
    }
)
@cache(expire=3600, key_builder=my_key_builder)
@limiter.limit("15/minute")
async def get_satellite_stac_data(
    request: Request,
    response : Response,
    collectionId: str,
    bbox: Optional[str] = Query(None, min_items=4, max_items=6),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=15),
    offset: Optional[int] = Query(OFFSET, ge=0),
    db:AsyncSession = Depends(get_db)
):
    """
    Retrieves STAC items filtered by satellites a.k.a collectionId.

    Parameters:
        request: The incoming HTTP request object.
        bbox: Bounding box [minLon, minLat, maxLon, maxLat].
        start_time: Start time filter in ISO 8601 string format.
        stop_time: Stop time filter in ISO 8601 string format.
        limit: Limit on the number of items per page.
        offset: Offset for pagination.
        db: The database session dependency.

    Returns:
        JSONResponse: A paginated response containing STAC items for the specified collectionId.

    Raises:
        HTTPException: If the collectionId is invalid or no data is found.
    """
    
    if collectionId not in COLLECTIONS:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")

    if bbox:
        bbox_values = bbox.split(",")
        bbox = []
        for x in bbox_values:
            try:
                bbox.append(float(x))
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid bbox value; must be a float.")
        
    validate_inputs(bbox, start_time, stop_time)
    
    if start_time and stop_time: 
        if start_time > stop_time:
            raise HTTPException(status_code=400, detail=f"acquisition_start_utc: {start_time} is exceeding acquisition_end_utc: {stop_time}")
        else:
            start_time = convert_to_datetime(start_time)
            stop_time = convert_to_datetime(stop_time)
    
    
    collectionId_query = "SELECT * FROM stac_metadata.stac WHERE satellite_name = :collectionId"
    params = {
        "collectionId": collectionId
    }
    
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
        raise HTTPException(status_code=404, detail=f"No data found for the satellite: {collectionId}")
    
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


@router.get(
    "/collections/{collectionId}/items/{itemId}", 
    response_model=stac.StacOutputBase,
    summary=" STAC Items",
    description="Retrieves all STAC items from the database with optional filters.",
    tags=["Items"],
    responses={
        200: {
            "description": "A paginated response containing STAC items.",
            "content": {
                "application/geo+json": {
                    "example": {
                        "total_count": 100,
                        "products": [
                            {
                                "id": "item1",
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
            "description": "Invalid satellite.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid satellite"
                    }
                }
            }
        },
        404: {
            "description": "No item found for satellite.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No item found for satellite."
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
        }
    }
)
@cache(expire=3600, key_builder=my_key_builder)
@limiter.limit("15/minute")
async def get_stac_item(
    request: Request,
    response : Response,
    collectionId: str,
    itemId: str,
    db:AsyncSession = Depends(get_db)
):
    if collectionId not in COLLECTIONS:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")
    
    itemId_query = "SELECT * FROM piersight_stac.stac WHERE satellite_name = :collectionId AND product_name = :itemId"
    params = {
        "collectionId": collectionId,
        "itemId": itemId
    }
    
    result: Result = await db.execute(sql_text(itemId_query), params)
    keys = result.keys()
    rows = result.fetchall()
    data = serialize_rows(rows, keys)
        
    if not data:
        raise HTTPException(status_code=404, detail=f"No item: {itemId} found for the satellite: {collectionId}")
    
    products = [build_products(stac_obj) for stac_obj in data]
    return stac.StacOutputBase(total_count=len(products), products=products)


@router.get(
    "/collections/{collectionId}/items/{itemId}/download",
    summary="Download STAC Item Asset",
    description="Downloads the complete asset package for a given STAC item.",
    tags=["Items"],
    responses={
        200: {
            "description": "The ZIP file containing the item's assets.",
            "content": {
                "application/zip": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            },
        },
        400: {
            "description": "Invalid collection ID provided."
        },
        403: {
            "description": "Insufficient permissions to access the asset."
        },
        404: {
            "description": "The requested asset was not found."
        },
        500: {
            "description": "A server-side error occurred while accessing the asset."
        }
    }
)
@limiter.limit("15/minute")
async def download_stac_item_zip(
    request: Request,
    response: Response,
    collectionId: str,
    itemId: str,
):
    if collectionId not in COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid collection: {collectionId}")
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    try:
        key = f"{S3_PREFIX}/{itemId}.zip"
        s3_response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        error_code = e.response.get("Error",{}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"The requested asset for item '{itemId}' does not exist.")
        elif error_code == "AccessDenied":
            raise HTTPException(status_code=403, detail="Insufficient permissions to access the asset.")
        else:
            raise HTTPException(status_code=500, detail="A server-side error occurred while accessing the asset.")

    return StreamingResponse(content=s3_response["Body"], media_type="application/zip", headers={"Content-Disposition":f"attachment; filename={itemId}.zip"})