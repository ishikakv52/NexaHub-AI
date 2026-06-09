"""
NEXA HUB — Views (DB-backed, Full) — FIXED
"""
from functools import wraps
import json, os, re, tempfile, base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
import traceback

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def home(request):
    return render(request, 'VoiceAssistant/index.html')


# ══════════════════════════════════════════════════════════════
# SAFE JSON PARSER  (always returns dict, never crashes)
# ══════════════════════════════════════════════════════════════
def _safe_json(request):
    """Crash-proof JSON parser. Always returns a dict."""
    try:
        body = request.body
        if isinstance(body, bytes):
            body = body.decode('utf-8', errors='ignore')
        body = body.strip()
        if not body:
            return {}
        return json.loads(body)
    except json.JSONDecodeError as e:
        return {'_error': 'invalid_json', '_detail': str(e)}
    except Exception as e:
        return {'_error': 'read_failed', '_detail': str(e)}


# ══════════════════════════════════════════════════════════════
# API: SAVE FITNESS DATA
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def save_fitness(request):
    try:
        data = _safe_json(request)

        if data.get('_error'):
            return JsonResponse({'success': False, 'error': 'Invalid JSON body'}, status=400)

        session_id = str(data.get('session_id', '')).strip()
        if not session_id:
            return JsonResponse({'success': False, 'error': 'session_id required'}, status=400)

        metric_fields = [
            'steps', 'weight_kg', 'water_liters', 'calories_burned',
            'calories_consumed', 'height_cm', 'sleep_hours', 'sleep_quality',
            'bedtime', 'wake_time', 'deep_sleep_hours', 'rem_sleep_hours',
            'heart_rate_resting', 'heart_rate_max', 'heart_rate_avg',
            'stress_score', 'recovery_score', 'mood', 'notes'
        ]

        clean_data = {}
        has_data = False

        for key in metric_fields:
            val = data.get(key)
            if val is None:
                continue
            if isinstance(val, str):
                val = val.strip()
                if val in ['', 'null', 'None']:
                    continue
            clean_data[key] = val
            has_data = True

        if not has_data:
            return JsonResponse({'success': False, 'error': 'Koi valid data provide nahi kiya!'}, status=400)

        from .db_service import save_fitness_entry
        entry = save_fitness_entry(session_id, clean_data)

        return JsonResponse({
            'success': True,
            'message': f"✅ Data save ho gaya! ({entry.get('date')})",
            'entry': entry,
            'overall_score': entry.get('overall_score', 0),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)


# ══════════════════════════════════════════════════════════════
# API: GET USER HISTORY
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST", "GET"])
def get_history(request):
    try:
        if request.method == 'GET':
            session_id = request.GET.get('session_id', '')
            days = int(request.GET.get('days', 7))
        else:
            data = _safe_json(request)
            session_id = data.get('session_id', '')
            days = int(data.get('days', 7))

        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)

        from .db_service import get_last_n_days, get_today
        entries = get_last_n_days(session_id, days)
        today = get_today(session_id)

        return JsonResponse({
            'success': True,
            'entries': entries,
            'today': today,
            'count': len(entries),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# API: SET GOAL
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def set_goal(request):
    try:
        data = _safe_json(request)
        session_id = data.get('session_id', '')
        metric = data.get('metric', '')
        target_value = data.get('target_value')

        if not all([session_id, metric, target_value is not None]):
            return JsonResponse({'success': False, 'error': 'session_id, metric, target_value required'}, status=400)

        from .db_service import set_goal as db_set_goal
        goal = db_set_goal(session_id, metric, float(target_value))

        return JsonResponse({
            'success': True,
            'message': f"🎯 Goal set: {metric} = {target_value}",
            'goal': goal,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# API: MAIN AI PROCESS  ← MAIN FIX YAHAN HAI
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def process_input(request):
    try:
        # ── Step 1: Parse JSON safely ──────────────────────
        try:
            raw_body = request.body.decode('utf-8', errors='ignore').strip()
            if not raw_body:
                return JsonResponse({'success': False, 'error': 'Empty request body'}, status=400)
            data = json.loads(raw_body)
        except json.JSONDecodeError as je:
            return JsonResponse({'success': False, 'error': f'Invalid JSON: {str(je)}'}, status=400)

        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'error': 'Body must be a JSON object'}, status=400)

        # ── Step 2: Extract fields ─────────────────────────
        model      = str(data.get('model', '')).strip()
        sub_model  = str(data.get('sub_model', '')).strip()
        user_input = str(data.get('text', '')).strip()
        session_id = str(data.get('session_id', 'default')).strip()

        # text is required
        if not user_input:
            return JsonResponse({'success': False, 'error': 'text field is required and cannot be empty'}, status=400)

        # model/sub_model can have defaults if missing
        if not model:
            model = 'healthcare'
        if not sub_model:
            sub_model = 'fitness_tracker'

        # ── Step 3: Build context ──────────────────────────
        context = data.get('context', {})
        if not isinstance(context, dict):
            context = {}
        context['session_id'] = session_id

        print(f"[NEXA] model={model} sub={sub_model} text={user_input[:60]} session={session_id}")

        # ── Step 4: Call AI engine ─────────────────────────
        try:
            from .services.ai_engine import get_ai_response
            result = get_ai_response(
                model=model,
                sub_model=sub_model,
                user_input=user_input,
                context=context
            )
        except Exception as ai_err:
            return JsonResponse({
                'success': False,
                'error': 'AI pipeline failed',
                'detail': str(ai_err),
                'trace': traceback.format_exc()
            }, status=500)

        # ── Step 5: Normalize result ───────────────────────
        if result is None:
            result = {'response': 'No response generated', 'type': 'normal'}
        elif not isinstance(result, dict):
            result = {'response': str(result), 'type': 'normal'}

        # Always ensure 'response' key exists
        if 'response' not in result:
            result['response'] = 'Processed successfully'

        return JsonResponse(result, safe=True, json_dumps_params={'default': str})

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }, status=500)


# ══════════════════════════════════════════════════════════════
# API: POST-REPORT Q&A
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def report_qa(request):
    try:
        data = _safe_json(request)
        question = str(data.get('question', '')).strip()
        report_context = data.get('report_context') or {}
        session_id = data.get('session_id', 'default')

        if not question:
            return JsonResponse({'error': 'No question provided'}, status=400)

        context = {
            'session_id': session_id,
            'report_context': report_context,
        }

        from .services.ai_engine import get_ai_response
        result = get_ai_response('healthcare', 'fitness_tracker', question, context)

        if not result.get('report_context') and report_context:
            result['report_context'] = report_context

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'response': f'Q&A Error: {str(e)}',
            'error': str(e),
            'trace': traceback.format_exc(),
        }, status=500)


# ══════════════════════════════════════════════════════════════
# API: TEXT TO SPEECH
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech(request):
    try:
        data = _safe_json(request)
        text = str(data.get('text', '')).strip()
        lang = str(data.get('lang', 'en')).strip()

        if not text or not GTTS_AVAILABLE:
            return JsonResponse({'error': 'TTS unavailable or empty text'}, status=400)

        lang_map = {'en': 'en', 'hi': 'hi', 'mr': 'mr', 'pa': 'pa', 'te': 'te', 'ta': 'ta', 'bn': 'bn', 'gu': 'gu'}
        gtts_lang = lang_map.get(lang, 'en')
        clean = re.sub(r'\*\*|__|\\*|_|`', '', text)
        clean = re.sub(r'[^\w\s.,!?;:\-\(\)\n]', ' ', clean)[:500]

        tts = gTTS(text=clean, lang=gtts_lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tts.save(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, 'rb') as f:
            audio_b64 = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp_path)

        return JsonResponse({'audio': audio_b64, 'format': 'mp3'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# API: SEND EMAIL
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def send_email_view(request):
    try:
        data = _safe_json(request)
        subject  = data.get('subject', 'No Subject')
        body     = data.get('body', '')
        sender   = data.get('sender', '')
        receiver = data.get('receiver', '')

        if not all([subject, body, sender, receiver]):
            return JsonResponse({'success': False, 'message': 'Saari fields fill karo!'}, status=400)

        settings.EMAIL_HOST_USER = sender
        send_mail(
            subject=subject, message=body,
            from_email=sender, recipient_list=[receiver],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': f'Email sent to: {receiver}'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Email failed: {str(e)}'})