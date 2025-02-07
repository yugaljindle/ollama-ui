#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Astro AI Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "deepseek-r1:1.5b"

class PromptRequest(BaseModel):
    prompt: str
    session_id: str

class GenerationResponse(BaseModel):
    response: str

message_sessions: Dict[str, List[dict]] = {}

@app.post("/generate", response_model=GenerationResponse)
async def generate_response(request: PromptRequest):
    try:
        # Initialize message history for new sessions
        if request.session_id not in message_sessions:
            message_sessions[request.session_id] = []

        message_sessions[request.session_id].append(
            {"role": "user", "content": request.prompt}
        )

        ollama_request = {
            "model": MODEL_NAME,
            "messages": message_sessions[request.session_id],
            "stream": False  # Using non-streaming for simplicity
        }
        
        logger.info(f"Sending request to Ollama with model: {MODEL_NAME}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=ollama_request,
                timeout=300  # 5 minutes
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error from Ollama API"
                )
            
            # Extract the response from Ollama
            result = response.json()
            generated_text = result.get("message", {}).get("content", "")
            
            if not generated_text:
                raise HTTPException(
                    status_code=500,
                    detail="No response generated"
                )
            
            # Add the assistant's response to the session-specific message history
            message_sessions[request.session_id].append({"role": "assistant", "content": generated_text})

            return GenerationResponse(response=generated_text)
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to Ollama timed out"
        )
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
