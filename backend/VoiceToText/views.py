from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import (
    transcribe_uploaded_audio,
    transcribe_uploaded_video,
    transcribe_microphone_blob,
)

# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def index(request):
    return render(request, "VoiceToText/index.html")

# ---------------------------------------------------------------------------
# Transcribe uploaded audio file
# ---------------------------------------------------------------------------

@csrf_exempt
def transcribe_audio(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    audio_file = request.FILES.get("audio_file")
    if not audio_file:
        return JsonResponse({"error": "No audio file provided."}, status=400)

    language = request.POST.get("language", "").strip()

    if language.lower() in ["", "auto"]:
        language = None

    try:
        result = transcribe_uploaded_audio(audio_file, language=language)
        return JsonResponse({
            "success": True,
            "text": result["text"],
            "language": result["language"],
        })
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Transcription failed: {str(e)}"}, status=500)

# ---------------------------------------------------------------------------
# Transcribe uploaded video file
# ---------------------------------------------------------------------------

@csrf_exempt
def transcribe_video(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    video_file = request.FILES.get("video_file")
    if not video_file:
        return JsonResponse({"error": "No video file provided."}, status=400)

    language = request.POST.get("language")

    try:
        result = transcribe_uploaded_video(video_file, language=language)
        return JsonResponse({
            "success": True,
            "text": result["text"],
            "language": result["language"],
        })
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Transcription failed: {str(e)}"}, status=500)

# ---------------------------------------------------------------------------
# Transcribe microphone recording
# ---------------------------------------------------------------------------

@csrf_exempt
def transcribe_microphone(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=405)

    audio_blob = request.FILES.get("audio_blob")
    if not audio_blob:
        return JsonResponse({"error": "No microphone audio received."}, status=400)

    language = request.POST.get("language")

    try:
        audio_bytes = audio_blob.read()
        result = transcribe_microphone_blob(audio_bytes, language=language)
        return JsonResponse({
            "success": True,
            "text": result["text"],
            "language": result["language"],
        })
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Transcription failed: {str(e)}"}, status=500)
