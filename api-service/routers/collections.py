# Imports
# Standard Library Imports
from typing import Optional, List

# Third-Party Imports
from fastapi import Depends, HTTPException, Request, APIRouter, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address

# Local Imports
from database.postgre import get_db
from models import collection as collection_model
from schemas import collection
from utils import my_key_builder


router = APIRouter()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

@router.post(
    "/collections",
    response_model=collection.CollectionModel,
    summary="Create Collection",
    description="""
    Create a new STAC collection.
    
    This endpoint allows adding a new collection to the catalog. The collection must
    follow the STAC collection specification and include required fields such as
    id, title, description, and extent.
    """,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Collection successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "PierSight_V01",
                        "type": "Collection",
                        "stac_version": "1.0.0",
                        "title": "PierSight V01 Collection",
                        "description": "SAR imagery from PierSight V01 satellite",
                        "license": "proprietary"
                    }
                }
            }
        },
        422: {
            "description": "Validation error in collection data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid collection data: missing required field 'extent'"
                    }
                }
            }
        }
    }
)
async def create_collection(
    new_collection: collection.CollectionModel,
    db: AsyncSession = Depends(get_db)
):
    """ 
    Creates a new STAC collection in the database.
    
    Args:
        new_collection: The collection data to create
        db: Database session dependency
        
    Returns:
        CollectionModel: The created collection object
    
    Raises:
        HTTPException: 
            - 422: If there is a validation error
            - 409: If collection with same ID already exists
            - 500: For other database errors
    """
    try:
        existing = await db.execute(
            select(collection_model.Collection).where(collection_model.Collection.id == new_collection.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Collection with ID '{new_collection.id}' already exists")

        collection_data = new_collection.dict()
        for link in collection_data["links"]:
            link['href'] = str(link['href'])
        if 'providers' in collection_data:
            for provider in collection_data['providers']:
                provider['url'] = str(provider['url'])
                
        new_collection_to_db = collection_model.Collection(**collection_data)
        db.add(new_collection_to_db)
        await db.commit()
        await db.refresh(new_collection_to_db)
        
        return new_collection
    except Exception as e:
        HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")


@router.get(
    "/collections",
    response_model=collection.CollectionModel,
    summary="List Collections",
    description="""
    Retrieves all available collections in the catalog.
    
    This endpoint implements the STAC API Collections specification, returning
    a list of all available collections with their metadata.
    """,
    response_description="A list of STAC collections",
    status_code=200,
    responses={
        200: {
            "description": "Successfully retrieved collections",
            "content": {
                "application/json": {
                    "example": {
                        "collections": [
                            {
                                "id": "PierSight_V01",
                                "type": "Collection",
                                "stac_version": "1.0.0",
                                "title": "PierSight V01 Collection",
                                "description": "SAR imagery from PierSight V01 satellite",
                                "license": "proprietary"
                            }
                        ],
                        "links": [
                            {
                                "rel": "self",
                                "href": "https://stac.eodata.piersight.space/v1/collections"
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
async def get_all_collections(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all collections from the catalog.

    Args:
        request: The incoming HTTP request
        response: The outgoing HTTP response
        db: Database session dependency
        
    Returns:
        CollectionList: Object containing list of collections and links
    
    Raises:
        HTTPException: 500 if there is an error retrieving the collections
    """
    try:
        collection_query = await db.execute(select(collection_model.Collection))
        collections = collection_query.scalars().all()
        collection_list = [
            collection_model.Collection(
                id=col.id,
                type=col.type,
                stac_version=col.stac_version,
                description=col.description,
                license=col.license,
                title=col.title,
                extent=col.extent,
                links=col.links,
                providers=col.providers,
            )
            for col in collections]
        return collection_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    

@router.get(
    "/collections/{collection_id}",
    response_model=collection.CollectionModel,
    summary="Get Collection",
    description="""
    Retrieve a specific collection by its identifier.
    
    This endpoint implements the STAC API Collections specification, returning
    detailed information about a single collection.
    """,
    response_description="A STAC collection",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Successfully retrieved collection",
            "content": {
                "application/json": {
                    "example": {
                        "id": "PierSight_V01",
                        "type": "Collection",
                        "stac_version": "1.0.0",
                        "title": "PierSight V01 Collection",
                        "description": "SAR imagery from PierSight V01 satellite",
                        "license": "proprietary",
                        "extent": {
                            "spatial": {
                                "bbox": [[-180, -90, 180, 90]]
                            },
                            "temporal": {
                                "interval": [["2024-01-01T00:00:00Z"]]
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Collection not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Collection 'PierSight_V01' not found"
                    }
                }
            }
        }
    }
)
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_collection(
    request: Request,
    response : Response,
    collectionId: str,
    db:AsyncSession = Depends(get_db)
):
    """
    Retrieves a specific collection by ID.

    Args:
        request: The incoming HTTP request
        response: The outgoing HTTP response
        collection_id: The ID of the collection to retrieve
        db: Database session dependency
        
    Returns:
        CollectionModel: The requested collection's metadata
    
    Raises:
        HTTPException: 
            - 404: If collection is not found
            - 500: For other errors
    """
    try:
        collection_query = await db.execute(select(collection_model.Collection).where(collection_model.Collection.id==collectionId))
        collections = collection_query.scalars().all()
        collection_list = [
            collection_model.Collection(
                id=col.id,
                type=col.type,
                stac_version=col.stac_version,
                description=col.description,
                license=col.license,
                title=col.title,
                extent=col.extent,
                links=col.links,
                providers=col.providers,
            )
            for col in collections]
        return collection_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")