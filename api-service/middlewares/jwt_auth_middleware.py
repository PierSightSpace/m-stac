# Imports
# Standard Library Imports
import os
import base64
from typing import Callable, Coroutine, Any

# Third-Party Imports
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError, ExpiredSignatureError, jwt

# Local Imports
from dotenv import load_dotenv
from database.postgre import get_db
from models.user import User


load_dotenv()


# JWT Configurations
JWT_ALGORITHM = ['ES256']
PUBLIC_KEY = base64.b64decode(os.getenv("ECDSA_PUBLIC_KEY")).decode("utf-8")


############################################################################################################
# User Authorization Middleware Definition
############################################################################################################
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Coroutine[Any, Any, JSONResponse]],
    ):
        '''Verifies the user's JWT token against the requests'''
        try:
            if "Authorization" not in request.headers:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized! No token provided"})
            
            JWT_token_to_be_verified = request.headers["Authorization"].split("Bearer ")[-1]
            
            db = await anext(get_db())
            is_valid = await self.validate_token(JWT_token_to_be_verified, db)
            
            response = await call_next(request)
            return response
        
        except HTTPException as http_exc:
            return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
        
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": str(e)})
        

    async def validate_token(
        self,    
        token,
        db:AsyncSession        
    ):
        '''Decode the provided JWT token using the PUBLIC_KEY and check whether the user is registered or not'''
        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=JWT_ALGORITHM, audience="api-service")
            print(payload)
            id = payload.get("user_id")
            
            if id is None:
                print("Invalid Token: user_id is missing")
                raise HTTPException(status_code=401, detail="Invalid token: user_id missing")
            
            try:
                id = int(id)
            except ValueError as e:
                print("User_id is not a valid integer")
                raise HTTPException(status_code=401, detail="Invalid user_id in token")
            
            result = await db.execute(select(User).where(User.id == id))
            user = result.scalars().first()
            if not user:
                print("Invalid token: user does not exist")
                raise HTTPException(status_code=401, detail="User not found")
            
            return True
        
        except ExpiredSignatureError as e:
            print(f"Token has expired: {str(e)}")
            raise HTTPException(status_code=401, detail=str(e))
    
        except JWTError as e:
            print(f"JWT decoding error: {str(e)}")
            raise HTTPException(status_code=401, detail=str(e))
        
        except SQLAlchemyError as db_err:
            print(f"Database error: {str(db_err)}")
            raise HTTPException(status_code=500 , detail=str(e))