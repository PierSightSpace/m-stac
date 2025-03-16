# Imports
# Third-Party Imports
from sqlalchemy import Column, Integer, Float, String, DateTime
from database import Base


############################################################################################################
# LogEntry Model
############################################################################################################
class LogEntry(Base):
    __tablename__ = 'log_entry'
    __table_args__ = {'schema': 'stac_metadata'}
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(50), nullable=False)
    method = Column(String(10), nullable=False)
    request_body = Column(String(100), nullable=True)
    response_body = Column(String(255), nullable=True)
    process_time = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"id='{self.id}'"