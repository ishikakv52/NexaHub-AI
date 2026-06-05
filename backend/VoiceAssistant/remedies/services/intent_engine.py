# intent_engine.py

import re

# =========================
# CONFIG (scalable vocab)
# =========================

MEDICAL_WORDS = {
    "high": [
        "pain", "fever", "dard", "ache", "symptom", "injury",
        "vomiting", "nausea", "breathlessness", "infection",
        "chest pain", "headache", "migraine", "cough",
        "bukhar", "khansi", "sardi", "sir dard"
    ],
    "medium": [
        "tired", "weak", "dizzy", "burning", "cramp"
    ],
    "low": [
        "not feeling well", "unwell", "off"
    ]
}

NON_MEDICAL_WORDS = [
    "movie", "song", "code", "study", "weather",
    "game", "news", "sports", "technology"
]


# =========================
# CLEAN TEXT
# =========================

def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)   # remove punctuation
    text = re.sub(r"\s+", " ", text)
    return text


# =========================
# INTENT DETECTOR
# =========================

def detect_intent(text: str) -> dict:
    """
    Returns:
    {
        "intent": "medical" | "general",
        "confidence": float (0-1),
        "score": int
    }
    """

    t = _normalize(text)

    medical_score = 0
    non_medical_score = 0

    # ---- medical scoring (weighted) ----
    for word in MEDICAL_WORDS["high"]:
        if word in t:
            medical_score += 3

    for word in MEDICAL_WORDS["medium"]:
        if word in t:
            medical_score += 2

    for word in MEDICAL_WORDS["low"]:
        if word in t:
            medical_score += 1

    # ---- non-medical scoring ----
    for word in NON_MEDICAL_WORDS:
        if word in t:
            non_medical_score += 2

    # =========================
    # DECISION LOGIC
    # =========================

    total = medical_score + non_medical_score + 1e-6
    confidence = medical_score / total

    intent = "medical" if medical_score > non_medical_score else "general"

    return {
        "intent": intent,
        "confidence": round(confidence, 3),
        "score": medical_score - non_medical_score
    }