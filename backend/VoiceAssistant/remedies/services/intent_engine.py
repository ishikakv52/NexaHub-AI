# intent_engine.py — Extended with vitals and fever intents

import re

MEDICAL_WORDS = {
    "high": [
        "pain", "fever", "dard", "ache", "symptom", "injury",
        "vomiting", "nausea", "breathlessness", "infection",
        "chest pain", "headache", "migraine", "cough",
        "bukhar", "khansi", "sardi", "sir dard",
        # vitals
        "bp", "blood pressure", "sugar", "glucose", "heart rate",
        "bpm", "spo2", "oxygen", "heartrate", "pulse",
        "raktachaap", "raktdaab", "madhumeh",
        # new diseases
        "dengue", "malaria", "typhoid", "jaundice", "diarrhea",
        "rash", "khujli", "anxiety", "panic",
    ],
    "medium": [
        "tired", "weak", "dizzy", "burning", "cramp",
        "thakan", "kamzori", "chakkar",
    ],
    "low": [
        "not feeling well", "unwell", "off", "tension",
    ],
}

NON_MEDICAL_WORDS = [
    "movie", "song", "code", "study", "weather",
    "game", "news", "sports", "technology",
]

FEVER_INTENT_WORDS = ["fever", "bukhar", "taap", "jwar", "temperature", "high temp"]
VITALS_INTENT_WORDS = ["bp", "blood pressure", "sugar", "glucose", "bpm", "heart rate", "spo2", "oxygen", "pulse"]


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_intent(text: str) -> dict:
    t = _normalize(text)
    medical_score = 0
    non_medical_score = 0

    for word in MEDICAL_WORDS["high"]:
        if word in t:
            medical_score += 3
    for word in MEDICAL_WORDS["medium"]:
        if word in t:
            medical_score += 2
    for word in MEDICAL_WORDS["low"]:
        if word in t:
            medical_score += 1
    for word in NON_MEDICAL_WORDS:
        if word in t:
            non_medical_score += 2

    # Sub-intent detection
    sub_intent = "general_medical"
    for w in FEVER_INTENT_WORDS:
        if w in t:
            sub_intent = "fever"
            break
    if sub_intent == "general_medical":
        for w in VITALS_INTENT_WORDS:
            if w in t:
                sub_intent = "vitals"
                break

    total = medical_score + non_medical_score + 1e-6
    confidence = medical_score / total
    intent = "medical" if medical_score > non_medical_score else "general"

    return {
        "intent": intent,
        "sub_intent": sub_intent,
        "confidence": round(confidence, 3),
        "score": medical_score - non_medical_score,
    }