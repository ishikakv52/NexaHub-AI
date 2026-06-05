import json
import os

# =========================
# PATH SETUP
# =========================

BASE = os.path.dirname(
    os.path.dirname(__file__)
)

DATA_DIR = os.path.join(BASE, "datasets")

SYMPTOMS_PATH = os.path.join(DATA_DIR, "symptoms.json")
REMEDIES_PATH = os.path.join(DATA_DIR, "remedies.json")
EMERGENCY_PATH = os.path.join(DATA_DIR, "emergency.json")


# =========================
# SAFE LOADERS
# =========================

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

SYMPTOMS_DATA = _load_json(SYMPTOMS_PATH)
REMEDIES_DATA = _load_json(REMEDIES_PATH)
EMERGENCY_DATA = _load_json(EMERGENCY_PATH)


# =========================
# EMERGENCY CHECK (PRIORITY 1)
# =========================

def check_emergency(symptoms: list):
    """
    Returns emergency message if any symptom is critical
    """

    for s in symptoms:
        if s in EMERGENCY_DATA:
            return {
                "emergency": True,
                "symptom": s,
                "message": EMERGENCY_DATA[s]
            }

    return {
        "emergency": False
    }


# =========================
# REMEDY FETCH
# =========================

def get_remedies(symptoms: list):
    """
    Returns remedies for given symptoms
    """

    result = {}

    for s in symptoms:
        if s in REMEDIES_DATA:
            result[s] = REMEDIES_DATA[s]

    return result


# =========================
# MAIN ENGINE
# =========================

def retrieve(symptoms: list):
    """
    FINAL RESPONSE BUILDER

    Returns:
    {
        "emergency": {...} or None,
        "remedies": {...},
        "status": "ok" | "emergency"
    }
    """

    if not symptoms:
        return {
            "status": "ok",
            "remedies": {},
            "message": "No symptoms detected"
        }

    # 1. Emergency check
    emergency = check_emergency(symptoms)

    if emergency["emergency"]:
        return {
            "status": "emergency",
            "emergency": emergency,
            "remedies": {},
            "message": emergency["message"]
        }

    # 2. Remedies fetch
    remedies = get_remedies(symptoms)

    return {
        "status": "ok",
        "symptoms": symptoms,
        "remedies": remedies,
        "message": "Remedies fetched successfully"
    }