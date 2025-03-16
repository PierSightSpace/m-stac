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
    path: str
    method: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    process_time: float
    timestamp: datetime
