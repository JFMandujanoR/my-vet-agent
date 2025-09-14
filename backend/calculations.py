def calculate_calories(weight_kg, activity_level='normal', species='dog'):
    # Simple formula for dogs and cats (can be improved)
    # Resting Energy Requirement (RER): 70 * (weight_kg ** 0.75)
    rer = 70 * (weight_kg ** 0.75)
    if activity_level == 'active':
        multiplier = 2.0
    elif activity_level == 'senior':
        multiplier = 1.2
    else:
        multiplier = 1.6
    return round(rer * multiplier, 2)

def calculate_food_amount(calories_needed, food_kcal_per_gram):
    # Amount of food in grams
    if food_kcal_per_gram <= 0:
        return None
    return round(calories_needed / food_kcal_per_gram, 2)

def calculate_dosage(weight_kg, dosage_mg_per_kg):
    # Dosage in mg
    return round(weight_kg * dosage_mg_per_kg, 2)
