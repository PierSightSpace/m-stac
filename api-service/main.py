# Imports
# Standard Library Imports
import json
from typing import Optional

# Third-Party Imports
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from shapely import wkt, to_geojson
from shapely.wkb import loads as wkb_loads
from contextlib import asynccontextmanager
from urllib.parse import urlparse, parse_qs, urlencode

# Local Imports
from database import engine, get_db
from models import stac as stac_model, log_entry as log_model
from schemas import stac, catalog
from middlewares.jwt_auth_middleware import JWTAuthMiddleware
from middlewares.logg_middleware import LoggMiddleware
from utils import convert_to_datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(stac_model.Base.metadata.create_all)
        await conn.run_sync(log_model.Base.metadata.create_all)
        print("🏪Database is ready")
    yield
    await engine.dispose()
        
        
app = FastAPI(lifespan=lifespan)


############################################################################################################
# Middlewares
############################################################################################################
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["m-stac-1.onrender.com", "m-stac.onrender.com", "127.0.0.1", "localhost"])
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(LoggMiddleware)


ALLOWED_PLATFORM = {"VARUNA-1", "VARUNA-2", "VARUNA-3"}
LIMIT = 7
OFFSET = 0


############################################################################################################
# Utility Functions
############################################################################################################
def extract_geometry_coords(geometry_data):
    stac_geojson_str = to_geojson(wkt.loads(wkb_loads(geometry_data, hex=True).wkt), indent=2)
    stac_geojson = json.loads(stac_geojson_str)
    geom_coords = stac_geojson["coordinates"]
    return geom_coords


def build_products(stac_obj) -> stac.StacBase:
    geom_coords = extract_geometry_coords(stac_obj.geometry_coordinates)
    geom_obj = stac.Geometry(coordinates=geom_coords)
    return stac.StacBase(
        id=stac_obj.id,
        type="Feature",
        geometry_type="Polygon",
        geometry_coordinates=geom_obj, 
        beam_mode=stac_obj.beam_mode,
        browse=stac_obj.browse,
        bytes=stac_obj.bytes,
        center_lat=stac_obj.center_lat,
        center_lon=stac_obj.center_lon,
        file_id=stac_obj.file_id,
        file_name=stac_obj.file_name,
        flight_direction=stac_obj.flight_direction,
        frame_number=stac_obj.frame_number,
        granule_type=stac_obj.granule_type,
        group_id=stac_obj.group_id,
        md5_sum=stac_obj.md5_sum,
        orbit=stac_obj.orbit,
        path_number=stac_obj.path_number,
        pge_version=stac_obj.pge_version,
        platform=stac_obj.platform,
        polarization=stac_obj.polarization,
        processing_date=stac_obj.processing_date,
        processing_level=stac_obj.processing_level,
        s3_urls=stac_obj.s3_urls,
        scene_name=stac_obj.scene_name,
        sensor=stac_obj.sensor,
        start_time=stac_obj.start_time,
        stop_time=stac_obj.stop_time,
        url=stac_obj.url,
    )


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
    offset: Optional[int] = Query(OFFSET, ge=0),
    db: AsyncSession = Depends(get_db)
):
    '''Retrives all the stac from the database'''    
    base_query = """SELECT * FROM stac_metadata.stac """
    params = {}
    
    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)

    num_and_limit_flag = False
    
    if coordinates:
        input_wkt = wkt.dumps(wkt.loads(coordinates))
        spatial_query = (base_query + "WHERE ST_Intersects(ST_GeomFromWKB(geometry_coordinates), ST_GeomFromText(:input_wkt, 4326)) ")
        params["input_wkt"] = input_wkt
        if start_time and stop_time:
            spatial_query += "AND start_time >= :start_time AND stop_time <= :stop_time "
            params["start_time"] = start_time
            params["stop_time"] = stop_time
        if num and num<limit:
            limit = num
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
            num_and_limit_flag = True
        if num_and_limit_flag==False and limit:
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            spatial_query += "OFFSET :offset"
            params["offset"] = offset
        spatial_query += ";"      
        data = await db.execute(text(spatial_query), params)
                    
    elif not coordinates:   
        norm_query = base_query
        if start_time and stop_time:
            norm_query += "AND start_time >= :start_time AND stop_time <= :stop_time "
            params["start_time"] = start_time
            params["stop_time"] = stop_time
        if num and num<limit:
            limit = num
            norm_query += "LIMIT :limit "
            params["limit"] = limit
            num_and_limit_flag = True
        if num_and_limit_flag==False and limit:
            norm_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            norm_query += "OFFSET :offset"
            params["offset"] = offset
        norm_query += ";"
        data = await db.execute(text(norm_query), params)
    
    data = data.fetchall()
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found")
        
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
    db: AsyncSession = Depends(get_db)
):
    '''Retrives all the stac from the database as per the satellite/products'''
    if platform not in ALLOWED_PLATFORM:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")
    
    base_query = """SELECT * FROM stac_metadata.stac WHERE platform = :platform """
    params = {"platform": platform}

    start_time = convert_to_datetime(start_time)
    stop_time = convert_to_datetime(stop_time)
    
    num_and_limit_flag = False
    
    if coordinates:
        input_wkt = wkt.dumps(wkt.loads(coordinates))
        spatial_query = (base_query + "AND ST_Intersects(ST_GeomFromWKB(geometry_coordinates), ST_GeomFromText(:input_wkt, 4326)) ")
        params["input_wkt"] = input_wkt
        if start_time and stop_time:
            spatial_query += "AND start_time >= :start_time AND stop_time <= :stop_time "
            params["start_time"] = start_time
            params["stop_time"] = stop_time
        if num and num<limit:
            limit = num
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
            num_and_limit_flag = True
        if num_and_limit_flag==False and limit:
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            spatial_query += "OFFSET :offset"
            params["offset"] = offset
        spatial_query += ";"        
        data = await db.execute(text(spatial_query), params)
                    
    elif not coordinates:   
        norm_query = base_query     
        if start_time and stop_time:
            norm_query += "AND start_time >= :start_time AND stop_time <= :stop_time "
            params["start_time"] = start_time
            params["stop_time"] = stop_time
        if num and num<limit:
            limit = num
            norm_query += "LIMIT :limit "
            params["limit"] = limit
            num_and_limit_flag = True
        if num_and_limit_flag==False and limit:
            norm_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            norm_query += "OFFSET :offset"
            params["offset"] = offset
        norm_query += ";"
        data = await db.execute(text(norm_query), params)
    
    data = data.fetchall()
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
