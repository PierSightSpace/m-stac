from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime, date

class Geometry(BaseModel):
    coordinates: list
    
class StacBase(BaseModel):
    id: Optional[int] = None
    type: Optional[str] = None 
    geometry_type: str
    geometry_coordinates: Geometry
    beam_mode: Optional[str] = None
    browse: Optional[HttpUrl] = None
    bytes: Optional[int] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    file_id: str
    file_name: Optional[str] = None
    flight_direction: Optional[str] = None
    frame_number: Optional[int] = None
    granule_type: Optional[str] = None
    group_id: Optional[str] = None
    md5_sum: Optional[str] = None
    orbit: Optional[int] = None
    path_number: Optional[int] = None
    pge_version: Optional[str] = None
    platform: Optional[str] = None
    polarization: Optional[str] = None
    processing_date: Optional[date] = None
    processing_level: Optional[str] = None
    s3_urls: Optional[str] = None
    scene_name: Optional[str] = None
    sensor: Optional[str] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    url: Optional[HttpUrl] = None
    

class StacOutputBase(BaseModel):
    total_count: int
    products: Optional[List[StacBase]] = []
    next: Optional[str] = None
    
    class Config:
        form_attribute = True
        extra = "forbid"
    
    
    
    