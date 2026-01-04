import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx

from pathlib import Path

# Add backend to sys.path to access app.core.config
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))
from app.core.config import settings

app = FastAPI(title="Demo Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str

@app.get("/")
def root():
    return {"service": "Demo Chatbot", "status": "online", "model": settings.GROQ_MODEL_NAME}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simple chatbot endpoint using Groq.
    """
    print(f"\n--- Chat Request ---")
    print(f"Message: {request.message}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.GROQ_MODEL_NAME,
                    "messages": [{"role": "user", "content": request.message}],
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"Success! Response: {content[:50]}...")
                return ChatResponse(response=content)
            else:
                print(f"Groq API Error ({response.status_code}): {response.text}")
                raise HTTPException(status_code=500, detail=f"Groq error: {response.text}")
                
    except Exception as e:
        print(f"Exception during chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)

