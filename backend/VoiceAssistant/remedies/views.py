# views.py — Fixed: status key collision, single-word disease detection

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json, traceback

from .services.cleaner import clean
from .services.language_engine import detect_language
from .services.translation_engine import translate_to_english
from .services.intent_engine import detect_intent
from .services.ml_engine import predict_intent
from .services.symptom_engine import extract_symptoms, extract_symptoms_merged
from .services.severity_engine import calculate_severity
from .services.retrieval_engine import retrieve
from .services.ranking_engine import rank_recommendations
from .services.response_engine import build_response
from .services.memory_engine import save_message, get_history
from .services.fever_engine import is_fever_query, ask_for_temperature, analyze_fever
from .services.vitals_engine import detect_vital_type, ask_for_vital, analyze_vital


def ai_chat(request):
    return render(request, "chat.html")

def index(request):
    return render(request, "index.html")


# ── Body parser ──────────────────────────────────────────────
def _parse_body(raw):
    try:
        if not raw: return {}
        decoded = raw.decode("utf-8").strip()
        if not decoded: return {}
        return json.loads(decoded)
    except Exception:
        return {}


# ── Lang resolver ────────────────────────────────────────────
def _lang_key(lang_obj) -> str:
    if isinstance(lang_obj, dict):
        lang_obj = lang_obj.get("language", "en")
    m = {"en":"en","hi":"hi","hinglish":"hinglish","mr":"mr","gu":"gu","others":"en"}
    return m.get(str(lang_obj).lower(), "en")


# ── In-memory pending state ──────────────────────────────────
_PENDING = {}
def _get_pending(uid): return _PENDING.get(uid)
def _set_pending(uid, s): _PENDING[uid] = s
def _clear_pending(uid): _PENDING.pop(uid, None)


# ── Success wrapper — prevents **result from overwriting status ──
def _ok(**kwargs):
    """Always returns status=success. Separates inner result into 'data' key
    while also hoisting common fields to top level for the frontend."""
    return {"status": "success", **kwargs}


# ── Main view ────────────────────────────────────────────────
@csrf_exempt
def process_remedy(request):
    if request.method != "POST":
        return JsonResponse({"status":"error","message":"Only POST allowed"}, status=405)

    try:
        body    = _parse_body(request.body)
        user_id = body.get("user_id", "default")
        message = body.get("message", "")

        if not message or not isinstance(message, str) or not message.strip():
            return JsonResponse({
                "status":"error",
                "error":"No input provided",
                "hint": 'Send JSON: {"message":"fever","user_id":"1"}'
            }, status=400)

        message = message.strip()
        history = get_history(user_id)
        save_message(user_id, "user", message)

        cleaned_text = clean(message)
        lang         = detect_language(cleaned_text)
        lang_key     = _lang_key(lang)

        # ── PENDING FLOW (follow-up answers) ───────────────
        pending = _get_pending(user_id)
        if pending:
            ptype = pending.get("type")

            if ptype == "fever":
                result = analyze_fever(message, lang_key)
                _clear_pending(user_id)
                save_message(user_id, "assistant", result.get("advice",""))
                return JsonResponse(_ok(
                    flow            = "fever_analysis",
                    input           = message,
                    language        = lang,
                    fever_severity  = result.get("fever_severity"),
                    temperature_f   = result.get("temperature_f"),
                    temperature_c   = result.get("temperature_c"),
                    is_emergency    = result.get("is_emergency", False),
                    see_doctor      = result.get("see_doctor", False),
                    advice          = result.get("advice",""),
                    lang            = result.get("lang", lang_key),
                ))

            elif ptype == "vitals":
                vital_type = pending.get("vital_type")
                result = analyze_vital(vital_type, message, lang_key)

                if result.get("status") == "needs_value":
                    # parse failed — ask again
                    save_message(user_id, "assistant", result.get("question",""))
                    return JsonResponse(_ok(
                        flow       = "vitals_followup",
                        input      = message,
                        language   = lang,
                        vital_type = vital_type,
                        question   = result.get("question",""),
                        lang       = result.get("lang", lang_key),
                    ))

                _clear_pending(user_id)
                save_message(user_id, "assistant", result.get("advice",""))
                return JsonResponse(_ok(
                    flow        = "vitals_analysis",
                    input       = message,
                    language    = lang,
                    vital_type  = result.get("vital_type"),
                    value       = result.get("value"),
                    level       = result.get("level"),
                    is_emergency= result.get("is_emergency", False),
                    see_doctor  = result.get("see_doctor", False),
                    advice      = result.get("advice",""),
                    lang        = result.get("lang", lang_key),
                ))

        # ── NORMAL FLOW ────────────────────────────────────
        translated     = translate_to_english(cleaned_text)
        canonical_text = translated.get("translated_text") or cleaned_text

        # FEVER
        if is_fever_query(cleaned_text) or is_fever_query(canonical_text):
            _set_pending(user_id, {"type": "fever"})
            q = ask_for_temperature(lang_key)
            save_message(user_id, "assistant", q.get("question",""))
            return JsonResponse(_ok(
                flow       = "fever_question",
                input      = message,
                language   = lang,
                sub_intent = "fever",
                question   = q.get("question",""),
                lang       = q.get("lang", lang_key),
            ))

        # VITALS
        vital_type = detect_vital_type(cleaned_text) or detect_vital_type(canonical_text)
        if vital_type:
            _set_pending(user_id, {"type":"vitals","vital_type":vital_type})
            q = ask_for_vital(vital_type, lang_key)
            save_message(user_id, "assistant", q.get("question",""))
            return JsonResponse(_ok(
                flow       = "vitals_question",
                input      = message,
                language   = lang,
                sub_intent = "vitals",
                vital_type = vital_type,
                question   = q.get("question",""),
                lang       = q.get("lang", lang_key),
            ))

        # REMEDY
        symptoms_data = extract_symptoms_merged(cleaned_text, canonical_text)
        symptoms      = symptoms_data.get("symptoms", [])
        severity      = calculate_severity(symptoms)
        retrieval     = retrieve(symptoms) or {}
        ranked        = rank_recommendations(symptoms, retrieval.get("remedies",{}))
        response      = build_response(retrieval, lang=lang_key)
        save_message(user_id, "assistant", str(response))

        return JsonResponse(_ok(
            flow                  = "remedy",
            input                 = message,
            language              = lang,
            symptoms              = symptoms,
            severity              = severity,
            ranked_recommendations= ranked,
            response              = response,
        ))

    except Exception as e:
        print("\n--- ERROR TRACE ---")
        print(traceback.format_exc())
        return JsonResponse({"status":"error","message":str(e),"type":"server_error"}, status=500)