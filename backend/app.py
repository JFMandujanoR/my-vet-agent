import re
from .calculations import calculate_calories, calculate_food_amount, calculate_dosage

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



@app.post("/query")
async def run_agent(query: Query):
    user_msg = query.message.lower()
    # Detect calorie intake calculation
    cal_match = re.search(r'(calorie|calories|energy).*?(dog|cat|pet)?', user_msg)
    food_match = re.search(r'(food amount|grams|how much food)', user_msg)
    dose_match = re.search(r'(dose|dosage|mg/kg|medication)', user_msg)


    # Example: "How many calories for a 10kg active dog?"
    if cal_match:
        # Extract weight and activity
        weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg)
        activity = 'normal'
        if 'active' in user_msg:
            activity = 'active'
        elif 'senior' in user_msg:
            activity = 'senior'
        species = 'dog' if 'dog' in user_msg else ('cat' if 'cat' in user_msg else None)
        missing = []
        if not weight:
            missing.append("weight in kg")
        if not species:
            missing.append("species (dog or cat)")
        if missing:
            return {"response": f"To calculate calories, please provide: {', '.join(missing)}."}
        weight_kg = float(weight.group(1))
        calories = calculate_calories(weight_kg, activity, species)
        return {"response": f"Estimated daily calories for a {activity} {species} weighing {weight_kg}kg: {calories} kcal/day."}


    # Example: "How much food for 300kcal/day if food is 3.5kcal/g?"
    if food_match:
        cal = re.search(r'(\d+(\.\d+)?)\s?kcal', user_msg)
        kcal_per_g = re.search(r'(\d+(\.\d+)?)\s?kcal/g', user_msg)
        missing = []
        if not cal:
            missing.append("daily calories (kcal)")
        if not kcal_per_g:
            missing.append("food energy (kcal/g)")
        if missing:
            return {"response": f"To calculate food amount, please provide: {', '.join(missing)}."}
        calories_needed = float(cal.group(1))
        food_kcal_per_gram = float(kcal_per_g.group(1))
        grams = calculate_food_amount(calories_needed, food_kcal_per_gram)
        return {"response": f"Amount of food needed: {grams} grams/day for {calories_needed} kcal/day at {food_kcal_per_gram} kcal/g."}


    # Example: "What is the dose for 12kg dog at 5mg/kg?"
    if dose_match:
        weight = re.search(r'(\d+(\.\d+)?)\s?kg', user_msg)
        dose = re.search(r'(\d+(\.\d+)?)\s?mg/kg', user_msg)
        missing = []
        if not weight:
            missing.append("weight (kg)")
        if not dose:
            missing.append("dosage (mg/kg)")
        if missing:
            return {"response": f"To calculate dosage, please provide: {', '.join(missing)}."}
        weight_kg = float(weight.group(1))
        dosage_mg_per_kg = float(dose.group(1))
        total_dose = calculate_dosage(weight_kg, dosage_mg_per_kg)
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
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
        # Use the new OpenAI 1.0+ API
        response = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.message}
            ]
        )
        return {"response": response.choices[0].message.content}

    except Exception as e:
        # Graceful error handling
        return {"error": str(e)}
