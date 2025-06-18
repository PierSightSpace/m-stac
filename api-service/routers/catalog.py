# Imports
# Third-Party Imports
from fastapi import APIRouter, Request, status
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
    "/", 
    response_model=catalog.CatalogBase,
    summary="Get STAC Catalog",
    description="""
    Retrieves the root STAC catalog containing metadata about available collections.
    
    The catalog provides:
    - Basic information about the PierSight STAC API
    - Links to child collections
    - Version information
    - Available extensions
    
    The response follows the STAC specification for catalog objects.
    """,
    response_description="A STAC catalog object containing metadata and links to collections",
    status_code=200,
    responses={
        200: {
            "description": "Successfully retrieved the STAC catalog",
            "content": {
                "application/json": {
                    "example": {
                        "type": "Catalog",
                        "id": "piersight-catalog",
                        "title": "PierSight Catalog",
                        "description": "PierSight's STAC catalog for maritime surveillance data",
                        "stac_version": "1.0.0",
                        "links": [
                            {
                                "rel": "self",
                                "href": "https://stac.eodata.piersight.space/v1/"
                            },
                            {
                                "rel": "child",
                                "href": "https://stac.eodata.piersight.space/v1/collections/PierSight_V01"
                            }
                        ]
                    }
                }
            }
        }
    }
)
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_piersight_catalog(
    request: Request,
    response: Response,
):
    """
    Returns the PierSight STAC catalog metadata.

    This endpoint provides the root catalog information for the PierSight STAC API,
    including links to all available collections and API endpoints.

    Args:
        request (Request): The incoming HTTP request
        response (Response): The outgoing HTTP response

    Returns:
        dict: A dictionary containing the catalog metadata.
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
                    "rel": "service-desc",
                    "mime_type": "application/vnd.oai.openapi+json;version=3.0",
                    "href": "https://stac.eodata.piersight.space/api/openapi.json"
                },
                {
                    "rel": "service-doc",
                    "mime_type": "text/html",
                    "href": "https://stac.eodata.piersight.space/api"
                },
                {
                    "rel": "conformance",
                    "mime_type": "application/json",
                    "href": "https://stac.eodata.piersight.space/v1/conformance"
                },
                {
                    "rel": "data",
                    "mime_type": "application/json",
                    "href": "https://stac.eodata.piersight.space/v1/collections"
                },
                {
                    "rel": "search",
                    "mime_type": "application/geo+json",
                    "href": "https://stac.eodata.piersight.space/v1/search"
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


@router.get(
    "/conformance",
    response_model=catalog.ConformanceResponse,
    summary="Get API Conformance",
    description="""
    Lists the conformance classes that the API conforms to.
    
    This endpoint is required by the OGC API specification and lists all
    conformance classes implemented by this API.
    """,
    response_description="A list of conformance classes that the API implements",
    status_code=200,
    responses={
        200: {
            "description": "The list of conformance classes implemented by this API",
            "content": {
                "application/json": {
                    "example": {
                        "conformsTo": [
                            "https://api.stacspec.org/v1.0.0/core",
                            "https://api.stacspec.org/v1.0.0/collections",
                            "https://api.stacspec.org/v1.0.0/search"
                        ]
                    }
                }
            }
        }
    }
)
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_conformance(
    request: Request,
    response: Response,
):
    """
    Returns the conformance declaration for the API.

    This endpoint lists all the standards and specifications that this API
    implements, helping clients understand the capabilities of the service.

    Args:
        request (Request): The incoming HTTP request
        response (Response): The outgoing HTTP response

    Returns:
        dict: A conformance object listing implemented specifications
    """
    return {
        "conformsTo": [
            "https://api.stacspec.org/v1.0.0/core",
            "https://api.stacspec.org/v1.0.0/collections",
            "https://api.stacspec.org/v1.0.0/search",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        ]
    }
    return conformance_result

