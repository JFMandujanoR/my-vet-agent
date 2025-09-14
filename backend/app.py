from fastapi import Request, Response, Cookie, Depends
import uuid
# Session memory bank
session_memory = {}

def get_session_id(request: Request, session_id: str = Cookie(None)):
    if not session_id:
        # Generate a new session ID
        session_id = str(uuid.uuid4())
    return session_id
import re
from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib
from .calculations import calculate_calories, calculate_food_amount, calculate_dosage

# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Veterinary Assistant Agent")

# Mount frontend static files at /frontend
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")

# Serve index.html at root
@app.get("/")
async def serve_index():
    return FileResponse(frontend_path / "index.html")
class Query(BaseModel):
    message: str

@app.post("/query")
async def run_agent(query: Query, request: Request, response: Response, session_id: str = Depends(get_session_id)):
    user_msg = query.message.lower()
    # Get or create session memory
    memory = session_memory.get(session_id, {})
    # Detect calculation intent or missing info
    cal_match = re.search(r'(calorie|calories|energy).*?(dog|cat|pet)?', user_msg) or memory.get('calorie_intent')
    food_match = re.search(r'(food amount|grams|how much food)', user_msg) or memory.get('food_intent')
    dose_match = re.search(r'(dose|dosage|mg/kg|medication)', user_msg) or memory.get('dose_intent')
    # If user only provides missing info, check memory for previous intent
    if not (cal_match or food_match or dose_match):
        # Try to infer what the user is providing
        if 'weight in kg' in memory.get('missing', []):
            weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg)
            if weight:
                memory['weight'] = weight
                cal_match = memory.get('calorie_intent')
        if 'species (dog or cat)' in memory.get('missing', []):
            if 'dog' in user_msg:
                memory['species'] = 'dog'
                cal_match = memory.get('calorie_intent')
            elif 'cat' in user_msg:
                memory['species'] = 'cat'
                cal_match = memory.get('calorie_intent')
        if 'daily calories (kcal)' in memory.get('missing', []):
            cal = re.search(r'(\d+(\.\d+)?)\s?kcal', user_msg)
            if cal:
                memory['calories_needed'] = cal
                food_match = memory.get('food_intent')
        if 'food energy (kcal/g)' in memory.get('missing', []):
            kcal_per_g = re.search(r'(\d+(\.\d+)?)\s?kcal/g', user_msg)
            if kcal_per_g:
                memory['food_kcal_per_gram'] = kcal_per_g
                food_match = memory.get('food_intent')
        if 'weight (kg)' in memory.get('missing', []):
            weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg)
            if weight:
                memory['weight'] = weight
                dose_match = memory.get('dose_intent')
        if 'dosage (mg/kg)' in memory.get('missing', []):
            dose = re.search(r'(\d+(\.\d+)?)\s?mg/kg', user_msg)
            if dose:
                memory['dosage_mg_per_kg'] = dose
                dose_match = memory.get('dose_intent')


    # Example: "How many calories for a 10kg active dog?"
    if cal_match:
        # Extract weight and activity
        weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg) or memory.get('weight')
        activity = 'normal'
        if 'active' in user_msg:
            activity = 'active'
        elif 'senior' in user_msg:
            activity = 'senior'
        else:
            activity = memory.get('activity', 'normal')
        species = 'dog' if 'dog' in user_msg else ('cat' if 'cat' in user_msg else memory.get('species'))
        missing = []
        if not weight:
            missing.append("weight in kg")
        if not species:
            missing.append("species (dog or cat)")
        if missing:
            # Store what info we have and intent
            if weight:
                memory['weight'] = weight
            if activity:
                memory['activity'] = activity
            if species:
                memory['species'] = species
            memory['calorie_intent'] = True
            memory['missing'] = missing
            session_memory[session_id] = memory
            response.set_cookie(key="session_id", value=session_id)
            return {"response": f"To calculate calories, please provide: {', '.join(missing)}."}
        weight_kg = float(weight.group(1)) if hasattr(weight, 'group') else float(weight)
        calories = calculate_calories(weight_kg, activity, species)
        session_memory.pop(session_id, None)
        response.set_cookie(key="session_id", value=session_id)
        return {"response": f"Estimated daily calories for a {activity} {species} weighing {weight_kg}kg: {calories} kcal/day."}


    # Example: "How much food for 300kcal/day if food is 3.5kcal/g?"
    if food_match:
        cal = re.search(r'(\d+(\.\d+)?)\s?kcal', user_msg) or memory.get('calories_needed')
        kcal_per_g = re.search(r'(\d+(\.\d+)?)\s?kcal/g', user_msg) or memory.get('food_kcal_per_gram')
        missing = []
        if not cal:
            missing.append("daily calories (kcal)")
        if not kcal_per_g:
            missing.append("food energy (kcal/g)")
        if missing:
            if cal:
                memory['calories_needed'] = cal
            if kcal_per_g:
                memory['food_kcal_per_gram'] = kcal_per_g
            memory['food_intent'] = True
            memory['missing'] = missing
            session_memory[session_id] = memory
            response.set_cookie(key="session_id", value=session_id)
            return {"response": f"To calculate food amount, please provide: {', '.join(missing)}."}
        calories_needed = float(cal.group(1)) if hasattr(cal, 'group') else float(cal)
        food_kcal_per_gram = float(kcal_per_g.group(1)) if hasattr(kcal_per_g, 'group') else float(kcal_per_g)
        grams = calculate_food_amount(calories_needed, food_kcal_per_gram)
        session_memory.pop(session_id, None)
        response.set_cookie(key="session_id", value=session_id)
        return {"response": f"Amount of food needed: {grams} grams/day for {calories_needed} kcal/day at {food_kcal_per_gram} kcal/g."}


    # Example: "What is the dose for 12kg dog at 5mg/kg?"
    if dose_match:
        weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg) or memory.get('weight')
        dose = re.search(r'(\d+(\.\d+)?)\s?mg/kg', user_msg) or memory.get('dosage_mg_per_kg')
        missing = []
        if not weight:
            missing.append("weight (kg)")
        if not dose:
            missing.append("dosage (mg/kg)")
        if missing:
            if weight:
                memory['weight'] = weight
            if dose:
                memory['dosage_mg_per_kg'] = dose
            memory['dose_intent'] = True
            memory['missing'] = missing
            session_memory[session_id] = memory
            response.set_cookie(key="session_id", value=session_id)
            return {"response": f"To calculate dosage, please provide: {', '.join(missing)}."}
        weight_kg = float(weight.group(1)) if hasattr(weight, 'group') else float(weight)
        dosage_mg_per_kg = float(dose.group(1)) if hasattr(dose, 'group') else float(dose)
        total_dose = calculate_dosage(weight_kg, dosage_mg_per_kg)
        session_memory.pop(session_id, None)
        response.set_cookie(key="session_id", value=session_id)
        return {"response": f"Total dosage: {total_dose} mg for {weight_kg}kg at {dosage_mg_per_kg} mg/kg."}

    # Otherwise, fallback to GPT
    system_prompt = (
        "You are a highly reliable, evidence-focused assistant for veterinary medicine professionals. "
        "Prioritize accuracy, transparency, and patient safety above all. "
        "Do not invent facts, drug names, dosages, protocols, citations, or product details. "
        "If a factual claim, dosage, or clinical recommendation cannot be supported by a known, high-quality source, "
        "explicitly say you do not have a reliable reference and refuse to fabricate one. "
        "When possible, retrieve and cite up-to-date primary sources (drug labels, manufacturer instructions, peer-reviewed journals, official guidelines or formulary references). "
        "When up-to-date references are not available, clearly state the knowledge cutoff or lack of live sources. "
        "\n\n"
        "For clinical or pharmacologic questions (e.g., dosage approximations, drug interactions, emergency treatment):\n"
        "- Require the following explicit inputs before giving a numeric dosage: species, patient weight (with units), age, pregnancy/lactation status, route of administration, formulation/concentration, and relevant comorbidities or concurrent drugs. "
        "- If any required input is missing, ask for it; do not guess. If the user instructs you to assume a value, list that assumption explicitly. "
        "- Provide calculations step-by-step: show the formula, substitute numeric values, show the arithmetic digit-by-digit, show unit conversions, and show the final numeric answer with units and chosen rounding rule. "
        "- Give a conservative recommended range (min–max) when appropriate, and explicitly state which value you consider safest and why. "
        "- Add safety checks and contraindications (e.g., dose limits, species-specific warnings), and advise confirmation against a primary source (drug label, formulary, or pharmacist). "
        "- Always end clinical answers with: a short summary, explicit citations or 'no reliable citation found', and a recommended next action (e.g., verify with product label, contact toxicology/poison control, consult the attending veterinarian). "
        "\n\n"
        "For nutritional or feeding calculations:\n"
        "- Ask for species, age, body condition score or target weight, activity level, and diet composition (calories per unit or label). "
        "- Show daily energy requirement formula used (e.g., RER, MER), all constants, and the final kcal/day and grams/day with conversions and rounding. "
        "\n\n"
        "For IT troubleshooting related to veterinary software/hardware:\n"
        "- Ask for platform, OS/version, software name and version, error messages/log excerpts, and recent changes. "
        "- Do not guess environment details; propose reproducible diagnostic steps and clearly label each command/step. "
        "\n\n"
        "General behavior rules:\n"
        "- Use conservative language when uncertain: label statements as 'Well-supported', 'Plausible but unverified', or 'Speculative'. "
        "- Provide a numeric or qualitative confidence indicator (High / Moderate / Low) with the reason. "
        "- If asked for information outside veterinary scope, or for illegal/unethical instructions, refuse and offer safe alternatives. "
        "- Prefer primary, authoritative sources. If you quote or paraphrase a source, include a citation (title, author, year, or URL when available) and do not fabricate bibliographic details. "
        "\n\n"
        "Preferred output format (use consistently):\n"
        "1) One-line clinical summary / quick answer\n"
        "2) Assumptions & missing data (explicit)\n"
        "3) Step-by-step calculations (formula, substitution, arithmetic, units)\n"
        "4) Final result (value with units) + rounding rule\n"
        "5) Safety/contraindications, caveats\n"
        "6) Sources / citation list (or 'no reliable citation found')\n"
        "7) Confidence level (High/Moderate/Low) + why\n"
        "8) Recommended next steps (verify with label, contact specialist, etc.)"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.message}
            ]
        )
        if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0], 'message'):
            return {"response": response.choices[0].message.content}
        else:
            return {"response": "Sorry, the AI could not generate a response. Please try again later or check your API key."}
    except Exception as e:
        return {"response": f"Sorry, there was an error with the AI service: {str(e)}"}
