# Imports
# Standard Library Imports
import os
from typing import Optional

# Third-Party Imports
from fastapi import HTTPException, Query, Request, APIRouter
from fastapi_cache.decorator import cache
from starlette.responses import Response, StreamingResponse
from shapely import wkt
from urllib.parse import urlparse, parse_qs, urlencode
from slowapi import Limiter
from slowapi.util import get_remote_address
import boto3
from botocore.exceptions import ClientError

# Local Imports
from dotenv import load_dotenv
from database.duck import duckdb_connection
from schemas import stac
from utils import convert_to_datetime, build_products, serialize_rows, validate_inputs, my_key_builder
from config.settings import LIMIT, OFFSET, COLLECTIONS, BASE_QUERY


load_dotenv()

S3_BUCKET = os.getenv('S3_BUCKET')
S3_PREFIX = os.getenv('S3_PREFIX')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


@router.get(
    "/v1/collections/{collectionId}/items",
    response_model=stac.StacOutputBase,
    summary="All STAC Items",
    description="Retrieves all STAC items from the database with optional filters.",
    tags=["STAC Catalog"],
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
                                    "coordinates": [[...]]
                                },
                                # Other fields...
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
@limiter.limit("5/minute")
async def get_satellite_stac_data(
    request: Request,
    response : Response,
    collectionId: str,
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=15),
    offset: Optional[int] = Query(OFFSET, ge=0),
):
    """
    Retrieves STAC items filtered by satellites a.k.a collectionId.

    Parameters:
        request: The incoming HTTP request object.
        responses: 
        collectionId: The satellite to filter by.
        coordinates: Spatial filter in WKT format.
        start_time: Start time filter in ISO 8601 string format.
        stop_time: Stop time filter in ISO 8601 string format.
        num: Maximum number of items to retrieve.
        limit: Limit on the number of items per page.
        offset: Offset for pagination.

    Returns:
        JSONResponse: A paginated response containing STAC items for the specified collectionId.

    Raises:
        HTTPException: If the collectionId is invalid or no data is found.
    """
    if collectionId not in COLLECTIONS:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")

    validate_inputs(coordinates, start_time, stop_time)
    
    if start_time and stop_time and start_time > stop_time:
        raise HTTPException(status_code=400, detail=f"acquisition_start_utc: {start_time} is exceeding acquisition_end_utc: {stop_time}")
    
    conn = duckdb_connection()
    
    collectionId_query = BASE_QUERY + f"""WHERE satellite_name = '{collectionId}' """

    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)
    
    num_and_limit_flag = False
    try: 
        if coordinates:
            input_wkt = wkt.dumps(wkt.loads(coordinates))
            spatial_query = (collectionId_query + f"AND ST_Intersects(ST_GeomFromHEXWKB(bounding_box_wkb),ST_GeomFromText('{input_wkt}')) ")
            if start_time and stop_time:
                spatial_query += f"AND acquisition_start_utc >= '{start_time}' AND acquisition_end_utc <= '{stop_time}' "
            if num and num<limit:
                limit = num
                spatial_query += f"LIMIT {limit} "
                num_and_limit_flag = True
            if num_and_limit_flag==False and limit:
                spatial_query += f"LIMIT {limit} "
            if offset:
                spatial_query += f"OFFSET {offset}"
            dataframe = conn.execute(spatial_query).df()
                        
        elif not coordinates:   
            norm_query = collectionId_query     
            if start_time and stop_time:
                norm_query += f"AND acquisition_start_utc >= '{start_time}' AND acquisition_end_utc <= '{stop_time}' "
            if num and num<limit:
                limit = num
                norm_query += f"LIMIT {limit} "
                num_and_limit_flag = True
            if num_and_limit_flag==False and limit:
                norm_query += f"LIMIT {limit} "
            if offset:
                norm_query += f"OFFSET {offset}"
            dataframe = conn.execute(norm_query).df()
        data=serialize_rows(dataframe)
    finally:
        conn.close()
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for the satellite: {collectionId}")
    
    products = [build_products(stac_obj) for stac_obj in data]
    next_url = None
    if ((num and (limit+offset)<num) and (num and offset<num)) or not num:
        if len(products) == limit and limit != num:
            parsed_url = urlparse(str(request.url))
            params = parse_qs(parsed_url.query)
            if not params:
                params = {}
            
            if coordinates:
                params['coordinates'] = [str(coordinates)]   
            if start_time and stop_time:
                params['acquisition_start_utc'] = [str(start_time)]
                params['acquisition_end_utc'] = [str(stop_time)]  
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
    "/v1/collections/{collectionId}/items/{itemId}", 
    response_model=stac.StacOutputBase,
    summary=" STAC Items",
    description="Retrieves all STAC items from the database with optional filters.",
    tags=["STAC Catalog"],
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
                                    "coordinates": [[...]]
                                },
                                # Other fields...
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
@limiter.limit("5/minute")
async def get_stac_item(
    request: Request,
    response : Response,
    collectionId: str,
    itemId: str,
):
    if collectionId not in COLLECTIONS:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")
    
    conn = duckdb_connection()
    
    itemId_query = BASE_QUERY + f"""WHERE satellite_name = '{collectionId}' AND product_name = '{itemId}'"""
    
    try:
        dataframe = conn.execute(itemId_query).df()
        data=serialize_rows(dataframe)
    finally:
        conn.close()
        
    if not data:
        raise HTTPException(status_code=404, detail=f"No item: {itemId} found for the satellite: {collectionId}")
    
    products = [build_products(stac_obj) for stac_obj in data]
    return stac.StacOutputBase(total_count=len(products), products=products)


@router.get(
    "/v1/collections/{collectionId}/items/{itemId}/download",
    summary="Download STAC Item Asset",
    description="Downloads the complete asset package for a given STAC item.",
    tags=["STAC Catalog"],
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
@limiter.limit("5/minute")
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
        print(s3_response)
    except ClientError as e:
        error_code = e.response.get("Error",{}).get("Code")
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"The requested asset for item '{itemId}' does not exist.")
        elif error_code == "AccessDenied":
            raise HTTPException(status_code=403, detail="Insufficient permissions to access the asset.")
        else:
            raise HTTPException(status_code=500, detail="A server-side error occurred while accessing the asset.")

    return StreamingResponse(content=s3_response["Body"], media_type="application/zip", headers={"Content-Disposition":f"attachment; filename={itemId}.zip"})