"""
NEXA HUB — Views (DB-backed, Full)
/api/save-fitness/  → saves user form data to DB
/api/process/       → AI response using DB data (session_id se)
/api/qa/            → post-report Q&A using DB data
/api/history/       → user ki last 7 days entries
/api/set-goal/      → user ka goal set karo
"""

import json, os, re, tempfile, base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from VoiceAssistant.VoiceAssistant.services.ai_engine import get_ai_response
from django.shortcuts import render

def home(request):
    return render(request, "VoiceAssistant/index.html")
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def index(request):
    return render(request, 'voice_assistant/index.html')


# ══════════════════════════════════════════════════════════════
# API: SAVE FITNESS DATA  (HTML form → DB)
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def save_fitness(request):
    """
    Saves user-entered fitness data to FitnessEntry table.
    Body: {
        session_id, date?,
        steps, sleep_hours, water_liters, weight_kg, height_cm,
        calories_burned, calories_consumed,
        heart_rate_resting, heart_rate_avg, heart_rate_max,
        stress_score, recovery_score, mood,
        deep_sleep_hours, rem_sleep_hours,
        bedtime, wake_time, sleep_quality, notes
    }
    """
    try:
        data       = json.loads(request.body)
        session_id = data.get('session_id', '').strip()

        if not session_id:
            return JsonResponse({'success': False, 'error': 'session_id required'}, status=400)

        # Check at least one metric provided
        metric_fields = [
            'steps', 'sleep_hours', 'water_liters', 'weight_kg',
            'calories_burned', 'calories_consumed', 'heart_rate_resting',
            'heart_rate_avg', 'stress_score', 'recovery_score'
        ]
        has_data = any(
            data.get(f) not in (None, '', 'null', 0)
            for f in metric_fields
        )
        if not has_data:
            return JsonResponse(
                {'success': False, 'error': 'Koi bhi data provide nahi kiya!'},
                status=400
            )

        from VoiceAssistant.VoiceAssistant.db_service import save_fitness_entry
        entry = save_fitness_entry(session_id, data)

        return JsonResponse({
            'success':  True,
            'message':  f"✅ Data save ho gaya! ({entry.get('date')})",
            'entry':    entry,
            'overall_score': entry.get('overall_score', 0),
        })

    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )


# ══════════════════════════════════════════════════════════════
# API: GET USER HISTORY
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST", "GET"])
def get_history(request):
    """Returns last N days of fitness entries for a session."""
    try:
        if request.method == 'GET':
            session_id = request.GET.get('session_id', '')
            days       = int(request.GET.get('days', 7))
        else:
            data       = json.loads(request.body)
            session_id = data.get('session_id', '')
            days       = int(data.get('days', 7))

        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)

        from VoiceAssistant.VoiceAssistant.db_service import get_last_n_days, get_today
        entries  = get_last_n_days(session_id, days)
        today    = get_today(session_id)

        return JsonResponse({
            'success':  True,
            'entries':  entries,
            'today':    today,
            'count':    len(entries),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# API: SET GOAL
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def set_goal(request):
    """
    Body: { session_id, metric, target_value }
    metric: steps | sleep_hours | water_liters | weight_kg | calories_burned
    """
    try:
        data         = json.loads(request.body)
        session_id   = data.get('session_id', '')
        metric       = data.get('metric', '')
        target_value = data.get('target_value')

        if not all([session_id, metric, target_value is not None]):
            return JsonResponse({'success': False, 'error': 'session_id, metric, target_value required'}, status=400)

        from VoiceAssistant.VoiceAssistant.db_service import set_goal as db_set_goal
        goal = db_set_goal(session_id, metric, float(target_value))

        return JsonResponse({
            'success': True,
            'message': f"🎯 Goal set: {metric} = {target_value}",
            'goal':    goal,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
# API: MAIN AI PROCESS  (with session_id)
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def process_input(request):
    try:
        data       = json.loads(request.body)
        model      = data.get('model', '')
        sub_model  = data.get('sub_model', '')
        user_input = data.get('text', '').strip()
        context    = data.get('context', {})
        session_id = data.get('session_id', 'default')

        if not user_input:
            return JsonResponse({'error': 'No input provided'}, status=400)

        # Inject session_id into context for health service
        context['session_id'] = session_id

        # Handle inline "save" commands from voice/text
        # e.g. "Save my steps 9000 sleep 7.5 water 2.5"
        inline = _parse_inline_save(user_input)
        if inline and model == 'healthcare' and sub_model == 'fitness_tracker':
            from VoiceAssistant.VoiceAssistant.db_service import save_fitness_entry
            inline['session_id'] = session_id
            entry = save_fitness_entry(session_id, inline)
            # After saving, auto-generate daily summary
            context['auto_summary'] = True
            user_input = 'daily summary'

        result = get_ai_response(model, sub_model, user_input, context)

        # Save chat log to DB
        try:
            from VoiceAssistant.VoiceAssistant.db_service import save_chat
            save_chat(session_id, 'user',  user_input,
                      model=model, sub_model=sub_model)
            save_chat(session_id, 'ai', result.get('response', ''),
                      model=model, sub_model=sub_model,
                      intent=result.get('type', ''),
                      report_type=result.get('type', ''),
                      report_data=result.get('data'))
        except Exception:
            pass

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse(
            {'response': 'Kuch galat ho gaya, dobara try karo.', 'error': str(e)},
            status=500
        )


def _parse_inline_save(text: str) -> dict:
    """
    Parse inline save commands like:
    'save steps 9000 sleep 7 water 2.5 weight 68'
    'update today steps 10000 sleep 8 water 3'
    Returns dict of fields or None if not a save command.
    """
    import re
    t = text.lower()
    triggers = ['save my', 'save today', 'update today', 'log my',
                'mera data save', 'aaj ka data', 'save data']
    if not any(tr in t for tr in triggers):
        return None

    fields = {}
    patterns = {
        'steps':              r'steps?\s+(\d+)',
        'sleep_hours':        r'sleep\s+([\d.]+)',
        'water_liters':       r'water\s+([\d.]+)',
        'weight_kg':          r'weight\s+([\d.]+)',
        'calories_burned':    r'cal(?:ories?)?\s+burned?\s+(\d+)',
        'calories_consumed':  r'cal(?:ories?)?\s+(?:consumed?|intake|khaya)\s+(\d+)',
        'heart_rate_resting': r'heart\s+rate?\s+(\d+)',
        'stress_score':       r'stress\s+(\d+)',
        'recovery_score':     r'recovery\s+(\d+)',
    }
    for field, pattern in patterns.items():
        m = re.search(pattern, t)
        if m:
            fields[field] = m.group(1)

    return fields if fields else None


# ══════════════════════════════════════════════════════════════
# API: POST-REPORT Q&A  (routes through main process_input)
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def report_qa(request):
    """
    Q&A endpoint — proxies to get_ai_response with report_context in context.
    This way it uses the same working flow as /api/process/.
    """
    try:
        data           = json.loads(request.body)
        question       = data.get('question', '').strip()
        report_context = data.get('report_context') or {}
        session_id     = data.get('session_id', 'default')

        if not question:
            return JsonResponse({'error': 'No question provided'}, status=400)

        context = {
            'session_id':     session_id,
            'report_context': report_context,
        }

        result = get_ai_response('healthcare', 'fitness_tracker', question, context)

        # Attach report_context forward for chained Q&A
        if not result.get('report_context') and report_context:
            result['report_context'] = report_context

        return JsonResponse(result)

    except Exception as e:
        import traceback
        return JsonResponse(
            {
                'response': f'Q&A Error: {str(e)}',
                'error':    str(e),
                'trace':    traceback.format_exc(),
            },
            status=500
        )


# ══════════════════════════════════════════════════════════════
# API: TEXT TO SPEECH
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        lang = data.get('lang', 'en')

        if not text or not GTTS_AVAILABLE:
            return JsonResponse({'error': 'TTS unavailable'}, status=400)

        lang_map = {'en':'en','hi':'hi','mr':'mr','pa':'pa','te':'te','ta':'ta','bn':'bn','gu':'gu'}
        gtts_lang = lang_map.get(lang, 'en')
        clean = re.sub(r'\*\*|__|\\*|_|`', '', text)
        clean = re.sub(r'[^\w\s.,!?;:\-\(\)\n]', ' ', clean)[:500]

        tts = gTTS(text=clean, lang=gtts_lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tts.save(tmp.name); tmp_path = tmp.name

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
        data     = json.loads(request.body)
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
        return JsonResponse({'success': True, 'message': f'Email sent: {receiver}'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Email failed: {str(e)}'})