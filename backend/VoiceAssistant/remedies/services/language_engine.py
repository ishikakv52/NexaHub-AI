# language_engine.py

from langdetect import detect, DetectorFactory
import re

DetectorFactory.seed = 0  # stable results


# =========================
# RULE-BASED OVERRIDES
# =========================

HINGLISH_HINTS = [
    "dard", "bukhar", "khansi", "sir", "body", "feeling",
    "ho raha", "lag raha", "thak", "chakkar"
]

INDIC_HINTS = [
    "ka", "ki", "hai", "me", "main", "se"
]


# =========================
# CLEAN TEXT
# =========================

def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


# =========================
# HINGLISH DETECTION
# =========================

def _is_hinglish(text: str) -> bool:
    t = text.lower()

    score = 0
    for w in HINGLISH_HINTS:
        if w in t:
            score += 1

    for w in INDIC_HINTS:
        if w in t:
            score += 1

    return score >= 2


# =========================
# MAIN FUNCTION
# =========================

def detect_language(text: str) -> dict:
    """
    Returns:
    {
        "language": "en" | "hi" | "hinglish" | "others",
        "raw": detected_lang,
        "confidence": float
    }
    """

    text = _clean(text)

    # ---- 1. Hinglish override ----
    if _is_hinglish(text):
        return {
            "language": "hinglish",
            "raw": "mixed",
            "confidence": 0.85
        }
    
    # ---- 2. langdetect ----
    try:
        lang = detect(text)

        # map normalization
        if lang == "hi":
            return {
                "language": "hi",
                "raw": lang,
                "confidence": 0.9
            }

        if lang == "en":
            return {
                "language": "en",
                "raw": lang,
                "confidence": 0.9
            }

        return {
            "language": "others",
            "raw": lang,
            "confidence": 0.7
        }

    except:
        return {
            "language": "en",
            "raw": "fallback",
            "confidence": 0.5
        }