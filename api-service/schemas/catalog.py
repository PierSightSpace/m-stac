# Imports
# Standard Library Imports
from typing import Optional, List, Literal

# Third-Party Imports
from pydantic import BaseModel, HttpUrl


############################################################################################################
# Cataog Schemas
############################################################################################################
class Links(BaseModel):
    """
    Links model for storing links in model

    Args:
        BaseModel: Base class for pydantic models.
    
    Attributes:
        rel: The relationship type of the link.
        mime_type: The MIME type of the link.
        href: The URL of the link.
   
    Returns: 
        None
    """
    rel: str
    mime_type: Literal["application/json", "application/geo+json", "application/vnd.oai.openapi+json;version=3.0", "text/html"]
    href: HttpUrl
    title: Optional[str] = None
    
class CatalogBase(BaseModel):
    """
    CatalogBase model for storing catalog information in a model.

    Args:
        BaseModel: Base class for pydantic models.
    
    Attributes:
        type: The type of the catalog.
        id: The unique identifier of the catalog.
        title: The title of the catalog.
        description: A brief description of the catalog.
        stac_version: The version of the STAC specification used.
        links: A list cotaining the links associated with the catalog.
        stac_extensions: A list of STAC extensions used in the catalog.
   
    Returns: 
        None
    """
    type: str
    id: str
    title: str
    description: Optional[str] = None
    stac_version: str
    links: Optional[List[Links]] = []
    stac_extensions: Optional[List[str]] = []
    
    class Config:
        form_attribute = True
        extra = "forbid"

class ConformanceResponse(BaseModel):
    """
    ConformanceResponse model for the API conformance declaration.

    Args:
        BaseModel: Base class for pydantic models.
    
    Attributes:
        conformsTo: A list of URIs identifying the conformance classes implemented by the API.
   
    Returns: 
        None
    """
    conformsTo: List[str]
    
    class Config:
        form_attribute = True
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "conformsTo": [
                    "https://api.stacspec.org/v1.0.0/core",
                    "https://api.stacspec.org/v1.0.0/collections",
                    "https://api.stacspec.org/v1.0.0/search",
                    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
                ]
            }
        }