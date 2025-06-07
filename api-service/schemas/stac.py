# Imports
# Standard Library Imports
from typing import Optional, List
from datetime import datetime, date

# Third-Party Imports
from pydantic import BaseModel, HttpUrl


############################################################################################################
# Stac Schemas
############################################################################################################
class Geometry(BaseModel):
    """
    Geometry model for storing geometry information in a model.

    Args:
        BaseModel: Base class for pydantic models.

    Attributes:
        coordinates: A list of coordinates representing the geometry.
    
    Returns:
        None
    """
    coordinates: list
    
class StacBase(BaseModel):
    """
    StacBase model for storing STAC metadata in a model.

    Args:
        BaseModel: Base class for pydantic models.

    Attributes:
        id: The unique identifier of the STAC item.
        type: The type of the STAC item.
        geometry_type: The type of geometry.
        geometry_coordinates: The coordinates of the geometry.
        beam_mode: The beam mode of the STAC item.
        browse: The URL of the browse image.
        bytes: The size of the STAC item in bytes.
        center_lat: The latitude of the center  point.
        center_lon: The longitude of the center point.
        file_id: The unique identifier of the file.
        file_name: The name of the file.
        flight_direction: Flight direction of the platform.
        frame_number: Frame number of the acquisition.
        granule_type: Granule type.
        group_id: Group identifier.
        md5_sum: MD5 checksum of the file.
        orbit: Orbit number.
        path_number: Path number of the acquisition.
        pge_version: Version of the processing software.
        platform: Platform name.
        polarization: Polarization mode.
        processing_date: Date the item was processed.
        processing_level: Processing level, such as L1 or L2.
        s3_urls: S3 URLs where the asset is stored.
        scene_name: Scene name.
        sensor: Sensor name.
        start_time: Acquisition start time.
        stop_time: Acquisition stop time.
        url: Main URL for the STAC item.
    
    Returns:
        None
    """
    id: str = None
    type: Optional[str] = None 
    geom_type: str
    bounding_box_wkb: Geometry
    beam_mode: Optional[str] = None
    browse: Optional[str] = None
    bytes: Optional[int] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    product_name: str
    product_file: Optional[str] = None
    orbit_direction: Optional[str] = None
    md5_sum: Optional[str] = None
    orbit_absolute_number: Optional[int] = None
    processor_version: Optional[str] = None
    satellite_name: Optional[str] = None
    polarization: Optional[str] = None
    processing_time: Optional[datetime] = None
    product_level: Optional[str] = None
    acquisition_start_utc: Optional[datetime] = None
    acquisition_end_utc: Optional[datetime] = None
    assets: Optional[str] = None
    

class StacOutputBase(BaseModel):
    """
    Pydantic model representing the output structure for a paginated list of STAC items.

    Attributes:
        total_count: Total number of STAC items available.
        products: List of STAC item metadata objects.
        next: URL or token for retrieving the next page of results, if any.

    Config:
        form_attribute: Indicates if the model should support form data.
        extra: Controls how extra fields are handled.
    """
    total_count: int
    products: Optional[List[StacBase]] = []
    next: Optional[str] = None
    
    class Config:
        form_attribute = True
        extra = "forbid"
   
    
    