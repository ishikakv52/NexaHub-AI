from langdetect import detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0  # Consistent results

LANG_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'ar': 'Arabic',
    'zh-cn': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'pt': 'Portuguese',
    'it': 'Italian',
}

# Script-based character range checks (no internet needed)
SCRIPT_RANGES = {
    'hi': ('\u0900', '\u097F'),  # Devanagari
    'ar': ('\u0600', '\u06FF'),  # Arabic
    'zh-cn': ('\u4E00', '\u9FFF'),  # CJK Unified
    'ja': ('\u3040', '\u30FF'),  # Hiragana + Katakana
    'ko': ('\uAC00', '\uD7A3'),  # Hangul
    'ru': ('\u0400', '\u04FF'),  # Cyrillic
}

# How much of the text must be that script to auto-detect (30% threshold)
SCRIPT_THRESHOLD = 0.30


def _detect_by_script(text):
    """
    Unicode range se script detect karo.
    langdetect se zyada reliable for non-Latin scripts.
    """
    total = len(text)
    if total == 0:
        return None

    for lang_code, (start, end) in SCRIPT_RANGES.items():
        count = sum(1 for c in text if start <= c <= end)
        if count / total >= SCRIPT_THRESHOLD:
            return lang_code

    return None


def detect_language(text):
    """
    Fully offline language detection.
    Script check first (reliable), langdetect second (statistical).
    """
    if not text or len(text.strip()) < 20:  # 5 → 20: langdetect unreliable below this
        return {
            'language': 'unknown',
            'language_name': 'Unknown',
            'confidence': 0,
            'method': 'too_short'
        }

    cleaned = text.strip()

    # --- Step 1: Script-based detection (strongest signal) ---
    script_lang = _detect_by_script(cleaned)
    if script_lang:
        return {
            'language': script_lang,
            'language_name': LANG_NAMES.get(script_lang, script_lang.upper()),
            'confidence': 92,
            'method': 'script_range'
        }

    # --- Step 2: Statistical detection via langdetect ---
    try:
        candidates = detect_langs(cleaned)
        if not candidates:
            raise LangDetectException(0, 'No candidates')

        top = candidates[0]
        lang     = top.lang                        # '.lang' attribute - no string parsing
        conf     = round(top.prob * 100, 1)        # '.prob' attribute - safe access

        # Low confidence = unreliable, don't guess
        if conf < 40:
            return {
                'language': 'unknown',
                'language_name': 'Unknown',
                'confidence': round(conf, 1),
                'method': 'langdetect_low_confidence'
            }

        return {
            'language': lang,
            'language_name': LANG_NAMES.get(lang, lang.upper()),
            'confidence': conf,
            'method': 'langdetect'
        }

    except LangDetectException:
        return {
            'language': 'unknown',
            'language_name': 'Unknown',
            'confidence': 0,
            'method': 'langdetect_failed'
        }