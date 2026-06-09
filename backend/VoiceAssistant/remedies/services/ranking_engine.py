# ranking_engine.py — Fixed for multilingual remedies format

from .severity_engine import calculate_severity

PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def _extract_en_advice(advice):
    """
    Handles both old list format and new multilingual dict format.
    Always returns a plain list of strings (English).
    """
    if isinstance(advice, dict):
        # New multilingual format: {en: [...], hi: [...], ...}
        return advice.get("en") or []
    if isinstance(advice, list):
        return advice
    if isinstance(advice, str):
        return [advice]
    return []


def rank_recommendations(symptoms: list, remedies: dict):
    """
    Sorts symptoms by severity priority (high → low).
    Returns ranked list — used by views.py for the response payload.
    """
    if not symptoms:
        return []

    severity_data = calculate_severity(symptoms)
    level = severity_data["level"]
    breakdown = severity_data["breakdown"]

    ranked = []
    for symptom in symptoms:
        raw_advice = remedies.get(symptom, [])
        advice_list = _extract_en_advice(raw_advice)

        weight = PRIORITY_WEIGHT.get(level, 1)
        symptom_score = breakdown.get(symptom, 1)
        total_priority = weight + symptom_score

        ranked.append({
            "symptom": symptom,
            "priority": total_priority,
            "severity_level": level,
            "advice": advice_list,
        })

    ranked.sort(key=lambda x: x["priority"], reverse=True)
    return ranked