# Imports
# Standard Library Imports
from typing import Optional
from datetime import datetime

# Third-Party Imports
from pydantic import BaseModel


############################################################################################################
# LogEntry Schemas
############################################################################################################
class LogEntry(BaseModel):
    """
    LogEntry model for storing the API request and response logs.

    Args:
        BaseModel: Base class for pydantic models.
    
    Attributes:
        path: The origin of the request.
        method: HTTP method used for request.
        request_body: Body of the request.
        resposne_body: Body of the resposne.
        process_time: Time taken to process the request.
        timestamp: Timestamp of when the lofg entry was created.

    Returns: 
        None
    """
    path: str
    method: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    process_time: float
    timestamp: datetime
