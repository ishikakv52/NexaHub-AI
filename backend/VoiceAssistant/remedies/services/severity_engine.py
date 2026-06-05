# severity_engine.py

# =========================
# SEVERITY MAP (CAN BE MOVED TO JSON LATER)
# =========================

SEVERITY_MAP = {
    # LOW
    "cold": 1,
    "cough": 1,
    "headache": 1,
    "fatigue": 1,

    # MEDIUM
    "fever": 2,
    "dizziness": 2,
    "vomiting": 2,
    "stomach_pain": 2,
    "diarrhea": 2,
    "sore_throat": 2,

    # HIGH (EMERGENCY RISK)
    "chest_pain": 3,
    "breathing_difficulty": 3,
    "unconsciousness": 3,
    "severe_bleeding": 3,
    "stroke_symptoms": 3
}


# =========================
# SEVERITY ENGINE
# =========================

def calculate_severity(symptoms: list):
    """
    Returns:
    {
        "score": int,
        "level": "low" | "medium" | "high",
        "breakdown": {symptom: score}
    }
    """

    if not symptoms:
        return {
            "score": 0,
            "level": "low",
            "breakdown": {}
        }

    total_score = 0
    breakdown = {}

    for s in symptoms:
        score = SEVERITY_MAP.get(s, 1)  # default low risk
        breakdown[s] = score
        total_score += score

    # =========================
    # NORMALIZE LEVEL
    # =========================

    if total_score <= 2:
        level = "low"
    elif total_score <= 4:
        level = "medium"
    else:
        level = "high"

    return {
        "score": total_score,
        "level": level,
        "breakdown": breakdown
    }