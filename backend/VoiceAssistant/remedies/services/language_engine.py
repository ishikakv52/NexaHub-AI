# language_engine.py — Fixed: short English medical phrases correctly detected

from langdetect import detect, DetectorFactory
import re

DetectorFactory.seed = 0

HINGLISH_HINTS = [
    "dard","bukhar","khansi","thakan","chakkar","ulti","dast","khujli",
    "ho raha","lag raha","ho gayi","mujhe","kya","nahi","bahut","thoda",
    "abhi","doctor","hai","gale","kamar","seene","sans","badan","neend",
    "sugar","bp","oxygen","dhadkan","peeth","jodo","daant","kaan","aankh",
]
HINDI_HINTS = [
    "मुझे","बुखार","दर्द","सिरदर्द","पेट","खांसी","ताप","उल्टी","चक्कर",
    "थकान","कमज़ोरी","खुजली","सांस","सीने","कमर","जोड़","दांत","कान",
]
MARATHI_HINTS = [
    "मला","ताप","डोकेदुखी","पोटदुखी","खोकला","थकवा","श्वास","उलटी","आहे","करा","घ्या","प्या",
]
ENGLISH_MEDICAL = [
    "fever","cold","cough","headache","pain","ache","tired","dizzy","vomit",
    "nausea","breath","chest","stomach","throat","back","joint","rash","anxiety",
    "sugar","pressure","oxygen","heart","pulse","blood","sore","weak","swollen",
    "sneeze","runny","blocked","cramp","burning","itching","swelling","infection",
    "I have","I am","my","feel","feeling","hurts","hurt",
]

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def _has_devanagari(text: str) -> bool:
    return sum(1 for c in text if "\u0900" <= c <= "\u097F") > 2

def _has_gujarati(text: str) -> bool:
    return sum(1 for c in text if "\u0A80" <= c <= "\u0AFF") > 2

def _is_marathi(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in MARATHI_HINTS)

def _is_hinglish(text: str) -> bool:
    t = _clean(text)
    score = sum(1 for w in HINGLISH_HINTS if w in t)
    return score >= 1

def _is_english_medical(text: str) -> bool:
    t = _clean(text)
    return any(w in t for w in ENGLISH_MEDICAL)

def detect_language(text: str) -> dict:
    # Script-based (most reliable)
    if _has_gujarati(text):
        return {"language": "gu", "raw": "gu", "confidence": 0.95}
    if _has_devanagari(text):
        if _is_marathi(text):
            return {"language": "mr", "raw": "mr", "confidence": 0.92}
        return {"language": "hi", "raw": "hi", "confidence": 0.92}

    # Hinglish (Latin-script Hindi/mixed)
    if _is_hinglish(text):
        return {"language": "hinglish", "raw": "mixed", "confidence": 0.85}

    # English medical phrases — override langdetect for short phrases
    if _is_english_medical(text):
        return {"language": "en", "raw": "en", "confidence": 0.88}

    # langdetect fallback for longer text
    try:
        lang = detect(_clean(text))
        lang_map = {"hi": "hi", "mr": "mr", "gu": "gu", "en": "en"}
        mapped = lang_map.get(lang)
        if mapped:
            return {"language": mapped, "raw": lang, "confidence": 0.9}
        # If langdetect gives garbage on short text, default to English
        return {"language": "en", "raw": lang, "confidence": 0.65}
    except Exception:
        return {"language": "en", "raw": "fallback", "confidence": 0.5}