
from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = FastAPI(title="Veterinary Assistant Agent")

# Mount frontend static files at /frontend
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


class Query(BaseModel):
    message: str


# Serve index.html at root
@app.get("/")
async def serve_index():
    return FileResponse(frontend_path / "index.html")

@app.get("/check_key")
async def check_key():
    return {"OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/query")
async def run_agent(query: Query):
    system_prompt = (
        "You are a helpful assistant for veterinary medicine doctors. "
        "You can perform calculations (e.g., dog feeding amounts based on breed, weight, activity), "
        "nutritional requirements, dosage approximations, and IT troubleshooting for common veterinary software "
        "and technologies (like practice management systems, digital X-rays, lab software). "
        "Always clarify assumptions if data is missing, and provide step-by-step reasoning for calculations."
    )
    
    try:
        # Use the new OpenAI 1.0+ API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.message}
            ]
        )
        return {"response": response.choices[0].message.content}

    except Exception as e:
        # Graceful error handling
        return {"error": str(e)}
