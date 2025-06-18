# Imports
# Standard Library Imports
import json
from typing import Optional
from datetime import datetime

# Third-Party Imports
from fastapi import HTTPException
from shapely import wkb, to_geojson
import pandas as pd
import geopandas as gpd

# Local Imports
from schemas import stac


def convert_to_datetime(time_in_str):
    """
    Converts a string in ISO 8601 format to a datetime object.

    Parameters:
        time_in_str: String representing the date and time in the format 'YYYY-MM-DDTHH:MM:SSZ'.

    Returns:
        A datetime object if conversion is successful, otherwise None.
    """
    if time_in_str:
        try:
            return datetime.strptime(time_in_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            print(str(e))
    return None


def extract_geometry_coords(geometry_data):
    """
    Extracts the coordinates from a geometry object.

    Parameters:
        geometry_data: The geometry data to extract coordinates from.

    Returns:
        The coordinates extracted from the geometry.
    """
    geom = wkb.loads(bytes.fromhex(geometry_data))
    stac_geojson_str = to_geojson(geom, indent=2)
    stac_geojson = json.loads(stac_geojson_str)
    geom_coords = stac_geojson["coordinates"]
    return geom_coords


def build_products(stac_obj) -> stac.StacBase:
    """
    Builds a STAC product object from the provided data.

    Parameters:
        stac_obj: The source object containing STAC item data.

    Returns:
        A STAC product object with all relevant fields populated.
    """
    geom_coords = extract_geometry_coords(stac_obj["bounding_box_wkb"])
    geom_obj = stac.Geometry(coordinates=geom_coords)
    return stac.StacBase(
        id=stac_obj["id"],
        type="Feature",
        geom_type="Polygon",
        bounding_box_wkb=geom_obj,
        browse=stac_obj["browse"],
        bytes=stac_obj["bytes"],
        center_lat=stac_obj["center_lat"],
        center_lon=stac_obj["center_lon"],
        product_name=stac_obj["product_name"],
        product_file=stac_obj["product_file"],
        orbit_direction=stac_obj["orbit_direction"],
        md5_sum=stac_obj["md5_sum"],
        orbit_absolute_number=stac_obj["orbit_absolute_number"],
        processor_version=stac_obj["processor_version"],
        satellite_name=stac_obj["satellite_name"],
        polarization=stac_obj["polarization"],
        processing_time=stac_obj["processing_time"],
        product_level=stac_obj["product_level"],
        acquisition_start_utc=stac_obj["acquisition_start_utc"],
        acquisition_end_utc=stac_obj["acquisition_end_utc"],
        assets=stac_obj["assets"],
    )


def serialize_rows(rows, keys):
    """
    Serializes a DataFrame of records to a list of dictionaries.

    Converts geometry fields to GeoJSON and replaces any NaN values with None.

    Parameters:
        dataframe: The DataFrame containing the records to serialize.

    Returns:
        A list of dictionaries representing the serialized records.
    """
    dataframe['geom_type'] = dataframe['bounding_box_wkb'].apply(lambda x: wkb.loads(x) if x else None)
    gdf = gpd.GeoDataFrame(dataframe, geometry='geometry', crs='EPSG:4326')
    result =  gdf.to_dict(orient='records')

    for res in result:
        for key, value in res.items():
            import math
            if isinstance(value, float) and math.isnan(value):
                res[key] = None
    return result
        
def validate_bbox(bbox: Optional[str]):
    """
    Validates that the provided coordinates are in a valid WKT format.

    Parameters:
        coordinates: The geometry coordinates to validate.

    Raises:
        HTTPException: If the coordinates are not valid WKT.
    """
    if bbox is not None:
        if not (len(bbox)==4 or len(bbox)==6):
            raise HTTPException(status_code=422, detail="bbox must have 4 or 6 numbers.")
    
        min_lon, min_lat, max_lon, max_lat = bbox[:4]
        if min_lon > max_lon or min_lat > max_lat:
            raise HTTPException(status_code=422, detail="bbox coordinates are invalid.")
    
                    
def validate_time(time: Optional[str], field_name):
    """
    Validates that the provided time string is in ISO 8601 format.

    Parameters:
        time: The time string to validate.
        field_name: The name of the field being validated (for error messages).

    Raises:
        HTTPException: If the time string is not in ISO 8601 format.
    """
    if time is not None:
        try:
            if time.endswith('Z'):
                time=time[:-1]
            datetime.fromisoformat(time)
        except Exception:
            raise HTTPException(status_code=422, detail=f"Invalid {field_name}; Must be in ISO 8601 datetime.")
        

def validate_inputs(bbox, start_time, stop_time):
    """
    Validates the input parameters for bbox and time filters.

    Parameters:
        coordinates: The geometry coordinates to validate.
        start_time: The start time string to validate.
        stop_time: The stop time string to validate.

    Raises:
        HTTPException: If any input is invalid.
    """
    validate_bbox(bbox)
    validate_time(start_time, field_name="start_time")
    validate_time(stop_time, field_name="stop_time")
    

def my_key_builder(func, namespace, request=None, response=None, args=(), kwargs=None):
    key = f"{namespace}:{request.url.path}"
    if request:
        params = "&".join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
        key += f"?{params}"
    return key