# Imports
# Standard Library Imports
from datetime import datetime

# Third-Party Imports
from sqlalchemy import Column, Integer, String, DateTime
from database.postgre import Base
from sqlalchemy_utils import EmailType


############################################################################################################
# User Model
############################################################################################################
class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(EmailType, nullable=False, index=True, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now())