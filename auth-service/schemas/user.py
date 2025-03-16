# Imports
# Standard Library Imports
from typing import Optional
from datetime import datetime

# Third-Party Imports
from pydantic import BaseModel, EmailStr


############################################################################################################
# User Schemas
############################################################################################################
class CreateUser(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        from_attribute = True


class LoginUser(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        from_attribute = True


class Token(BaseModel):
    access_token: str
    token_type: str


class DataToken(BaseModel):
    id: Optional[str] = None
    
    
class PostUser(BaseModel):
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attribute = True
    
