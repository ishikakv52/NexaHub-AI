"""
NexaHub AI — TextToSpeech views.py
Human-like TTS using Microsoft edge-tts (free, no API key).
Auto-detects Hindi vs English text and uses correct neural voice.
Male/female voices with 5 emotion styles via SSML prosody.
"""

import os
import uuid
import asyncio
import unicodedata

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
# Voices — English + Hindi, Male + Female
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
# Emotion presets — SSML prosody per style
# ---------------------------------------------------------------------------
EMOTIONS = {
    "friendly": {
        "rate": "+5%", "pitch": "+8Hz", "volume": "+10%",
        "style_en": "friendly",   "style_hi": "friendly",
    },
    "confident": {
        "rate": "-5%", "pitch": "-5Hz", "volume": "+15%",
        "style_en": "customerservice", "style_hi": "customerservice",
    },
    "calm": {
        "rate": "-20%", "pitch": "-8Hz", "volume": "-10%",
        "style_en": "gentle",    "style_hi": "gentle",
    },
    "excited": {
        "rate": "+30%", "pitch": "+15Hz", "volume": "+20%",
        "style_en": "excited",   "style_hi": "excited",
    },
    "apologetic": {
        "rate": "-15%", "pitch": "-10Hz", "volume": "-15%",
        "style_en": "empathetic", "style_hi": "empathetic",
    },
}

DEFAULT_EMOTION = "friendly"


# ---------------------------------------------------------------------------
# Language detection — checks for Devanagari Unicode block
# ---------------------------------------------------------------------------
def detect_language(text: str) -> str:
    """Returns 'hi' if text contains Devanagari characters, else 'en'."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":   # Devanagari block
            return "hi"
    return "en"


# ---------------------------------------------------------------------------
# Core synthesis
# ---------------------------------------------------------------------------
async def _synthesize(text: str, voice: str, emotion: dict, lang: str, out_path: str):
    """
    Build SSML with prosody + speaking style, save to MP3.
    Falls back to plain prosody if SSML style fails.
    """
    style_key = f"style_{lang}"
    style     = emotion.get(style_key, "friendly")

    ssml = (
        "<speak version='1.0' "
        "xmlns='http://www.w3.org/2001/10/synthesis' "
        "xmlns:mstts='http://www.w3.org/2001/mstts' "
        f"xml:lang='{'hi-IN' if lang == 'hi' else 'en-US'}'>"
        f"<voice name='{voice}'>"
        f"<mstts:express-as style='{style}'>"
        f"<prosody rate='{emotion['rate']}' "
        f"pitch='{emotion['pitch']}' "
        f"volume='{emotion['volume']}'>"
        f"{text}"
        "</prosody>"
        "</mstts:express-as>"
        "</voice>"
        "</speak>"
    )

    try:
        comm = edge_tts.Communicate(ssml, voice, ssml=True)
        await comm.save(out_path)
    except Exception:
        # Fallback: plain prosody without style tag
        comm = edge_tts.Communicate(
            text, voice,
            rate=emotion["rate"],
            pitch=emotion["pitch"],
            volume=emotion["volume"],
        )
        await comm.save(out_path)


async def _generate_both(text: str, emotion_cfg: dict, lang: str) -> tuple[str, str]:
    """Generate male and female MP3s concurrently."""
    male_voice   = VOICES[lang]["male"]
    female_voice = VOICES[lang]["female"]

    male_path   = os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")
    female_path = os.path.join(MEDIA_FOLDER, f"{uuid.uuid4().hex}.mp3")

    await asyncio.gather(
        _synthesize(text, male_voice,   emotion_cfg, lang, male_path),
        _synthesize(text, female_voice, emotion_cfg, lang, female_path),
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
    Fields : text, style
    Returns: { success, male, female, emotion, language }
    """
    text  = request.POST.get("text", "").strip()
    style = request.POST.get("style", DEFAULT_EMOTION).strip().lower()

    if not text:
        return JsonResponse({"success": False, "error": "Text is required."})
    if len(text) > 2000:
        return JsonResponse({"success": False, "error": "Max 2000 characters."})
    if style not in EMOTIONS:
        style = DEFAULT_EMOTION

    lang        = detect_language(text)   # "hi" or "en"
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

        base_url = request.build_absolute_uri(settings.MEDIA_URL + "tts/")
        return JsonResponse({
            "success":  True,
            "male":     base_url + os.path.basename(male_path),
            "female":   base_url + os.path.basename(female_path),
            "emotion":  style,
            "language": "Hindi" if lang == "hi" else "English",
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})