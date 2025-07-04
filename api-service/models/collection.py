# Imports
# Standard Library Imports
from sqlalchemy import Column, JSON, String
from database.postgre import Base


############################################################################################################
# Collection Model
############################################################################################################
class Collection(Base):
    """
    Collection model for storing the information of all the collections.
    
    Args:
        Base: Base class for declarative models for SQLAlchemy.
    
    Attributes:
        __tablename__: Name of the table in the database.
        __table_args__: Additional table arguments, such as schema.
        
    """
    __tablename__ = 'collection'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False, default='collection')
    stac_version = Column(String, nullable=False, default='1.0.0')
    description = Column(String, nullable=False)
    license = Column(String, nullable=False)
    title = Column(String, nullable=False)
    extent = Column(JSON, nullable=False)
    links = Column(JSON, nullable=False)
    providers = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"id='{self.id}'"