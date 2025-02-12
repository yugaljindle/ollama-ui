#!/usr/bin/env python3

import configparser
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel
from typing import Dict, List

config = configparser.ConfigParser()
config.read('../config.ini')

# Configuration
APP_NAME = config["common"]["app_name"]
SERVER_PORT = int(config["server"]["port"])
OLLAMA_BASE_URL = config["server"]["ollama_base_url"]
MODEL_NAME = config["server"]["model_name"]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=f"{APP_NAME} Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            message_sessions[request.session_id].append(
                {"role": "assistant", "content": generated_text})

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
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
