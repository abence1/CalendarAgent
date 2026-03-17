from fastapi import APIRouter
from googleapiclient.errors import HttpError
from fastapi import HTTPException
import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from helpers.schemas import EventModel
from helpers.schemas import DeleteModel

router = APIRouter()


SCOPES = ["https://www.googleapis.com/auth/calendar"]

def calendar():
    if not os.path.exists("token.json"):
        raise HTTPException(status_code=401, detail="Not authenticated. Please visit /login")
    
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)



@router.post("/event") 
def add_event(event: EventModel):
    service = calendar()
    event_body = {
        'summary': event.summary,
        'description': event.description,
        'start': {
            'dateTime': event.start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': event.end_time,
            'timeZone': 'UTC',
        },
    }
    try:
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return {"status": "Success", "message": "Event created"}
    except HttpError as e:
        return {"status": "Error", "message": str(e)}

@router.get("/event")
def get_event(name: str):
    service = calendar()
    try:
        events_response = service.events().list(calendarId="primary", q=name, singleEvents=True).execute()
        events = events_response.get("items", [])
        if not events:
            return {"status": "Error", "message": "Event not found!"}
        
        results = []
        for event in events:
            results.append({
                "title": event["summary"],
                "id": event["id"]
            })        
        return {"status": "Success", "matches": results}
    except Exception as e:
        {"status": "Error", "message": str(e)}

@router.delete("/event")
def delete_event(event: DeleteModel):
    service = calendar()
    try:
        service.events().delete(calendarId="primary", eventId=event.id).execute()
        return {"status": "Success", "message": "Event deleted"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}