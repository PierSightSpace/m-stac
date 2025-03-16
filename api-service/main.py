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

# Local Imports
from database import engine, get_db
from models import stac as model
from schemas import stac, catalog
from middlewares.JWTAuthMiddleware import JWTAuthMiddleware
from middlewares.LoggMiddleware import LoggMiddleware


@asynccontextmanager
async def  lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(model.Base.metadata.create_all)
    yield
    await engine.dispose()
        
        
app = FastAPI(lifespan=lifespan)


############################################################################################################
# Middlewares
############################################################################################################
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(LoggMiddleware)


ALLOWED_PLATFORM = {"SENTINEL-1A", "SENTINEL-1B", "Sentinel-3"}
LIMIT = 10
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
@app.get("/eodata/v1/", response_model=catalog.CatalogBase)
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


@app.get("/eodata/v1/all", response_model=stac.StacOutputBase)
async def get_all_stacs(
    request: Request,
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(LIMIT, ge=1, le=100),
    offset: Optional[int] = Query(OFFSET, ge=0),
    db: AsyncSession = Depends(get_db)
):
    '''Retrives all the stac from the database'''
    base_query = """SELECT * FROM stac_metadata.stac """
    params = {}
    
    if coordinates:
        input_wkt = wkt.dumps(wkt.loads(coordinates))
        spatial_query = (base_query + "WHERE ST_Intersects(ST_GeomFromWKB(geometry_coordinates), ST_GeomFromText(:input_wkt, 4326)) ")
        params["input_wkt"] = input_wkt
        if start_time and end_time:
            spatial_query += "AND start_time >= :start_time AND stop_time <= :end_time "
            params["start_time"] = start_time
            params["end_time"] = end_time
        if limit:
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            spatial_query += "OFFSET :offset"
            params["offset"] = offset
        spatial_query += ";"        
        data = await db.execute(text(spatial_query), params)
                    
    elif not coordinates:   
        norm_query = base_query     
        if start_time and end_time:
            norm_query += "AND start_time >= :start_time AND stop_time <= :end_time "
            params["start_time"] = start_time
            params["end_time"] = end_time
        if limit:
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
    if len(products) == limit and limit != num:
        print(request.url)
        next_url = f"{request.url}?limit={limit}&offset={offset + limit}"

    return stac.StacOutputBase(total_count=len(products), products=products, next=next_url)


@app.get("/eodata/v1/satellite/{platform}", response_model=stac.StacOutputBase)
async def get_satellite_stac_data(
    platform: str,
    request: Request,
    coordinates: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    num: Optional[int] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=15),
    offset: Optional[int] = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    '''Retrives all the stac from the database as per the satellite/products'''
    if platform not in ALLOWED_PLATFORM:                  
        raise HTTPException(status_code=400, detail="Invalid satellite")
    
    base_query = """SELECT * FROM stac_metadata.stac WHERE platform = :platform """
    params = {"platform": platform}

    if coordinates:
        input_wkt = wkt.dumps(wkt.loads(coordinates))
        spatial_query = (base_query + "AND ST_Intersects(ST_GeomFromWKB(geometry_coordinates), ST_GeomFromText(:input_wkt, 4326)) ")
        params["input_wkt"] = input_wkt
        if start_time and end_time:
            spatial_query += "AND start_time >= :start_time AND stop_time <= :end_time "
            params["start_time"] = start_time
            params["end_time"] = end_time
        if limit:
            spatial_query += "LIMIT :limit "
            params["limit"] = limit
        if offset:
            spatial_query += "OFFSET :offset"
            params["offset"] = offset
        spatial_query += ";"        
        data = await db.execute(text(spatial_query), params)
                    
    elif not coordinates:   
        norm_query = base_query     
        if start_time and end_time:
            norm_query += "AND start_time >= :start_time AND stop_time <= :end_time "
            params["start_time"] = start_time
            params["end_time"] = end_time
        if limit:
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
    if len(products) == limit and limit != num:
        print(request.url)
        next_url = f"{request.url}?limit={limit}&offset={offset + limit}"

    return stac.StacOutputBase(total_count=len(products), products=products, next=next_url)
