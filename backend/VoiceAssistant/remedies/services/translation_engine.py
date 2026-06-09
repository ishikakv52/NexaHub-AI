# translation_engine.py — Fixed: handles Devanagari + Gujarati Unicode substring matching

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


def _clean_ascii(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_unicode(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _has_indic(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F\u0A80-\u0AFF]", text))


def translate_to_english(text: str) -> dict:
    """
    Converts multilingual medical input → English canonical symptom keys.
    Handles English, Hinglish, Hindi (Devanagari), Marathi, Gujarati.

    Returns:
    {
        "translated_text": "headache fever",   ← space-separated canonical keys
        "matched_terms":   ["headache", "fever"],
        "confidence_map":  {"headache": 3, "fever": 3}
    }
    """
    text_ascii   = _clean_ascii(text)
    text_unicode = _clean_unicode(text)
    words_ascii  = set(text_ascii.split())

    matched_terms = set()
    confidence_map = {}

    for canonical, variants in MAPPING.items():
        score = 0
        for v in variants:
            v_lower = v.lower().strip()

            if _has_indic(v):
                # Devanagari / Gujarati: use substring on original unicode text
                if v_lower in text_unicode:
                    score += 3
            else:
                # ASCII / Hinglish / English
                if v_lower in words_ascii:
                    score += 3
                elif v_lower in text_ascii:
                    score += 1

        if score > 0:
            matched_terms.add(canonical)
            confidence_map[canonical] = score

    return {
        "translated_text": " ".join(list(matched_terms)),
        "matched_terms": list(matched_terms),
        "confidence_map": confidence_map,
    }