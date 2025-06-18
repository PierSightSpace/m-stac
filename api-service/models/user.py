# Imports
# Standard Library Imports
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_utils import EmailType

# Local Imports
from database.postgre import Base


############################################################################################################
# User Model
############################################################################################################
class User(Base):
    """
    User model for storing user information in a Postgre database.

    Args:
        Base: Base class for declarative models for SQLAlchemy.
    
    Attributes:
        __tablename__: Name of the table in the database.
        __table_args__: Additional table arguments, such as schema.
        id: Primary key of the user.
        email: Email address of the user (unique).
        password: Password of the user.
        created_at: Timestamp of the user's registration.
    
    Returns: 
        None
    """
    __tablename__ = 'user'
    __table_args__ = {'schema': 'piersight_stac'}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(EmailType, nullable=False, index=True, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now())