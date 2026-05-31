"""
NexaHub AI — TextToSpeech views.py
Human-like TTS using Microsoft edge-tts (free, no API key).

Supports:
  - English text        → en-US-GuyNeural / en-US-JennyNeural
  - Hindi (Devanagari)  → hi-IN-MadhurNeural / hi-IN-SwaraNeural
  - Hinglish (Roman)    → hi-IN voices with xml:lang=hi-IN

Auto-deletes generated files after 60 seconds.
"""

import os
import re
import uuid
import asyncio
import threading
import time

import edge_tts

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
# Voices
# ---------------------------------------------------------------------------
VOICES = {
    "en": {
        "male":   "en-US-GuyNeural",
        "female": "en-US-JennyNeural",
    },
    "hi": {
        "male":   "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
    },
}

# ---------------------------------------------------------------------------
# Emotion presets
# ---------------------------------------------------------------------------
EMOTIONS = {
    "friendly":   {"rate": "+5%",  "pitch": "+8Hz",  "volume": "+10%", "style_en": "friendly",        "style_hi": "friendly"},
    "confident":  {"rate": "-5%",  "pitch": "-5Hz",  "volume": "+15%", "style_en": "customerservice", "style_hi": "customerservice"},
    "calm":       {"rate": "-20%", "pitch": "-8Hz",  "volume": "-10%", "style_en": "gentle",          "style_hi": "gentle"},
    "excited":    {"rate": "+30%", "pitch": "+15Hz", "volume": "+20%", "style_en": "excited",         "style_hi": "excited"},
    "apologetic": {"rate": "-15%", "pitch": "-10Hz", "volume": "-15%", "style_en": "empathetic",      "style_hi": "empathetic"},
}

DEFAULT_EMOTION = "friendly"


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------
HINGLISH_MARKERS = {
    "namaste", "namaskar", "kaise", "kaisi", "kya", "kyun", "kyunki",
    "aap", "hum", "yeh", "woh", "yah", "vah",
    "hai", "hain", "hoga", "hogi", "tha", "thi",
    "nahi", "nahin", "mujhe", "tumhe", "unhe",
    "accha", "achha", "theek", "bahut", "bohot", "bilkul",
    "sundar", "pyaar", "pyar", "yaar", "bhai",
    "khana", "paani", "ghar", "kaam", "raat",
    "aaj", "abhi", "jaldi", "thoda",
    "mera", "tera", "apna", "unka", "inke", "uske",
    "karo", "karna", "bolo", "suno", "dekho",
    "dhanyavaad", "shukriya", "maafi",
    "lekin", "agar", "toh", "isliye",
    "haan", "arre", "oye",
}

def detect_language(text: str) -> str:
    # Devanagari
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
    # Hinglish
    words   = set(re.findall(r"[a-zA-Z]+", text.lower()))
    matches = words & HINGLISH_MARKERS
    ratio   = len(matches) / len(words) if words else 0
    if len(matches) >= 2:
        return "hinglish"
    if len(matches) >= 1 and ratio >= 0.3:
        return "hinglish"
    return "en"


# ---------------------------------------------------------------------------
# Auto-cleanup — delete files after delay
# ---------------------------------------------------------------------------
def _schedule_cleanup(*paths: str, delay: int = 1):
    """Delete given file paths after `delay` seconds in a background thread."""
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
    xml_lang  = "hi-IN" if lang in ("hi", "hinglish") else "en-US"
    style_key = "style_hi" if lang in ("hi", "hinglish") else "style_en"
    style     = emotion.get(style_key, "friendly")
    inner     = f'<lang xml:lang="hi-IN">{text}</lang>' if lang == "hinglish" else text

    return (
        f'<speak version="1.0" '
        f'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="http://www.w3.org/2001/mstts" '
        f'xml:lang="{xml_lang}">'
        f'<voice name="{voice}">'
        f'<mstts:express-as style="{style}">'
        f'<prosody rate="{emotion["rate"]}" '
        f'pitch="{emotion["pitch"]}" '
        f'volume="{emotion["volume"]}">'
        f'{inner}'
        f'</prosody>'
        f'</mstts:express-as>'
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


async def _generate_both(text: str, emotion_cfg: dict, lang: str) -> tuple[str, str]:
    voice_lang  = "hi" if lang in ("hi", "hinglish") else "en"
    male_path   = os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")
    female_path = os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")

    await asyncio.gather(
        _synthesize(text, VOICES[voice_lang]["male"],   emotion_cfg, lang, male_path),
        _synthesize(text, VOICES[voice_lang]["female"], emotion_cfg, lang, female_path),
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
    text  = request.POST.get("text", "").strip()
    style = request.POST.get("style", DEFAULT_EMOTION).strip().lower()

    if not text:
        return JsonResponse({"success": False, "error": "Text is required."})
    if len(text) > 2000:
        return JsonResponse({"success": False, "error": "Max 2000 characters."})
    if style not in EMOTIONS:
        style = DEFAULT_EMOTION

    lang        = detect_language(text)
    emotion_cfg = EMOTIONS[style]

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            male_path, female_path = loop.run_until_complete(
                _generate_both(text, emotion_cfg, lang)
            )
        finally:
            loop.close()

        for path in (male_path, female_path):
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                raise RuntimeError(f"Empty output: {os.path.basename(path)}")

        # Schedule auto-delete after 60 seconds
        _schedule_cleanup(male_path, female_path, delay=60)

        lang_label = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish"}.get(lang, "English")
        base_url   = request.build_absolute_uri(settings.MEDIA_URL + "tts/")

        return JsonResponse({
            "success":  True,
            "male":     base_url + os.path.basename(male_path),
            "female":   base_url + os.path.basename(female_path),
            "emotion":  style,
            "language": lang_label,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})