from sqlalchemy import Column, Integer, Float, String, BigInteger, Date, DateTime, Text
from database import Base
from sqlalchemy_utils import EmailType
from datetime import datetime

class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(EmailType, nullable=False, index=True, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now())