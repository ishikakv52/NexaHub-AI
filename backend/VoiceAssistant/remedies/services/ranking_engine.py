# ranking_engine.py

from .severity_engine import calculate_severity

# =========================
# REMEDY PRIORITY RULES
# =========================

PRIORITY_WEIGHT = {
    "high": 3,
    "medium": 2,
    "low": 1
}


# =========================
# RANKING ENGINE
# =========================

def rank_recommendations(symptoms: list, remedies: dict):
    """
    Input:
        symptoms → list of detected symptoms
        remedies → dict from retrieval_engine

    Output:
        sorted recommendations (high → low priority)
    """

    if not symptoms:
        return []

    # Get severity info
    severity_data = calculate_severity(symptoms)

    level = severity_data["level"]
    breakdown = severity_data["breakdown"]

    ranked = []

    for symptom in symptoms:

        advice_list = remedies.get(symptom, [])

        if isinstance(advice_list, str):
            advice_list = [advice_list]

        weight = PRIORITY_WEIGHT.get(level, 1)
        symptom_score = breakdown.get(symptom, 1)

        total_priority = weight + symptom_score

        ranked.append({
            "symptom": symptom,
            "priority": total_priority,
            "severity_level": level,
            "advice": advice_list
        })

    # =========================
    # SORT BY PRIORITY (DESC)
    # =========================

    ranked.sort(key=lambda x: x["priority"], reverse=True)

    return ranked