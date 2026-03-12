from pydantic import BaseModel

class EventModel(BaseModel):
    summary: str
    description: str
    start_time: str
    end_time: str