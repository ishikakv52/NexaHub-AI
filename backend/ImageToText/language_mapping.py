import re
from langdetect import DetectorFactory, detect, LangDetectException

DetectorFactory.seed = 0

# Language values used by the frontend dropdown.
# Only codes supported by the local translation model are included here.
lang_map = {
    "en": "English",
    "hi": "Hindi",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "ar": "Arabic",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ur": "Urdu",
    "zh": "Chinese",
    "ja": "Japanese",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ms": "Malay",
    "vi": "Vietnamese",
    "ko": "Korean",
    "kn": "Kannada",
    "ne": "Nepali",
    "or": "Odia",
    "sd": "Sindhi",
}

unsupported_languages = {"as", "doi", "gom", "mai", "mni-mtei", "sa"}

alias_map = {
    "zh-cn": "zh",
    "zh_tw": "zh",
    "zh-tw": "zh",
    "zh_cn": "zh",
    "original": "original",
    "auto": "auto",
}

# ---------------------------------------------------------------------------
# Unicode script ranges → candidate language codes
# Order matters: more specific ranges come first.
# ---------------------------------------------------------------------------
SCRIPT_RANGES = [
    # Arabic / Urdu / Sindhi  (Arabic script is shared; urdu/sindhi detected by context below)
    (r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]", "ar"),

    # Devanagari  (Hindi, Marathi, Nepali — disambiguated below)
    (r"[\u0900-\u097F]", "hi"),

    # Bengali
    (r"[\u0980-\u09FF]", "bn"),

    # Gurmukhi  (Punjabi)
    (r"[\u0A00-\u0A7F]", "pa"),

    # Gujarati
    (r"[\u0A80-\u0AFF]", "gu"),

    # Odia
    (r"[\u0B00-\u0B7F]", "or"),

    # Tamil
    (r"[\u0B80-\u0BFF]", "ta"),

    # Telugu
    (r"[\u0C00-\u0C7F]", "te"),

    # Kannada
    (r"[\u0C80-\u0CFF]", "kn"),

    # Malayalam
    (r"[\u0D00-\u0D7F]", "ml"),

    # Sinhala (not in lang_map — skip gracefully)
    # (r"[\u0D80-\u0DFF]", "si"),

    # CJK Unified Ideographs — Chinese / Japanese share range; disambiguate below
    (r"[\u4E00-\u9FFF\u3400-\u4DBF]", "zh"),

    # Hiragana / Katakana → definitely Japanese
    (r"[\u3040-\u309F\u30A0-\u30FF]", "ja"),

    # Hangul → Korean
    (r"[\uAC00-\uD7AF\u1100-\u11FF]", "ko"),

    # Cyrillic → Russian (most common in our lang_map)
    (r"[\u0400-\u04FF]", "ru"),
]

# Vocabulary hints to disambiguate Devanagari (hi / mr / ne)
_MARATHI_HINTS = re.compile(
    r"\b(आहे|नाही|आणि|करण्यात|मराठी|महाराष्ट्र|होते|असे|त्यांनी)\b"
)
_NEPALI_HINTS = re.compile(
    r"\b(छ|छन्|गर्न|नेपाल|नेपाली|भयो|गरेको|हुन्छ|थियो)\b"
)

# Arabic-script language hints
_URDU_HINTS = re.compile(r"[\u06BE\u06C1\u06C3\u06D2\u0679\u0688\u0691\u0698\u06AF]")
_SINDHI_HINTS = re.compile(r"[\u062C\u0DA0-\u0DA9\u0DB3\u0DB6\u0DB8\u0DC4]")


def _dominant_script(text: str):
    """
    Return the language code of the dominant Unicode script found in text,
    or None if no script block has significant presence.
    """
    if not text:
        return None

    counts: dict[str, int] = {}
    for pattern, lang in SCRIPT_RANGES:
        matches = re.findall(pattern, text)
        if matches:
            # Hiragana/Katakana always wins over CJK for Japanese
            key = lang
            counts[key] = counts.get(key, 0) + len(matches)

    if not counts:
        return None

    dominant = max(counts, key=lambda k: counts[k])
    total_chars = max(len(text.replace(" ", "")), 1)
    dominant_ratio = counts[dominant] / total_chars

    # Require at least 15 % of non-space characters to be from that script
    if dominant_ratio < 0.15:
        return None

    # --- Disambiguation ---

    # Japanese: if Hiragana/Katakana exists alongside CJK, it's Japanese
    if dominant == "zh" and counts.get("ja", 0) > 0:
        return "ja"

    # Devanagari: Hindi vs Marathi vs Nepali
    if dominant == "hi":
        if _NEPALI_HINTS.search(text):
            return "ne"
        if _MARATHI_HINTS.search(text):
            return "mr"
        return "hi"

    # Arabic script: Urdu vs Sindhi vs Arabic
    if dominant == "ar":
        if _URDU_HINTS.search(text):
            return "ur"
        if _SINDHI_HINTS.search(text):
            return "sd"
        return "ar"

    return dominant


def detect_language(text: str, hint: str = None) -> str:
    """
    Detect language of *text* and return a code present in lang_map.

    Steps:
      1. If a reliable OCR hint is given (e.g. tesseract ran with 'hin'),
         trust it directly.
      2. Try Unicode-script detection — highly accurate for non-Latin scripts.
      3. Fall back to langdetect for Latin-script text.
      4. Default to 'en' if everything fails.

    Parameters
    ----------
    text : str
        The extracted OCR text.
    hint : str, optional
        A language code hint from the OCR engine (e.g. 'hi' when Tesseract
        was called with lang='hin').  Only used when the hint is in lang_map.
    """
    if not text or not text.strip():
        return "en"

    # Step 1 — trust a reliable OCR hint
    if hint and hint in lang_map:
        return hint

    # Step 2 — Unicode script detection
    script_lang = _dominant_script(text)
    if script_lang and script_lang in lang_map:
        return script_lang

    # Step 3 — langdetect fallback (best for Latin-script languages)
    try:
        detected = normalize_lang_code(detect(text))
        if detected and detected in lang_map:
            return detected
    except (LangDetectException, Exception):
        pass

    # Step 4 — safe default
    return "en"


def normalize_lang_code(lang_code):
    if not lang_code:
        return None
    code = lang_code.strip().lower()
    return alias_map.get(code, code)


def is_lang_supported(lang_code):
    code = normalize_lang_code(lang_code)
    return code in lang_map or code == "original"


def get_supported_lang_code(lang_code):
    code = normalize_lang_code(lang_code)
    return code if code in lang_map else None