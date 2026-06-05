import json
import os
import re

# =========================
# PATH SETUP
# =========================

BASE = os.path.dirname(
    os.path.dirname(__file__)
)

PATH = os.path.join(
    BASE,
    "datasets",
    "multilingual_map.json"
)


# =========================
# SAFE LOAD (IMPORTANT)
# =========================

def _load_mapping():
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

MAPPING = _load_mapping()


# =========================
# CLEAN TEXT
# =========================

def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================
# TOKENIZER
# =========================

def _tokens(text: str):
    return set(text.split())


# =========================
# CORE ENGINE
# =========================

def extract_symptoms(text: str):
    """
    Returns:
    {
        "symptoms": [...],
        "confidence_map": {...}
    }
    """

    text = _clean(text)
    tokens = _tokens(text)

    found = set()
    confidence_map = {}

    for symptom, words in MAPPING.items():
        score = 0

        for w in words:
            w_clean = w.lower()

            # token match (safe)
            if w_clean in tokens:
                score += 3

            # phrase match (light fallback)
            elif w_clean in text:
                score += 1

        if score > 0:
            found.add(symptom)
            confidence_map[symptom] = score

    return {
        "symptoms": list(found),
        "confidence_map": confidence_map
    }