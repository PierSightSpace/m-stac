# Imports
# Third-Party Imports
from sqlalchemy import Column, Integer, Float, String, DateTime
from database.postgre import Base


############################################################################################################
# LogEntry Model
############################################################################################################
class LogEntry(Base):
    """
    LogEntry model for storing log entries in a Postgre database.

    Args:
        Base: Base class for declarative models for SQLAlchemy.
    
    Attributes:
        __tablename__: Name of the table in the database.
        __table_args__: Additional table arguments, such as schema.
        id: Primary key of the log entry.
        path: The origin of the request.
        method: HTTP method used for request.
        request_body: Body of the request.
        resposne_body: Body of the resposne.
        process_time: Time taken to process the request.
        timestamp: Timestamp of when the lofg entry was created.

    Returns:
        None
    """
    __tablename__ = 'log_entry'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(256), nullable=False)
    method = Column(String(10), nullable=False)
    request_body = Column(String(100), nullable=True)
    response_body = Column(String(256), nullable=True)
    process_time = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"id='{self.id}'"