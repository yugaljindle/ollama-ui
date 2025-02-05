from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
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
    model_name: Optional[str] = None

class GenerationResponse(BaseModel):
    response: str

@app.post("/generate", response_model=GenerationResponse)
async def generate_response(request: PromptRequest):
    try:
        # Use specified model or fall back to default
        model = request.model_name or MODEL_NAME
        
        # Prepare the request to Ollama
        ollama_request = {
            "model": model,
            "prompt": request.prompt,
            "stream": False  # We'll use non-streaming for simplicity
        }
        
        logger.info(f"Sending request to Ollama with model: {model}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=ollama_request,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error from Ollama API"
                )
            
            # Extract the response from Ollama
            result = response.json()
            generated_text = result.get("response", "")
            
            if not generated_text:
                raise HTTPException(
                    status_code=500,
                    detail="No response generated"
                )
            
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
