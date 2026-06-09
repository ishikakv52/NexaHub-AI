# symptom_engine.py — Fixed: matches original + canonical, full Hinglish support

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(__file__))
PATH = os.path.join(BASE, "datasets", "multilingual_map.json")


def _load_mapping():
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

MAPPING = _load_mapping()

# ===========================
# DIRECT CANONICAL KEYWORD MAP
# If the text IS already a symptom key (from translation_engine output),
# map it directly. This handles cases like canonical="stomach_pain" or "back_pain"
# ===========================
CANONICAL_KEYS = set([
    "headache", "fever", "cold", "cough", "stomach_pain", "vomiting",
    "diarrhea", "sore_throat", "fatigue", "dizziness", "chest_pain",
    "breathing_difficulty", "high_bp", "low_bp", "high_sugar", "low_sugar",
    "high_heart_rate", "low_heart_rate", "low_spo2", "body_pain", "back_pain",
    "joint_pain", "skin_rash", "eye_problem", "anxiety", "insomnia",
    "constipation", "acidity", "diabetes_symptoms", "dengue_symptoms",
    "malaria_symptoms", "typhoid_symptoms", "jaundice", "kidney_problem",
    "migraine", "sinusitis", "toothache", "ear_problem",
])


def _clean_ascii(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_unicode(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _has_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text))


def _has_gujarati(text: str) -> bool:
    return bool(re.search(r"[\u0A80-\u0AFF]", text))


def _extract_from_text(text: str) -> dict:
    """Core matching logic for one text input."""
    is_indic = _has_devanagari(text) or _has_gujarati(text)

    text_ascii = _clean_ascii(text)
    text_unicode = _clean_unicode(text)
    tokens_ascii = set(text_ascii.split())

    found = set()
    confidence_map = {}

    # Direct canonical key match — if translated text IS already a symptom key
    for word in tokens_ascii:
        if word in CANONICAL_KEYS:
            found.add(word)
            confidence_map[word] = confidence_map.get(word, 0) + 5

    # Also check multi-word canonical keys (e.g. "stomach_pain" → "stomach pain" after clean)
    text_no_underscore = text_ascii.replace("_", " ")
    for key in CANONICAL_KEYS:
        key_spaced = key.replace("_", " ")
        if key_spaced in text_no_underscore:
            found.add(key)
            confidence_map[key] = confidence_map.get(key, 0) + 5

    # Full multilingual map matching
    for symptom, words in MAPPING.items():
        score = 0
        for w in words:
            w_lower = w.lower().strip()

            if _has_devanagari(w) or _has_gujarati(w):
                # Indic script: substring match on unicode text
                if w_lower in text_unicode:
                    score += 3
            else:
                # ASCII / Hinglish / multi-word phrase
                if w_lower in tokens_ascii:
                    score += 3
                elif w_lower in text_ascii:
                    score += 2

        if score > 0:
            found.add(symptom)
            confidence_map[symptom] = confidence_map.get(symptom, 0) + score

    return found, confidence_map


def extract_symptoms(text: str) -> dict:
    """
    Extract symptoms from user text.
    Handles: English, Hinglish, Hindi (Devanagari), Marathi, Gujarati.

    Returns:
    {
        "symptoms": [...],
        "confidence_map": {...}
    }
    """
    found, confidence_map = _extract_from_text(text)

    return {
        "symptoms": list(found),
        "confidence_map": confidence_map,
    }


def extract_symptoms_merged(original_text: str, canonical_text: str) -> dict:
    """
    Run extraction on BOTH original user text AND canonical translated text,
    then merge results. This ensures Hinglish/Hindi words caught from original
    AND canonical symptom keys caught from translated text.
    """
    found1, conf1 = _extract_from_text(original_text)
    found2, conf2 = _extract_from_text(canonical_text)

    merged_found = found1 | found2
    merged_conf = {**conf1}
    for k, v in conf2.items():
        merged_conf[k] = merged_conf.get(k, 0) + v

    return {
        "symptoms": list(merged_found),
        "confidence_map": merged_conf,
    }