# Imports
# Standard Library Imports
import os
import base64
from datetime import timedelta, datetime

# Third-Party Imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

# Local Imports
from dotenv import load_dotenv
from models.user import User

# OAuth2 password bearer scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


load_dotenv()


# JWT Configurations
JWT_ALGORITHM = 'ES256'
ACCESS_TOKEN_EXPIRE_MINUTES = 1000
PRIVATE_KEY = base64.b64decode(os.getenv("ECDSA_PRIVATE_KEY")).decode("utf-8")


############################################################################################################
# Token Generation Function
############################################################################################################
def create_access_token(
    data: dict
):
    '''Generates the JWT token for the logged in user with the encoded user's credentials'''
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    user_id = data.get("user_id")
    to_encode.update({
        "exp": int(expire.timestamp()), 
        "iat": int(datetime.now().timestamp()), 
        "nbf": int(datetime.now().timestamp()),
        "iss": "m-stac.piersight.space",
        "aud": "api-service",
        "sub": user_id,
    })
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt
