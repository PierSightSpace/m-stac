# Imports
# Third-Party Imports
from fastapi import  APIRouter, Request
from fastapi_cache.decorator import cache
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

# Local Imports
from schemas import catalog
from utils import my_key_builder


router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

@router.get(
    "/v1", 
    response_model=catalog.CatalogBase,
    summary="PierSight STAC Catalog",
    description="Return the PierSight catalog metadata.",
    tags=["STAC Catalog"],
        
) 
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_piersight_catalog(
    request: Request,
    response : Response,
):
    """
    Returns the PierSight catalog metadata.

    Returns:
        A dictionary containing the catalog metadata.
    """
    catalog_result = {
        "type": "Catalog",
        "id": "PierSight Space Maritime Servilliance Data",
        "title": "PierSight Catalog",
        "description": 'PierSight Catalog provides access to high-resolution, all-weather Synthetic Aperture Radar (SAR) imagery and maritime surveillance data collected by the PierSight satellite constellation. The catalog enables persistent monitoring of global maritime activities, including ship detection, oil spill tracking, and coastal infrastructure analysis, supporting applications in security, environmental monitoring, and maritime domain awareness.',
        "stac_version": "1.0.0",
        "links": 
            [
                {
                    "rel": "self",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/"
                },
                {
                    "rel": "root",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01",
                    "title": "PierSight-V01 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V02",
                    "title": "PierSight-V02 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V03",
                    "title": "PierSight-V03 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V04",
                    "title": "PierSight-V04 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V05",
                    "title": "PierSight-V05 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V06",
                    "title": "PierSight-V06 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V07",
                    "title": "PierSight-V07 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V08",
                    "title": "PierSight-V08 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V09",
                    "title": "PierSight-V09 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V10",
                    "title": "PierSight-V10 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V11",
                    "title": "PierSight-V11 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V12",
                    "title": "PierSight-V12 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V13",
                    "title": "PierSight-V13 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V14",
                    "title": "PierSight-V14 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V15",
                    "title": "PierSight-V15 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V16",
                    "title": "PierSight-V16 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V17",
                    "title": "PierSight-V17 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V18",
                    "title": "PierSight-V18 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V19",
                    "title": "PierSight-V19 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V20",
                    "title": "PierSight-V20 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V21",
                    "title": "PierSight-V21 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V22",
                    "title": "PierSight-V22 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V23",
                    "title": "PierSight-V23 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V24",
                    "title": "PierSight-V24 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V25",
                    "title": "PierSight-V25 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V26",
                    "title": "PierSight-V26 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V27",
                    "title": "PierSight-V27 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V28",
                    "title": "PierSight-V28 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V29",
                    "title": "PierSight-V29 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V30",
                    "title": "PierSight-V30 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V31",
                    "title": "PierSight-V31 Collection"
                },
                {
                    "rel": "child",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V32",
                    "title": "PierSight-V32 Collection"
                },
            ],
        "stac_extensions": []
    }
    
    return catalog_result