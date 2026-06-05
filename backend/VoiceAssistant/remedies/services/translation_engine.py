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
# SAFE LOAD
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
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# =========================
# TRANSLATION ENGINE
# =========================

def translate_to_english(text: str) -> dict:
    """
    Converts multilingual medical input → English canonical symptoms

    Returns:
    {
        "translated_text": "...",
        "matched_terms": [...],
        "confidence_map": {...}
    }
    """

    text = _clean(text)
    words = set(text.split())

    matched_terms = set()
    confidence_map = {}

    # =========================
    # CORE MATCHING LOGIC
    # =========================

    for canonical, variants in MAPPING.items():

        score = 0

        for v in variants:
            v_clean = v.lower()

            # exact token match
            if v_clean in words:
                score += 3

            # phrase match fallback
            elif v_clean in text:
                score += 1

        if score > 0:
            matched_terms.add(canonical)
            confidence_map[canonical] = score

    # =========================
    # OUTPUT
    # =========================

    return {
        "translated_text": " ".join(list(matched_terms)),
        "matched_terms": list(matched_terms),
        "confidence_map": confidence_map
    }