# Imports
# Standard Library Imports
import os

# Third-Party Imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local Imports
from dotenv import load_dotenv

load_dotenv()


DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:Niral0%261%403@{DB_HOST}:{DB_PORT}/{DB_NAME}"


engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    """
    Dependency function to provide postgre database session.
    
    Args: 
        None
        
    Returns: 
        AsyncSession: An asynchronous database session.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.commit()
        