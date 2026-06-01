"""
NexaHub AI — TextToSpeech views.py
Features:
  - 25 languages supported
  - Male/Female neural voices
  - 5 emotion styles
  - Hinglish (Roman Hindi) auto-detection
  - Voice translation to any supported language
  - Auto-cleanup after 60 seconds
"""

import os
import re
import uuid
import asyncio
import threading
import time

import edge_tts
from deep_translator import GoogleTranslator

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


# ---------------------------------------------------------------------------
# Media folder
# ---------------------------------------------------------------------------
MEDIA_FOLDER = os.path.join(settings.MEDIA_ROOT, "tts")
os.makedirs(MEDIA_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# Language → edge-tts voices mapping (25 languages)
# ---------------------------------------------------------------------------
LANG_VOICES = {
    "en": {"male": "en-US-GuyNeural",      "female": "en-US-JennyNeural"},
    "hi": {"male": "hi-IN-MadhurNeural",   "female": "hi-IN-SwaraNeural"},
    "fr": {"male": "fr-FR-HenriNeural",    "female": "fr-FR-DeniseNeural"},
    "de": {"male": "de-DE-ConradNeural",   "female": "de-DE-KatjaNeural"},
    "es": {"male": "es-ES-AlvaroNeural",   "female": "es-ES-ElviraNeural"},
    "ru": {"male": "ru-RU-DmitryNeural",   "female": "ru-RU-SvetlanaNeural"},
    "ar": {"male": "ar-SA-HamedNeural",    "female": "ar-SA-ZariyahNeural"},
    "bn": {"male": "bn-BD-PradeepNeural",  "female": "bn-BD-NabanitaNeural"},
    "ta": {"male": "ta-IN-ValluvarNeural", "female": "ta-IN-PallaviNeural"},
    "te": {"male": "te-IN-MohanNeural",    "female": "te-IN-ShrutiNeural"},
    "ml": {"male": "ml-IN-MidhunNeural",   "female": "ml-IN-SobhanaNeural"},
    "mr": {"male": "mr-IN-ManoharNeural",  "female": "mr-IN-AarohiNeural"},
    "gu": {"male": "gu-IN-NiranjanNeural", "female": "gu-IN-DhwaniNeural"},
    "ur": {"male": "ur-PK-AsadNeural",     "female": "ur-PK-UzmaNeural"},
    "zh": {"male": "zh-CN-YunxiNeural",    "female": "zh-CN-XiaoxiaoNeural"},
    "ja": {"male": "ja-JP-KeitaNeural",    "female": "ja-JP-NanamiNeural"},
    "pt": {"male": "pt-BR-AntonioNeural",  "female": "pt-BR-FranciscaNeural"},
    "pa": {"male": "pa-IN-OjasNeural",     "female": "pa-IN-VaaniNeural"},
    "ms": {"male": "ms-MY-OsmanNeural",    "female": "ms-MY-YasminNeural"},
    "vi": {"male": "vi-VN-NamMinhNeural",  "female": "vi-VN-HoaiMyNeural"},
    "ko": {"male": "ko-KR-InJoonNeural",   "female": "ko-KR-SunHiNeural"},
    "kn": {"male": "kn-IN-GaganNeural",    "female": "kn-IN-SapnaNeural"},
    "ne": {"male": "ne-NP-SagarNeural",    "female": "ne-NP-HemkalaNeural"},
    "or": {"male": "or-IN-SukantNeural",   "female": "or-IN-SubhasiniNeural"},
    "sd": {"male": "sd-PK-FirasNeural",    "female": "sd-PK-FirasNeural"},
}

# Google Translate uses zh-CN for Chinese
GOOGLE_LANG_MAP = {"zh": "zh-CN"}


# ---------------------------------------------------------------------------
# Emotion presets
# ---------------------------------------------------------------------------
EMOTIONS = {
    "friendly":   {"rate": "+5%",  "pitch": "+8Hz",  "volume": "+10%"},
    "confident":  {"rate": "-5%",  "pitch": "-5Hz",  "volume": "+15%"},
    "calm":       {"rate": "-20%", "pitch": "-8Hz",  "volume": "-10%"},
    "excited":    {"rate": "+30%", "pitch": "+15Hz", "volume": "+20%"},
    "apologetic": {"rate": "-15%", "pitch": "-10Hz", "volume": "-15%"},
}

DEFAULT_EMOTION = "friendly"


# ---------------------------------------------------------------------------
# Hinglish detection
# ---------------------------------------------------------------------------
HINGLISH_MARKERS = {
    "namaste", "namaskar", "pranam", "adaab",
    "aap", "tum", "main", "hum", "yeh", "woh", "yah", "vah", "vo", "ye", "wo",
    "mujhe", "tumhe", "unhe", "inhe", "usse", "isse", "humein",
    "meri", "teri", "uski", "unki", "hamari", "tumhari",
    "mera", "tera", "uska", "unka", "hamara", "tumhara", "apna", "apni",
    "hai", "hain", "hoga", "hogi", "tha", "thi", "hoon", "ho",
    "karo", "karna", "kar", "kiya", "karte", "karti",
    "bolo", "bola", "boli", "bol", "suno", "suna", "sun",
    "dekho", "dekha", "dekh", "jao", "gaya", "gayi", "gaye",
    "aao", "aaya", "aayi", "aaye", "liya", "diya",
    "hua", "hui", "hue", "hona", "raha", "rahi", "rahe", "rehna",
    "chahiye", "chahta", "chahti", "sakta", "sakti", "sakte",
    "milna", "mila", "mili", "samajh", "samjha",
    "lagta", "lagti", "laga", "pata", "malum",
    "chal", "chalo", "chalte", "ruko", "ruk", "bata", "batao",
    "kya", "kyun", "kyunki", "kaise", "kaisi", "kaun", "kahan",
    "kab", "kitna", "kitni", "kitne", "kidhar",
    "accha", "achha", "theek", "thik", "bahut", "bohot", "bilkul",
    "zyada", "jyada", "thoda", "thodi", "kam", "bas", "sirf",
    "haan", "nahi", "nahin", "naa",
    "are", "arre", "oye", "yaar", "bhai",
    "wah", "waah", "shabash", "shayad",
    "zaroor", "zarur", "pakka", "sach",
    "matlab", "seedha", "seedhi",
    "vgera", "wagera", "waghera", "aadi",
    "kaafi", "itna", "utna",
    "sundar", "acha", "bura", "naya", "purana", "bada", "chota",
    "saaf", "ganda", "sahi", "galat", "mushkil", "aasaan", "asaan",
    "mahan", "mahaan", "bekar", "bakwas",
    "ghar", "kaam", "naam", "din", "raat", "subah", "shaam",
    "khana", "paani", "chai", "roti", "daal", "chawal",
    "dost", "behan", "maa", "baap", "papa", "mama",
    "beta", "beti", "bhaiya", "didi", "chacha",
    "shahar", "gaon", "raasta", "dukan", "bazaar",
    "paisa", "rupya", "naukri", "padhai",
    "samay", "waqt", "jagah",
    "aaj", "kal", "parso", "abhi", "jaldi", "dhire",
    "pehle", "baad", "phir", "dobara",
    "aur", "lekin", "magar", "toh", "to", "isliye",
    "jabki", "jab", "tab", "agar", "agr", "warna", "fir", "bhi", "hi",
    "ek", "do", "teen", "char", "paanch",
    "sab", "sabhi", "koi", "yani", "yaane",
    "ji", "sahab", "shukriya", "dhanyavaad", "maafi",
}

def detect_language(text: str) -> str:
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    words   = set(re.findall(r"[a-zA-Z]+", text.lower()))
    matches = words & HINGLISH_MARKERS
    ratio   = len(matches) / len(words) if words else 0
    if len(matches) >= 2:           return "hinglish"
    if len(matches) >= 1 and ratio >= 0.3: return "hinglish"
    return "en"


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language using Google Translate (free)."""
    google_lang = GOOGLE_LANG_MAP.get(target_lang, target_lang)
    translated = GoogleTranslator(source="auto", target=google_lang).translate(text)
    return translated or text


# ---------------------------------------------------------------------------
# Auto-cleanup
# ---------------------------------------------------------------------------
def _schedule_cleanup(*paths: str, delay: int = 60):
    def _delete():
        time.sleep(delay)
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
    threading.Thread(target=_delete, daemon=True).start()


# ---------------------------------------------------------------------------
# SSML builder
# ---------------------------------------------------------------------------
def build_ssml(text: str, voice: str, emotion: dict, lang: str) -> str:
    # Determine xml:lang from voice name (e.g. hi-IN-MadhurNeural → hi-IN)
    parts    = voice.split("-")
    xml_lang = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "en-US"
    inner    = f'<lang xml:lang="hi-IN">{text}</lang>' if lang == "hinglish" else text

    return (
        f'<speak version="1.0" '
        f'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="http://www.w3.org/2001/mstts" '
        f'xml:lang="{xml_lang}">'
        f'<voice name="{voice}">'
        f'<prosody rate="{emotion["rate"]}" '
        f'pitch="{emotion["pitch"]}" '
        f'volume="{emotion["volume"]}">'
        f'{inner}'
        f'</prosody>'
        f'</voice>'
        f'</speak>'
    )


# ---------------------------------------------------------------------------
# Async synthesis
# ---------------------------------------------------------------------------
async def _synthesize(text: str, voice: str, emotion: dict, lang: str, out_path: str):
    ssml = build_ssml(text, voice, emotion, lang)
    try:
        comm = edge_tts.Communicate(ssml, voice, ssml=True)
        await comm.save(out_path)
    except Exception:
        comm = edge_tts.Communicate(
            text, voice,
            rate=emotion["rate"],
            pitch=emotion["pitch"],
            volume=emotion["volume"],
        )
        await comm.save(out_path)


async def _generate_both(text: str, emotion_cfg: dict, voice_lang: str, detect_lang: str) -> tuple[str, str]:
    voices     = LANG_VOICES.get(voice_lang, LANG_VOICES["en"])
    male_path  = os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")
    female_path= os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")

    await asyncio.gather(
        _synthesize(text, voices["male"],   emotion_cfg, detect_lang, male_path),
        _synthesize(text, voices["female"], emotion_cfg, detect_lang, female_path),
    )
    return male_path, female_path


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
def index(request):
    return render(request, "TextToSpeech/index.html")


@csrf_exempt
@require_POST
def generate_speech(request):
    """
    POST /texttospeech/generate/
    Fields: text, style
    Returns: { success, male, female, emotion, language, detected_lang }
    """
    text  = request.POST.get("text", "").strip()
    style = request.POST.get("style", DEFAULT_EMOTION).strip().lower()

    if not text:
        return JsonResponse({"success": False, "error": "Text is required."})
    if len(text) > 2000:
        return JsonResponse({"success": False, "error": "Max 2000 characters."})
    if style not in EMOTIONS:
        style = DEFAULT_EMOTION

    detected    = detect_language(text)
    voice_lang  = "hi" if detected in ("hi", "hinglish") else detected if detected in LANG_VOICES else "en"
    emotion_cfg = EMOTIONS[style]

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            male_path, female_path = loop.run_until_complete(
                _generate_both(text, emotion_cfg, voice_lang, detected)
            )
        finally:
            loop.close()

        for path in (male_path, female_path):
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                raise RuntimeError(f"Empty output: {os.path.basename(path)}")

        _schedule_cleanup(male_path, female_path, delay=60)

        lang_label = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish"}.get(detected, "English")
        base_url   = request.build_absolute_uri(settings.MEDIA_URL + "tts/")

        return JsonResponse({
            "success":       True,
            "male":          base_url + os.path.basename(male_path),
            "female":        base_url + os.path.basename(female_path),
            "emotion":       style,
            "language":      lang_label,
            "detected_lang": voice_lang,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
@require_POST
def translate_speech(request):
    """
    POST /texttospeech/translate/
    Fields: text, target_lang, style
    Translates text then generates voice in target language.
    Returns: { success, male, female, translated_text, target_lang }
    """
    text        = request.POST.get("text", "").strip()
    target_lang = request.POST.get("target_lang", "en").strip().lower()
    style       = request.POST.get("style", DEFAULT_EMOTION).strip().lower()

    if not text:
        return JsonResponse({"success": False, "error": "Text is required."})
    if target_lang not in LANG_VOICES:
        return JsonResponse({"success": False, "error": f"Unsupported language: {target_lang}"})
    if style not in EMOTIONS:
        style = DEFAULT_EMOTION

    try:
        # Step 1: Translate
        translated  = translate_text(text, target_lang)
        emotion_cfg = EMOTIONS[style]

        # Step 2: Generate voice in target language
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            male_path, female_path = loop.run_until_complete(
                _generate_both(translated, emotion_cfg, target_lang, target_lang)
            )
        finally:
            loop.close()

        for path in (male_path, female_path):
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                raise RuntimeError(f"Empty output: {os.path.basename(path)}")

        _schedule_cleanup(male_path, female_path, delay=60)

        base_url = request.build_absolute_uri(settings.MEDIA_URL + "tts/")

        return JsonResponse({
            "success":         True,
            "male":            base_url + os.path.basename(male_path),
            "female":          base_url + os.path.basename(female_path),
            "translated_text": translated,
            "target_lang":     target_lang,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})