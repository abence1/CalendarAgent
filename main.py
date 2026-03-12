import datetime as dt
import os.path
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ["https://www.googleapis.com/auth/calendar"]

app = FastAPI()

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
            
            authorization_url, state =  flow.authorization_url(access_type="offline", include_granted_scopes="true", code_challenge=None)

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
