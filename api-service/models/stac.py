# Imports
# Third-Party Imports
from sqlalchemy import Column, Integer, Float, String, BigInteger, Date, DateTime, Text
from geoalchemy2 import Geometry
from database import Base

############################################################################################################
# Stac Model
############################################################################################################
class Stac(Base):
    __tablename__ = 'stac'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=True)
    geometry_type = Column(String(50), nullable=False)
    geometry_coordinates = Column(Geometry("GEOMETRY"), nullable=False)
    beam_mode = Column(String(50), nullable=True)
    browse = Column(String(500), nullable=True)
    bytes = Column(BigInteger, nullable=True)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    file_id = Column(String(100), unique=True, nullable=False)
    file_name = Column(String(100), nullable=True)
    flight_direction = Column(String(10), nullable=True)
    frame_number = Column(Integer, nullable=True)
    granule_type = Column(String(50), nullable=True)
    group_id = Column(String(100), nullable=True)
    md5_sum = Column(String(32), nullable=True)
    orbit = Column(Integer, nullable=True)
    path_number = Column(Integer, nullable=True)
    pge_version = Column(String(10), nullable=True)
    platform = Column(String(100), nullable=True)
    polarization = Column(String(50), nullable=True)
    processing_date = Column(Date, nullable=True)
    processing_level = Column(String(50), nullable=True)
    s3_urls = Column(Text, nullable=True)
    scene_name = Column(String(200), nullable=True)
    sensor = Column(String(50), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    stop_time = Column(DateTime(timezone=True), nullable=True)
    url = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"file_id='{self.file_id}'"
    