# Imports
# Standard Library Imports
from datetime import datetime

# Third-Party Imports
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import threading
from pydantic import BaseModel
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

# Local Imports
from database import engine, get_db
from schemas import user as user_schema
from utils import hash_pass, verify_password, schedule_key_rotation, get_secret_key_csrf
from auth import create_access_token
from models import user as model


rotation_thread = None
stop_rotation = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Handles startup and shutdown events:
    - Initializes the database schema
    - Starts a thread for periodic security key rotation for csrf protection
    '''
    global rotation_thread
    async with engine.begin() as conn:
        await conn.run_sync(model.Base.metadata.create_all)
    
    stop_rotation.clear()
    rotation_thread = threading.Thread(target=schedule_key_rotation)
    rotation_thread.daemon = True
    rotation_thread.start()
    yield
        

app = FastAPI(lifespan=lifespan)

############################################################################################################
# Middlewares
############################################################################################################
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    
############################################################################################################
# CSRF Protection Settings
############################################################################################################
class CsrfSettings(BaseModel):
    secret_key: str = get_secret_key_csrf()
    cookie_samesite: str = "none"
    cookie_secure: bool = True
    

csrf = CsrfProtect()


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


############################################################################################################
# API End-Points
############################################################################################################
@app.get("/csrftoken")
async def get_csrf_token(
    csrf_protect:CsrfProtect = Depends()
):
    response = JSONResponse(status_code=200, content={'csrf_token':'cookie'})
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response
    
    
@app.post("/new_user", status_code=201, response_model=user_schema.PostUser)
async def create_users(
    user:user_schema.CreateUser, 
    db:AsyncSession = Depends(get_db),
    csrf_protect:CsrfProtect = Depends()
):
    '''Creates a new user and saves in the table.'''
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


@app.post("/login", response_model=user_schema.Token)
async def login(
    user_login_details: user_schema.LoginUser,
    db: AsyncSession = Depends(get_db),
    csrf_protect:CsrfProtect = Depends()
):
    '''Authenticates the user and returns the JWT token'''
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
    
    
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
  '''Handles CSRF protection errors'''
  return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})