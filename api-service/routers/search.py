# Imports
# Standard Library Imports
from typing import Optional

# Third-Party Imports
from fastapi import HTTPException, Query, Request, APIRouter
from fastapi_cache.decorator import cache
from starlette.responses import Response
from shapely import wkt
from urllib.parse import urlparse, parse_qs, urlencode
from slowapi import Limiter
from slowapi.util import get_remote_address

# Local Imports
from database.duck import duckdb_connection
from schemas import stac
from utils import convert_to_datetime, build_products, serialize_rows, validate_inputs, my_key_builder
from config.settings import LIMIT, OFFSET, BASE_QUERY


router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


@router.post(
    "/v1/search", 
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
        }
    }
)
@cache(expire=3600, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_all_stacs(
    request: Request,
    response : Response,
    collectionId: Optional[str] = Query(None),
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=100),
    offset: Optional[int] = Query(OFFSET, ge=0)
):
    """
    Retrieves all STAC items from the database.

    Parameters:
        request: The incoming HTTP request object.
        response: 
        collectionId:Filter for the satellite collection.
        coordinates: Spatial filter in WKT format.
        start_time: Start time filter in ISO 8601 string format.
        stop_time: Stop time filter in ISO 8601 string format.
        num: Maximum number of items to retrieve.
        limit: Limit on the number of items per page.
        offset: Offset for pagination.

    Returns:
        JSONResponse: A paginated response containing STAC items matching the filters.

    Raises:
        HTTPException: If start_time is after stop_time or no data is found.
    """
    validate_inputs(coordinates, start_time, stop_time)
    conn = duckdb_connection()

    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)
    
    if start_time and stop_time and start_time > stop_time:
        raise HTTPException(status_code=400, detail=f"acquisition_start_utc: {start_time} is exceeding acquisition_end_utc: {stop_time}")
    
    num_and_limit_flag = False
    try:
        if coordinates:
            input_wkt = wkt.dumps(wkt.loads(coordinates))
            spatial_query = (BASE_QUERY + f"WHERE satellite_name='{collectionId}' AND ST_Intersects(ST_GeomFromHEXWKB(bounding_box_wkb),ST_GeomFromText('{input_wkt}')) ")
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
            norm_query = BASE_QUERY
            if start_time and stop_time:
                norm_query += f"WHERE satellite_name='{collectionId}' AND acquisition_start_utc >= '{start_time}' AND acquisition_end_utc <= '{stop_time}' "
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
        raise HTTPException(status_code=404, detail="No data found for given input")
        
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