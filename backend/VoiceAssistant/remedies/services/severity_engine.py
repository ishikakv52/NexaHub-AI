# severity_engine.py — Expanded severity map with new conditions

SEVERITY_MAP = {
    # LOW
    "cold": 1, "cough": 1, "headache": 1, "fatigue": 1,
    "constipation": 1, "insomnia": 1, "skin_rash": 1,
    "toothache": 1, "ear_problem": 1, "eye_problem": 1,
    "sinusitis": 1, "anxiety": 1,

    # MEDIUM
    "fever": 2, "dizziness": 2, "vomiting": 2, "stomach_pain": 2,
    "diarrhea": 2, "sore_throat": 2, "body_pain": 2, "back_pain": 2,
    "joint_pain": 2, "acidity": 2, "migraine": 2,

    # HIGH (EMERGENCY RISK)
    "chest_pain": 3, "breathing_difficulty": 3, "unconsciousness": 3,
    "severe_bleeding": 3, "stroke_symptoms": 3,
    "high_bp": 3, "low_bp": 2, "high_sugar": 3, "low_sugar": 3,
    "high_heart_rate": 3, "low_heart_rate": 3, "low_spo2": 3,
    "dengue_symptoms": 3, "malaria_symptoms": 3, "typhoid_symptoms": 3,
    "jaundice": 2, "diabetes_symptoms": 2, "kidney_problem": 2,
}


def calculate_severity(symptoms: list):
    if not symptoms:
        return {"score": 0, "level": "low", "breakdown": {}}

    total_score = 0
    breakdown = {}
    for s in symptoms:
        score = SEVERITY_MAP.get(s, 1)
        breakdown[s] = score
        total_score += score

    if total_score <= 2:   level = "low"
    elif total_score <= 5: level = "medium"
    else:                  level = "high"

    return {"score": total_score, "level": level, "breakdown": breakdown}