from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime, date

class LogEntry(BaseModel):
    path: str
    method: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    process_time: float
    timestamp: datetime
