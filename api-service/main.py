# Imports
# Standard Library Imports
import json
from typing import Optional

# Third-Party Imports
from fastapi import FastAPI, HTTPException, Query, Request
from sqlalchemy import text
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from shapely import wkb, wkt, to_geojson
import geopandas as gpd
from datetime import datetime
from contextlib import asynccontextmanager
from urllib.parse import urlparse, parse_qs, urlencode

# Local Imports
from database.duck import duckdb_connection
from database.postgre import engine
from models import log_entry as log_model
from schemas import stac, catalog
from middlewares.jwt_auth_middleware import JWTAuthMiddleware
from middlewares.logg_middleware import LoggMiddleware
from utils import convert_to_datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(log_model.Base.metadata.create_all)
        print("🏪Database is ready")
    yield
    await engine.dispose()
        
        
app = FastAPI(lifespan=lifespan)


############################################################################################################
# Middlewares
############################################################################################################
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["m-stac-1.onrender.com", "m-stac.onrender.com", "127.0.0.1", "localhost"])
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(LoggMiddleware)


BASE_QUERY = f"""SELECT * FROM read_parquet('s3://piersight-stac/stac_*.parquet') """
ALLOWED_PLATFORM = {"VARUNA-1", "VARUNA-2", "VARUNA-3"}
LIMIT = 7
OFFSET = 0


############################################################################################################
# Utility Functions
############################################################################################################
def extract_geometry_coords(geometry_data):
    stac_geojson_str = to_geojson(geometry_data, indent=2)
    stac_geojson = json.loads(stac_geojson_str)
    geom_coords = stac_geojson["coordinates"]
    return geom_coords


def build_products(stac_obj) -> stac.StacBase:
    geom_coords = extract_geometry_coords(stac_obj["geometry"])
    geom_obj = stac.Geometry(coordinates=geom_coords)
    return stac.StacBase(
        id=stac_obj["id"],
        type="Feature",
        geometry_type="Polygon",
        geometry_coordinates=geom_obj, 
        beam_mode=stac_obj["beam_mode"],
        browse=stac_obj["browse"],
        bytes=stac_obj["bytes"],
        center_lat=stac_obj["center_lat"],
        center_lon=stac_obj["center_lon"],
        file_id=stac_obj["file_id"],
        file_name=stac_obj["file_name"],
        flight_direction=stac_obj["flight_direction"],
        frame_number=stac_obj["frame_number"],
        granule_type=stac_obj["granule_type"],
        group_id=stac_obj["group_id"],
        md5_sum=stac_obj["md5_sum"],
        orbit=stac_obj["orbit"],
        path_number=stac_obj["path_number"],
        pge_version=stac_obj["pge_version"],
        platform=stac_obj["platform"],
        polarization=stac_obj["polarization"],
        processing_date=stac_obj["processing_date"],
        processing_level=stac_obj["processing_level"],
        s3_urls=stac_obj["s3_urls"],
        scene_name=stac_obj["scene_name"],
        sensor=stac_obj["sensor"],
        start_time=stac_obj["start_time"],
        stop_time=stac_obj["stop_time"],
        url=stac_obj["url"],
    )


def serialize_rows(dataframe):
    """
    Serialize a list of tuples (rows) to a JSON-serializable list of dicts.
    Converts bytes fields to hex strings.
    """
    dataframe['geometry'] = dataframe['geometry_coordinates'].apply(lambda x: wkb.loads(x) if x else None)
    gdf = gpd.GeoDataFrame(dataframe, geometry='geometry', crs='EPSG:4326')
    result =  gdf.to_dict(orient='records')

    for res in result:
        for key, value in res.items():
            import math
            if isinstance(value, float) and math.isnan(value):
                res[key] = None
    return result
        
def validate_coordinates(coordinates: Optional[str]):
    """
    Validates whether the goemetry or its type is valid or not
    """
    if coordinates is not None:
        try: 
            geometry = wkt.loads(coordinates)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid coordinates; Must be in WKT format")
                    

def validate_time(time: Optional[str], field_name):
    if time is not None:
        try:
            if time.endswith('Z'):
                time=time[:-1]
            datetime.fromisoformat(time)
        except Exception:
            raise HTTPException(status_code=422, detail=f"Invalid {field_name}; Must be in ISO 8601 datetime.")
        

def validate_inputs(coordinates, start_time, stop_time):
    validate_coordinates(coordinates)
    validate_time(start_time, field_name="start_time")
    validate_time(stop_time, field_name="stop_time")
############################################################################################################
# API End-Points
############################################################################################################
@app.get("/eodata/v1/catalog", response_model=catalog.CatalogBase)
async def get_piersight_catalog():
    '''Catalog of the PierSight'''
    catalog_result = {
        "type": "Catalog",
        "id": "PierSight Space Maritime Servilliance Data",
        "title": "PierSight Catalog",
        "stac_version": "1.0.0",
        "links": [],
        "stac_extensions": []
    }
    return catalog_result


@app.get("/eodata/v1/stacs/all", response_model=stac.StacOutputBase)
async def get_all_stacs(
    request: Request,
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=100),
    offset: Optional[int] = Query(OFFSET, ge=0)
):
    '''Retrives all the stac from the database'''    
    validate_inputs(coordinates, start_time, stop_time)
    conn = duckdb_connection()

    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)
    
    if start_time and stop_time and start_time > stop_time:
        raise HTTPException(status_code=400, detail=f"start_time: {start_time} is exceeding stop_time: {stop_time}")
    
    num_and_limit_flag = False
    try:
        if coordinates:
            input_wkt = wkt.dumps(wkt.loads(coordinates))
            spatial_query = (BASE_QUERY + f"WHERE ST_Intersects(ST_GeomFromHEXWKB(geometry_coordinates),ST_GeomFromText('{input_wkt}')) ")
            if start_time and stop_time:
                spatial_query += f"AND start_time >= '{start_time}' AND stop_time <= '{stop_time}' "
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
                norm_query += f"WHERE start_time >= '{start_time}' AND stop_time <= '{stop_time}' "
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


@app.get("/eodata/v1/stacs/satellite/{platform}", response_model=stac.StacOutputBase)
async def get_satellite_stac_data(
    platform: str,
    request: Request,
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    stop_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=15),
    offset: Optional[int] = Query(OFFSET, ge=0),
):
    '''Retrives all the stac from the database as per the satellite/products'''
    if platform not in ALLOWED_PLATFORM:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")

    validate_inputs(coordinates, start_time, stop_time)
    
    if start_time and stop_time and start_time > stop_time:
        raise HTTPException(status_code=400, detail=f"start_time: {start_time} is exceeding stop_time: {stop_time}")
    
    conn = duckdb_connection()
    
    platform_query = BASE_QUERY + f"""WHERE platform = '{platform}' """

    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)
    
    num_and_limit_flag = False
    try: 
        if coordinates:
            input_wkt = wkt.dumps(wkt.loads(coordinates))
            spatial_query = (platform_query + f"AND ST_Intersects(ST_GeomFromHEXWKB(geometry_coordinates),ST_GeomFromText('{input_wkt}')) ")
            if start_time and stop_time:
                spatial_query += f"AND start_time >= '{start_time}' AND stop_time <= '{stop_time}' "
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
            norm_query = platform_query     
            if start_time and stop_time:
                norm_query += f"AND start_time >= '{start_time}' AND stop_time <= '{stop_time}' "
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
        raise HTTPException(status_code=404, detail=f"No data found for the satellite: {platform}")
    
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
