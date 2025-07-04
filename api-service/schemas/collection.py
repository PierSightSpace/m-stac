# Imports
# Standard Library Imports
from typing import Optional, List

# Third-Party Imports
from pydantic import BaseModel, HttpUrl

# Local Imports
from .catalog import Links

############################################################################################################
# STAC Collection Schemas
############################################################################################################
class Provider(BaseModel):
    """
    Provider model for storing provider information in a stac item.
    
    Attributes:
        name: The name of the provider.
        roles: Optional; List of roles associated with the provider (e.g., "producer", "licensor").
        url: Optional; The url of the provider's website or service.
        
    Config:
        form_attribute: Indicates if the model should support form data.
        extra: Controls how extra fields are handled.
    """
    name: str
    roles: Optional[List[str]] = []
    url: Optional[HttpUrl] = None
    
    class Config:
        form_attribute = True
        etra = "forbid" 


class Extent(BaseModel):
    """
    Pydantic model representing the extent of a STAC collection.
    
    Attributes:
        spatial: Spatial extent of the collection.
        temporal: Temporal extent of the collection. 
    
    Config:
        form_attribute: Indicates if the model should support form data.
        extra: Controls how extra fields are handled.
    """
    spatial: dict = {}
    temporal: dict = {}
    
    class Config:
        form_attribute = True
        extra = "forbid"
        
        
class CollectionModel(BaseModel):
    """
    Pydantic model representing a STAC collections
    
    Attributes:
        id: Unique identifier for the collection.
        type: Type of the STAC item, typically "collection".
        stac_version: Version of the STAC specification used.
        description: Optional; Description of the collection.
        license: License information for the collection.
        title: Title of the Collection.
        extent: Extent of  the collection containing spatial and temporal information.
        links: List of links related to the collection.
        providers: Optional; List of providers associated with the collection.
        
    Config:
        form_attribute: Indicates if the model should support form data.
        extra: Controls how extra fields are handled.
    """
    id: str
    type: str = "collection"
    stac_version: str = "1.0.0"
    description: str = ""
    license: Optional[str] = None
    title: str = ""
    extent: Extent = Extent()
    links: List[Links] = []
    providers: Optional[List[Provider]] = []
    
    class Config:
        form_attribute = True
        extra = "forbid"