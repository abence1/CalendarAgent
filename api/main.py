import datetime as dt
import os.path
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from schemas import EventModel
from schemas import DeleteModel

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ["https://www.googleapis.com/auth/calendar"]

app = FastAPI()

def calendar():
    if not os.path.exists("token.json"):
        raise HTTPException(status_code=401, detail="Not authenticated. Please visit /login")
    
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


@app.get("/login")
def login():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        else:
            flow = Flow.from_client_secrets_file("credentials.json", scopes=SCOPES, redirect_uri="http://localhost:8000/auth")
            
            authorization_url, state =  flow.authorization_url(access_type="offline", include_granted_scopes="true", code_challenge=None, prompt="consent")

            return RedirectResponse(authorization_url)

@app.get("/auth")
def auth(request: Request):
    try:
        flow = Flow.from_client_secrets_file("credentials.json", scopes=SCOPES, redirect_uri="http://localhost:8000/auth")
        flow.fetch_token(authorization_response=str(request.url))
        creds = flow.credentials
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        return {"status": "Success", "message": "Calendar access granted!"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@app.post("/event") 
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

@app.get("/event")
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

@app.delete("/event")
def delete_event(event: DeleteModel):
    service = calendar()
    try:
        service.events().delete(calendarId="primary", eventId=event.id).execute()
        return {"status": "Success", "message": "Event deleted"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
