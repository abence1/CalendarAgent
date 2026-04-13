from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import datetime     
from helpers.schemas import PromptRequest, EventModel
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
load_dotenv()

router = APIRouter()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

def add_event(summary: str, description: str, start_time: str, end_time: str):
    service = calendar()
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/Budapest',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Budapest',
        },
    }
    try:
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return {"status": "Success", "message": "Event created"}
    except HttpError as e:
        return {"status": "Error", "message": str(e)}

@router.post("/ask-gemini")
async def ask_gemini(request: PromptRequest):
    try:
        today = datetime.datetime.now().strftime("%A, %B, %d, %Y")
        context = f"You are a calendar assistant. When asked to add an event, do not check for existing events or list current events. Just call the add_event function directly with the provided information. Today is {today}"
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=context + request.prompt,
            config=types.GenerateContentConfig(
                tools=[add_event],
                automatic_function_calling={"disable": False}
            )
        )

        return {"status": "Success", "message": response.text}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

