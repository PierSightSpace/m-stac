# Imports
# Standard Library Imports
from typing import Optional, List, Literal

# Third-Party Imports
from pydantic import BaseModel, HttpUrl


############################################################################################################
# Cataog Schemas
############################################################################################################
class Links(BaseModel):
    rel: str
    mime_type: Literal["application/json", "application/geo+json", "application/vnd.oai.openapi+json;version=3.0", "text/html"]
    href: HttpUrl
    
class CatalogBase(BaseModel):
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