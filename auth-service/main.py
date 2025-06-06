# Imports
# Standard Library Imports
from datetime import datetime
 
# Third-Party Imports
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
 
# Local Imports
from database import engine, get_db
from schemas import user as user_schema
from utils import hash_pass, verify_password
from utils import hash_pass, verify_password
from auth import create_access_token
from models import user as model
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Handles startup and shutdown events:
    - Initializes the database schema on startup.
    - Creates the tables if they do not exist on PostgreSQL.
   
    Parameters:
        app: The FastAPI application instance.
 
    Returns:
        None. Used as a context manager for FastAPI lifespan events.
    '''
    async with engine.begin() as conn:
        await conn.run_sync(model.Base.metadata.create_all)
   
    yield
       
# Swagger UI Metadata
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Endpoints for user authentication, including registration and login.",
    }
]
 
app = FastAPI(
    lifespan=lifespan,
    title="auth-service",
    description="Authentication Service for UserManagement",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url='/api',
)
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
 
 
############################################################################################################
# Middlewares
############################################################################################################
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["m-stac.onrender.com", "127.0.0.1"])

############################################################################################################
# API End-Points
############################################################################################################
@app.post(
    "/new_user",
    status_code=201,
    response_model=user_schema.PostUser,
    tags=["Authentication"],
    summary="Register a new user",
    description="Creates a new user with the provided details and saves it in the database.",
    responses={
        201: {
            "description": "User created successfully",
            "model": user_schema.PostUser,
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "johndoe@exmaple.com",
                        "created_at": "2025-01-01T00:00:00Z",
                    }
                }
            }
        },
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        },
        422: {
            "description": "Error creating user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error creating user: <error_massage>"
                    }
                }
            }
        }
    }
)      
async def create_users(
    user:user_schema.CreateUser,
    db:AsyncSession = Depends(get_db)
):
    """
    Creates a new user and saves it in the database.
 
    Parameters:
        user: The user data to create.
        db: The database session dependency.
 
    Returns:
        The created user object.
 
    Raises:
        HTTPException: If the email is already registered or user creation fails.
    """
    existing_user = await db.execute(
        model.User.__table__.select().where(model.User.email==user.email)
    )
    existing_user = existing_user.scalar_one_or_none()
 
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
   
    hashed_pass = hash_pass(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_pass
    user_data["created_at"] = datetime.now()
    try:
        new_user = model.User(**user_data)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error creating user: {str(e)}")
 
    return new_user
 
 
@app.post(
    "/login",
    response_model=user_schema.Token,
    tags=["Authentication"],
    summary="User Login",
    description="Authenticates a user and returns a JWT token if credentials are valid.",
    responses={
        200: {
            "description": "User authenticated successfully",
            "model": user_schema.Token,
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "your_jwt_token",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Incorrect email or password",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        },
        422: {
            "description": "Error during login",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error during login: <error_message>"
                    }
                }
            }
        }
    }
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    user_login_details: user_schema.LoginUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns a JWT token if credentials are valid.
 
    Parameters:
        user_login_details: The user's login credentials.
        db: The database session dependency.
        csrf_protect: The CSRF protection dependency (not used, can be removed).

    Returns:
        A dictionary containing the access token and token type.
 
    Raises:
        HTTPException: If the credentials are incorrect.
    """
    user = await db.execute(
        select(model.User).where(model.User.email==user_login_details.email)
    )
    user = user.scalar_one_or_none()
   
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
   
   
    if not verify_password(user_login_details.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
 
    access_token = create_access_token(data={"user_id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}