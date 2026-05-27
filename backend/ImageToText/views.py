from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    M2M100ForConditionalGeneration,
    M2M100Tokenizer,
)
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import json
import unicodedata
import re

from .language_mapping import lang_map, get_supported_lang_code, normalize_lang_code, detect_language

# ---------------------------------------------------------------------------
# Model cache — loaded once, reused across all requests
# ---------------------------------------------------------------------------
MODEL_CACHE = {}


def get_trocr_model():
    key = "trocr"
    if key not in MODEL_CACHE:
        processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten")
        model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-handwritten")
        MODEL_CACHE[key] = (processor, model)
    return MODEL_CACHE[key]


def get_m2m100_model():
    key = "m2m100"
    if key not in MODEL_CACHE:
        # 1.2B gives much better quality than 418M across all language pairs
        tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_1.2B")
        model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_1.2B")
        MODEL_CACHE[key] = (tokenizer, model)
    return MODEL_CACHE[key]


# ---------------------------------------------------------------------------
# Tesseract language map — comprehensive, covering every Tesseract data pack
# ---------------------------------------------------------------------------
TESS_LANG_MAP = {
    "af":  "afr",   # Afrikaans
    "sq":  "sqi",   # Albanian
    "am":  "amh",   # Amharic
    "ar":  "ara",   # Arabic
    "hy":  "hye",   # Armenian
    "az":  "aze",   # Azerbaijani
    "eu":  "eus",   # Basque
    "be":  "bel",   # Belarusian
    "bn":  "ben",   # Bengali
    "bs":  "bos",   # Bosnian
    "bg":  "bul",   # Bulgarian
    "ca":  "cat",   # Catalan
    "ceb": "ceb",   # Cebuano
    "zh":  "chi_sim+chi_tra",  # Chinese (both simplified + traditional probe)
    "zh-cn": "chi_sim",
    "zh-tw": "chi_tra",
    "hr":  "hrv",   # Croatian
    "cs":  "ces",   # Czech
    "da":  "dan",   # Danish
    "nl":  "nld",   # Dutch
    "en":  "eng",   # English
    "eo":  "epo",   # Esperanto
    "et":  "est",   # Estonian
    "fi":  "fin",   # Finnish
    "fr":  "fra",   # French
    "gl":  "glg",   # Galician
    "ka":  "kat",   # Georgian
    "de":  "deu",   # German
    "el":  "ell",   # Greek
    "gu":  "guj",   # Gujarati
    "ht":  "hat",   # Haitian Creole
    "he":  "heb",   # Hebrew
    "hi":  "hin",   # Hindi
    "hu":  "hun",   # Hungarian
    "is":  "isl",   # Icelandic
    "id":  "ind",   # Indonesian
    "ga":  "gle",   # Irish
    "it":  "ita",   # Italian
    "ja":  "jpn",   # Japanese
    "kn":  "kan",   # Kannada
    "kk":  "kaz",   # Kazakh
    "km":  "khm",   # Khmer
    "ko":  "kor",   # Korean
    "ku":  "kur",   # Kurdish
    "ky":  "kir",   # Kyrgyz
    "lo":  "lao",   # Lao
    "la":  "lat",   # Latin
    "lv":  "lav",   # Latvian
    "lt":  "lit",   # Lithuanian
    "lb":  "ltz",   # Luxembourgish
    "mk":  "mkd",   # Macedonian
    "ms":  "msa",   # Malay
    "ml":  "mal",   # Malayalam
    "mt":  "mlt",   # Maltese
    "mr":  "mar",   # Marathi
    "mn":  "mon",   # Mongolian
    "my":  "mya",   # Myanmar/Burmese
    "ne":  "nep",   # Nepali
    "nb":  "nor",   # Norwegian
    "or":  "ori",   # Odia (Oriya)
    "ps":  "pus",   # Pashto
    "fa":  "fas",   # Persian/Farsi
    "pl":  "pol",   # Polish
    "pt":  "por",   # Portuguese
    "pa":  "pan",   # Punjabi (Gurmukhi)
    "ro":  "ron",   # Romanian
    "ru":  "rus",   # Russian
    "sa":  "san",   # Sanskrit
    "sr":  "srp",   # Serbian
    "sd":  "snd",   # Sindhi
    "si":  "sin",   # Sinhala
    "sk":  "slk",   # Slovak
    "sl":  "slv",   # Slovenian
    "so":  "som",   # Somali
    "es":  "spa",   # Spanish
    "sw":  "swa",   # Swahili
    "sv":  "swe",   # Swedish
    "tl":  "tgl",   # Tagalog/Filipino
    "tg":  "tgk",   # Tajik
    "ta":  "tam",   # Tamil
    "tt":  "tat",   # Tatar
    "te":  "tel",   # Telugu
    "th":  "tha",   # Thai
    "ti":  "tir",   # Tigrinya
    "tr":  "tur",   # Turkish
    "tk":  "tuk",   # Turkmen
    "uk":  "ukr",   # Ukrainian
    "ur":  "urd",   # Urdu
    "ug":  "uig",   # Uyghur
    "uz":  "uzb",   # Uzbek
    "vi":  "vie",   # Vietnamese
    "cy":  "cym",   # Welsh
    "yi":  "yid",   # Yiddish
    "yo":  "yor",   # Yoruba
    "zu":  "zul",   # Zulu
}

# Probe string covers Latin, Cyrillic, Arabic, Devanagari, CJK, and many
# other scripts in a single Tesseract pass so script detection has real data.
PROBE_LANGS = (
    "eng+hin+ara+ben+tam+tel+mal+mar+guj+ori+urd+pan+"
    "chi_sim+chi_tra+jpn+kor+rus+ukr+bul+srp+"
    "tha+mya+khm+lao+sin+kat+hye+amh+tir+"
    "pol+ces+slk+hrv+ron+hun+fin+swe+dan+nor+"
    "tur+fas+pus+kaz+uzb+vie+ind+msa+tgl+"
    "nep+kir+tgk+mon+kan+snd+aze+bel+lat"
)


# ---------------------------------------------------------------------------
# Unicode-script based language detection — works even when langdetect fails
# ---------------------------------------------------------------------------

# Map Unicode script name → our ISO-639-1 code
# When multiple languages share a script we fall back to langdetect to pick one.
SCRIPT_LANG_MAP = {
    "DEVANAGARI":   None,    # hi / mr / ne / sa — disambiguated below
    "ARABIC":       None,    # ar / ur / fa / ps / sd / ug — disambiguated below
    "BENGALI":      "bn",
    "GUJARATI":     "gu",
    "GURMUKHI":     "pa",
    "KANNADA":      "kn",
    "MALAYALAM":    "ml",
    "MYANMAR":      "my",
    "ORIYA":        "or",
    "SINHALA":      "si",
    "TAMIL":        "ta",
    "TELUGU":       "te",
    "THAI":         "th",
    "TIBETAN":      "bo",
    "GEORGIAN":     "ka",
    "ARMENIAN":     "hy",
    "ETHIOPIC":     "am",    # Amharic is dominant
    "KHMER":        "km",
    "LAO":          "lo",
    "MONGOLIAN":    "mn",
    "YI":           "ii",
    "TIBETAN":      "bo",
    "HANGUL":       "ko",
    "HIRAGANA":     "ja",
    "KATAKANA":     "ja",
    "CJK":          "zh",    # refined to zh-cn / zh-tw later if needed
    "HEBREW":       "he",
    "CYRILLIC":     None,    # ru/uk/bg/sr/mk/be — disambiguated below
    "GREEK":        "el",
    "LATIN":        None,    # too many languages — must use langdetect
}

# Devanagari sub-disambiguation heuristics (character frequency patterns)
DEVANAGARI_HINTS = {
    "ne": ["ले", "को", "छ", "मा", "हो", "गर्"],
    "mr": ["आहे", "आणि", "नाही", "हे", "ते", "मी"],
    "hi": ["है", "और", "में", "के", "को", "एक"],
}

# Arabic-script sub-disambiguation
ARABIC_HINTS = {
    "ur": ["ہے", "کے", "میں", "اور", "نے", "کو", "ہیں"],
    "fa": ["است", "این", "که", "را", "با", "از", "برای"],
    "ps": ["چې", "دی", "چه", "او", "له", "د"],
    "ar": ["في", "من", "على", "إلى", "هذا", "التي"],
}

# Cyrillic sub-disambiguation
CYRILLIC_HINTS = {
    "uk": ["що", "та", "він", "це", "але", "для"],
    "bg": ["се", "за", "не", "от", "на", "са"],
    "sr": ["је", "да", "се", "за", "или", "ово"],
    "ru": ["что", "это", "как", "все", "для", "или"],
}


def _dominant_script(text: str) -> str | None:
    """Return the Unicode script name that dominates in `text`."""
    counts: dict[str, int] = {}
    for ch in text:
        if ch.isspace() or ch in ".,!?;:\"'()[]{}0123456789":
            continue
        try:
            name = unicodedata.name(ch, "")
        except (ValueError, TypeError):
            continue
        # Extract script from Unicode character name, e.g. "ARABIC LETTER BA" → "ARABIC"
        parts = name.split()
        if parts:
            script = parts[0]
            counts[script] = counts.get(script, 0) + 1
    return max(counts, key=counts.get) if counts else None


def _hint_match(text: str, hints: dict[str, list[str]]) -> str | None:
    """Pick the language whose hint words appear most in `text`."""
    best_lang, best_count = None, 0
    for lang, words in hints.items():
        c = sum(1 for w in words if w in text)
        if c > best_count:
            best_lang, best_count = lang, c
    return best_lang if best_count > 0 else None


def robust_detect_language(text: str, hint: str | None = None) -> str:
    """
    Multi-stage language detection:
      1. Use OCR hint if provided and trustworthy
      2. Unicode script dominance
      3. Hint-word disambiguation for shared-script families
      4. Fall back to langdetect
      5. Final fallback: "en"
    """
    if not text or not text.strip():
        return hint or "en"

    # Stage 1 — trust the OCR hint for unambiguous scripts
    if hint and hint in TESS_LANG_MAP:
        return hint

    script = _dominant_script(text)

    # Stage 2 — map unique scripts directly
    if script and script in SCRIPT_LANG_MAP:
        mapped = SCRIPT_LANG_MAP[script]
        if mapped:
            return mapped

    # Stage 3 — disambiguate shared scripts
    if script == "DEVANAGARI":
        lang = _hint_match(text, DEVANAGARI_HINTS)
        if lang:
            return lang
        # Default to Hindi for Devanagari when no hints match
        return "hi"

    if script == "ARABIC":
        lang = _hint_match(text, ARABIC_HINTS)
        if lang:
            return lang
        return "ar"

    if script == "CYRILLIC":
        lang = _hint_match(text, CYRILLIC_HINTS)
        if lang:
            return lang
        return "ru"

    # Stage 4 — langdetect for Latin and unknown scripts
    try:
        detected = detect_language(text, hint=hint)
        if detected and detected != "unknown":
            return detected
    except Exception:
        pass

    # Stage 5 — final fallback
    return "en"


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def preprocess_image(image: Image.Image, sharpen: bool = False) -> Image.Image:
    """Grayscale → resize → contrast → optional sharpen → back to RGB."""
    img = image.convert("L")
    # Upscale small images — Tesseract works best at ~300 DPI equivalent
    w, h = img.size
    if max(w, h) < 1000:
        scale = 1000 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    if sharpen:
        img = img.filter(ImageFilter.SHARPEN)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# OCR view
# ---------------------------------------------------------------------------

@csrf_exempt
def ocr_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Send a POST request with an image."})

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return HttpResponse("No file uploaded.", status=400)

    image = Image.open(uploaded_file).convert("RGB")
    handwritten = request.POST.get("handwritten") == "true"
    force_lang = request.POST.get("lang", "").strip()  # optional manual lang hint
    ocr_lang_hint = None

    if handwritten:
        # ----------------------------------------------------------------
        # Handwritten path — TrOCR (English-optimised deep learning model)
        # ----------------------------------------------------------------
        proc, model = get_trocr_model()
        img_pre = preprocess_image(image)
        pixel_values = proc(images=img_pre, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = proc.batch_decode(generated_ids, skip_special_tokens=True)[0]
        debug_msg = "Handwritten OCR via TrOCR (microsoft/trocr-large-handwritten)."
        # TrOCR is English-only — no reliable lang hint
        ocr_lang_hint = "en"

    elif force_lang and force_lang in TESS_LANG_MAP:
        # ----------------------------------------------------------------
        # Caller explicitly told us the language — skip probe, run direct
        # ----------------------------------------------------------------
        tess_lang = TESS_LANG_MAP[force_lang]
        img_pre = preprocess_image(image, sharpen=True)
        text = pytesseract.image_to_string(img_pre, lang=tess_lang)
        debug_msg = f"Forced-language OCR: Tesseract lang='{tess_lang}' (user supplied '{force_lang}')."
        ocr_lang_hint = force_lang

    else:
        # ----------------------------------------------------------------
        # Auto-detect path
        # Step 1: broad multi-script probe to capture real characters
        # Step 2: Unicode-script detection on probe output
        # Step 3: re-run OCR with the best matching Tesseract language pack
        # ----------------------------------------------------------------
        img_pre = preprocess_image(image, sharpen=True)

        # --- Probe pass ---
        probe_text = pytesseract.image_to_string(img_pre, lang=PROBE_LANGS)
        probe_lang = robust_detect_language(probe_text)

        tess_lang = TESS_LANG_MAP.get(probe_lang, "eng")

        if tess_lang != "eng":
            # Re-run with specific language pack for better glyph accuracy
            text = pytesseract.image_to_string(img_pre, lang=tess_lang)
            # Verify that the re-run text still looks like the detected language
            # (sometimes Tesseract returns garbage with a wrong pack — fallback
            # to probe_text in that case)
            if len(text.strip()) < len(probe_text.strip()) * 0.5:
                text = probe_text
                debug_msg = (
                    f"Script detected as '{probe_lang}' (Tesseract pack: '{tess_lang}'), "
                    "but re-run produced less text — kept probe result."
                )
            else:
                debug_msg = (
                    f"Script auto-detected as '{probe_lang}'; "
                    f"re-ran OCR with Tesseract lang='{tess_lang}'."
                )
            ocr_lang_hint = probe_lang
        else:
            # English / Latin — probe text is already good quality
            text = probe_text
            debug_msg = "Auto-detected Latin/English script; used multi-script probe result."

    # ------------------------------------------------------------------
    # Final language detection on the extracted text
    # ------------------------------------------------------------------
    detected_lang = "en"
    if text.strip():
        detected_lang = robust_detect_language(text, hint=ocr_lang_hint)

    return JsonResponse({
        "uploaded_file": uploaded_file.name,
        "extracted_text": text,
        "detected_lang": detected_lang,
        "detected_lang_name": lang_map.get(detected_lang, "Unknown"),
        "debug": debug_msg,
    })


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    tokenizer, model = get_m2m100_model()
    source_lang = normalize_lang_code(source_lang)
    target_lang = normalize_lang_code(target_lang)

    tokenizer.src_lang = source_lang
    # Chunk long texts to stay within the model's 1024-token context window
    chunks = _chunk_text(text, max_chars=800)
    translated_chunks = []
    for chunk in chunks:
        encoded = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=1024)
        forced_bos = tokenizer.get_lang_id(target_lang)
        tokens = model.generate(**encoded, forced_bos_token_id=forced_bos)
        translated_chunks.append(
            tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]
        )
    return " ".join(translated_chunks)


def _chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """Split text on sentence boundaries to keep chunks under max_chars."""
    sentences = re.split(r"(?<=[.!?।۔。！？])\s+", text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = s
        else:
            current = (current + " " + s).strip()
    if current:
        chunks.append(current)
    return chunks or [text]


# ---------------------------------------------------------------------------
# Translation view
# ---------------------------------------------------------------------------

@csrf_exempt
def translate_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is supported"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    text        = data.get("text", "").strip()
    target_lang = get_supported_lang_code(data.get("target_lang", ""))
    source_lang = get_supported_lang_code(data.get("source_lang", ""))

    if not text:
        return JsonResponse({"error": "No text provided"}, status=400)

    if target_lang is None:
        return JsonResponse({"error": "Target language not supported"}, status=400)

    if target_lang == "original":
        return JsonResponse({"translated_text": text})

    if source_lang is None:
        source_lang = robust_detect_language(text)

    if source_lang == target_lang:
        return JsonResponse({"translated_text": text})

    try:
        translated = translate_text(text, source_lang, target_lang)
        return JsonResponse({
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
        })
    except Exception as exc:
        return JsonResponse({"error": f"Translation failed: {exc}"}, status=500)