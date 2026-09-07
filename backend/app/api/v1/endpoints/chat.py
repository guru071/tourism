from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from typing import List, Dict

from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@router.post("")
async def chat_with_assistant(payload: ChatRequest):
    """Real-time AI chatbot endpoint for the frontend assistant."""
    if not settings.GEMINI_API_KEY:
        return {"reply": "I am currently operating in offline mode. Please configure the GEMINI_API_KEY in the backend to enable AI conversations."}
    
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert history to Gemini format
        formatted_history = []
        for msg in payload.history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
            
        chat = model.start_chat(history=formatted_history)
        
        system_prompt = (
            "You are a professional, helpful travel assistant for the AI Tourism Ecosystem. "
            "Maintain a strictly professional tone. Do not use any emojis. "
            "Help the user with destination recommendations, itinerary adjustments, and travel advice."
        )
        
        # We inject the system prompt transparently if this is the first message
        if not formatted_history:
            full_message = f"{system_prompt}\n\nUser Question: {payload.message}"
        else:
            full_message = payload.message
            
        response = chat.send_message(full_message)
        
        return {"reply": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")
