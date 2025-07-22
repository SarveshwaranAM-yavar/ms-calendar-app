from pydantic import BaseModel
from typing import List, Optional

class EventAttendee(BaseModel):
    email: str

class EventRequest(BaseModel):
    subject: str
    content: Optional[str]
    start_time: str  # ISO 8601 format
    end_time: str
    attendees: Optional[List[EventAttendee]] = []
    is_online_meeting: Optional[bool] = False

