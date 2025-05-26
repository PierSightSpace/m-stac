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
    """
    Schema for creating a new user.

    Attributes:
        email: User's email address.
        password: User's password.

    Config:
        from_attribute: Indicates if the model should support attribute-based population.
    """
    email: EmailStr
    password: str
    
    class Config:
        from_attribute = True


class LoginUser(BaseModel):
    """
    Schema for user login.

    Attributes:
        email: User's email address.
        password: User's password.

    Config:
        from_attribute: Indicates if the model should support attribute-based population.
    """
    email: EmailStr
    password: str
    
    class Config:
        from_attribute = True


class Token(BaseModel):
    """
    Schema representing an authentication token.

    Attributes:
        access_token: The JWT or access token string.
        token_type: The type of the token, such as 'bearer'.
    """
    access_token: str
    token_type: str


class DataToken(BaseModel):
    """
    Schema representing a data token.

    Attributes:
        id: Identifier for the token.
    """
    id: Optional[str] = None
    
    
class PostUser(BaseModel):
    """
    Schema for returning user information after creation.

    Attributes:
        email: User's email address.
        created_at: Timestamp when the user was created.

    Config:
        from_attribute: Indicates if the model should support attribute-based population.
    """
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attribute = True
    
