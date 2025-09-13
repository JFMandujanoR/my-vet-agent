from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Veterinary Assistant Agent")

class Query(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Veterinary Assistant Agent is running. Use POST /query to interact."}

@app.post("/query")
async def run_agent(query: Query):
    system_prompt = (
        "You are a helpful assistant for veterinary medicine doctors. "
        "You can perform calculations (e.g., dog feeding amounts based on breed, weight, activity), "
        "nutritional requirements, dosage approximations, and IT troubleshooting for common veterinary software "
        "and technologies (like practice management systems, digital X-rays, lab software). "
        "Always clarify assumptions if data is missing, and provide step-by-step reasoning for calculations."
    )
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query.message}
        ]
    )
    return {"response": completion.choices[0].message["content"]}
