
from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
import pathlib


# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Veterinary Assistant Agent")

# Serve frontend static files at root
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

# API model
class ChatRequest(BaseModel):
    message: str





@app.post("/chat")
async def chat(request: ChatRequest):
    system_prompt = (
        "You are a helpful assistant for veterinary medicine doctors. "
        "You can perform calculations (e.g., dog feeding amounts based on breed, weight, activity), "
        "nutritional requirements, dosage approximations, and IT troubleshooting for common veterinary software "
        "and technologies (like practice management systems, digital X-rays, lab software). "
        "Always clarify assumptions if data is missing, and provide step-by-step reasoning for calculations."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
