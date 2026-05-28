import os
import tempfile
import subprocess

# ---------------------------------------------------------------------------
# Groq client cache — loaded once, reused across all requests
# Same pattern as ImageToText's MODEL_CACHE
# ---------------------------------------------------------------------------
CLIENT_CACHE = {}
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

 # 🔑 Replace with your actual key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")
# ---------------------------------------------------------------------------
# Whisper model to use via Groq
# Options: "whisper-large-v3" (best) or "whisper-large-v3-turbo" (faster)
# ---------------------------------------------------------------------------
GROQ_WHISPER_MODEL = "whisper-large-v3"

# ---------------------------------------------------------------------------
# Max file size allowed — 25MB (Groq's limit is also 25MB)
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def get_groq_client():
    """
    Returns a cached Groq client.
    Same pattern as ImageToText's get_trocr_model() / get_m2m100_model().
    """
    if "groq" not in CLIENT_CACHE:
        try:
            from groq import Groq
            CLIENT_CACHE["groq"] = Groq(api_key=GROQ_API_KEY)
        except ImportError:
            raise ImportError(
                "Groq SDK not installed. Run: pip install groq"
            )
    return CLIENT_CACHE["groq"]


def extract_audio_from_video(video_path):
    """
    Extract audio from video using FFmpeg.
    Returns path to a temporary WAV file.
    Install FFmpeg: sudo apt install ffmpeg
    """
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio.close()

    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        temp_audio.name
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        os.unlink(temp_audio.name)
        raise RuntimeError(
            f"FFmpeg failed. Make sure FFmpeg is installed.\n"
            f"Ubuntu: sudo apt install ffmpeg\n"
            f"Mac: brew install ffmpeg\n"
            f"Error: {result.stderr}"
        )

    return temp_audio.name


def transcribe_with_groq(file_path, language=None):
    client = get_groq_client()

    kwargs = {
        "model": GROQ_WHISPER_MODEL,
        "response_format": "verbose_json",
    }
    if language:
        language = language.strip().lower()

    if language and language != "auto":
        kwargs["language"] = language


    with open(file_path, "rb") as f:
        response = client.audio.transcriptions.create(file=f, **kwargs)

    # Debug log to see what fields exist
    print("Groq raw response:", response.__dict__)

    return {
        "text": response.text.strip() if hasattr(response, "text") else "",
        "language": getattr(response, "language", "unknown"),
    }



# ---------------------------------------------------------------------------
# Public helpers called by views.py
# ---------------------------------------------------------------------------

def transcribe_uploaded_audio(audio_file_obj, language=None):
    """Transcribe a Django UploadedFile (audio)."""

    # File size check
    if audio_file_obj.size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")

    suffix = os.path.splitext(audio_file_obj.name)[-1] or ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in audio_file_obj.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        return transcribe_with_groq(tmp_path, language=language)
    finally:
        os.unlink(tmp_path)


def transcribe_uploaded_video(video_file_obj, language=None):
    """Extract audio from video, then transcribe."""

    if video_file_obj.size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")

    suffix = os.path.splitext(video_file_obj.name)[-1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in video_file_obj.chunks():
            tmp.write(chunk)
        tmp_video_path = tmp.name

    tmp_audio_path = None
    try:
        tmp_audio_path = extract_audio_from_video(tmp_video_path)
        return transcribe_with_groq(tmp_audio_path, language=language)
    finally:
        os.unlink(tmp_video_path)
        if tmp_audio_path and os.path.exists(tmp_audio_path):
            os.unlink(tmp_audio_path)


def transcribe_microphone_blob(audio_bytes, language=None):
    """Transcribe raw audio bytes recorded from browser microphone."""

    if len(audio_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Recording too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return transcribe_with_groq(tmp_path, language=language)
    finally:
        os.unlink(tmp_path)