from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from google import genai
import os

from helpers.schemas import PromptRequest

load_dotenv()

router = APIRouter()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@router.post("/ask-gemini")
async def ask_gemini(request: PromptRequest):
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=request.prompt
        )

        return {"status": "Success", "message": response.text}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

