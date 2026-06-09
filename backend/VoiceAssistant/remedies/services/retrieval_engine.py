# retrieval_engine.py — Fixed emergency message extraction for multilingual dict

import json
import os

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, "datasets")

SYMPTOMS_PATH  = os.path.join(DATA_DIR, "symptoms.json")
REMEDIES_PATH  = os.path.join(DATA_DIR, "remedies.json")
EMERGENCY_PATH = os.path.join(DATA_DIR, "emergency.json")


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

SYMPTOMS_DATA  = _load_json(SYMPTOMS_PATH)
REMEDIES_DATA  = _load_json(REMEDIES_PATH)
EMERGENCY_DATA = _load_json(EMERGENCY_PATH)


def check_emergency(symptoms: list):
    """
    Returns emergency dict if any symptom is critical.
    Handles both old (string) and new (nested dict with multilingual messages) formats.
    """
    for s in symptoms:
        if s in EMERGENCY_DATA:
            entry = EMERGENCY_DATA[s]
            # New format: {"action": ..., "message": {"en": ..., "hi": ...}}
            if isinstance(entry, dict) and "message" in entry:
                msg = entry["message"]  # this is the multilingual dict
            else:
                msg = entry  # old plain string format
            return {
                "emergency": True,
                "symptom": s,
                "action": entry.get("action", "CALL_EMERGENCY") if isinstance(entry, dict) else "CALL_EMERGENCY",
                "message": msg,   # multilingual dict OR plain string
            }
    return {"emergency": False}


def get_remedies(symptoms: list):
    result = {}
    for s in symptoms:
        if s in REMEDIES_DATA:
            result[s] = REMEDIES_DATA[s]
    return result


def retrieve(symptoms: list):
    if not symptoms:
        return {
            "status": "ok",
            "remedies": {},
            "message": "No symptoms detected",
        }

    emergency = check_emergency(symptoms)

    if emergency["emergency"]:
        return {
            "status": "emergency",
            "emergency": emergency,
            "remedies": {},
            "message": emergency["message"],
        }

    remedies = get_remedies(symptoms)

    return {
        "status": "ok",
        "symptoms": symptoms,
        "remedies": remedies,
        "message": "Remedies fetched successfully",
    }