from datetime import timedelta, datetime
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Callable, Coroutine, Any
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import schemas
from database import get_db
import os
import models
import logger
from utils import get_secret_key_auth

JWT_ALGORITHM = 'HS256'

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Coroutine[Any, Any, JSONResponse]],
    ):
        logger.debug(f"Request URL path: {request.url.path}")
        try:
            if "Authorization" not in request.headers:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
            JWT_token_to_be_verified = request.headers["Authorization"].split("Bearer ")[-1]
            if not validate_token(JWT_token_to_be_verified):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
            response = await call_next(request)
            return response
        
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": str(e)})
        

def validate_token(token):
    try:
        payload = jwt.decode(token, get_secret_key_auth, algorithms=JWT_ALGORITHM)
        id: str = payload.get("id")
        if id is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        token_data = schemas.DataToken(id=id)
    except JWTError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
