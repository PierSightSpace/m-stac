# Imports
# Standard Library Imports
from typing import Optional, List

# Third-Party Imports
from fastapi import Depends, HTTPException, Request, APIRouter
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

@router.post("/v1/collections", response_model=collection.CollectionModel)
async def create_collection(
    new_collection: collection.CollectionModel,
    db:AsyncSession = Depends(get_db)
):
    """ 
    Creates a new collection in the database.
    
    Parameters:
        collection_data: The collection data to create.
        db: The database session dependency.
        
    Returns:
        The created colection object.
    
    Raises:
        HTTPException: If there is an error creating the collection.
    """
    try:
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
        HTTPException(status_code=422, detail=f"Error creating collection: {str(e)}")


@router.get("/v1/collections", response_model=List[collection.CollectionModel])
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_all_collections(
    request: Request,
    response : Response,
    db:AsyncSession = Depends(get_db)
):
    """
    Retrives the all the collections.

    Parameters:
        db: The database session dependency.
        
    Returns:
        A dictionary containing the collection metadata.
    
    Raises:
        HTTPException: If there is an error retrieving the collections.
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
    

@router.get("/v1/collections/{collectionId}", response_model=List[collection.CollectionModel])
@cache(expire=86400, key_builder=my_key_builder)
@limiter.limit("5/minute")
async def get_collection(
    request: Request,
    response : Response,
    collectionId: str,
    db:AsyncSession = Depends(get_db)
):
    """
    Retrives the specified collection.

    Parameters:
        db: The database session dependency.
        
    Returns:
        A dictionary containing the collection metadata.
    
    Raises:
        HTTPException: If there is an error retrieving the collections.
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