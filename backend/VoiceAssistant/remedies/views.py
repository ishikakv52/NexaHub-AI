from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import traceback

from .services.cleaner import clean
from .services.language_engine import detect_language
from .services.translation_engine import translate_to_english
from .services.intent_engine import detect_intent
from .services.ml_engine import predict_intent
from .services.symptom_engine import extract_symptoms
from .services.severity_engine import calculate_severity
from .services.retrieval_engine import retrieve
from .services.ranking_engine import rank_recommendations
from .services.response_engine import build_response
from .services.memory_engine import save_message, get_history

def ai_chat(request):
    return render(request, "chat.html")

def safe_body_from_raw(raw):
    try:
        if not raw:
            return {}
        decoded = raw.decode("utf-8").strip()
        if not decoded:
            return {}
        return json.loads(decoded)
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return {}

@csrf_exempt
def process_remedy(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        raw_body = request.body
        print(">>> RAW BODY:", raw_body)
        print(">>> LENGTH:", len(raw_body))

        body = safe_body_from_raw(raw_body)
        print(">>> PARSED BODY:", body)

        user_id = body.get("user_id", "default")
        message = body.get("message", "")
        print(">>> MESSAGE:", message)

        if not message or not isinstance(message, str) or not message.strip():
            return JsonResponse(
                {"status": "error", "error": "No input provided",
                 "hint": "Send JSON like {\"message\": \"fever\", \"user_id\": \"1\"}"},
                status=400
            )

        message = message.strip()
        history = get_history(user_id)
        save_message(user_id, "user", message)
        cleaned_text = clean(message)
        lang = detect_language(cleaned_text)
        translated = translate_to_english(cleaned_text)
        canonical_text = translated.get("translated_text") or cleaned_text
        ml_intent = predict_intent(canonical_text)
        rule_intent = detect_intent(canonical_text)
        intent = "medical" if ml_intent == "medical" else rule_intent
        symptoms_data = extract_symptoms(canonical_text)
        symptoms = symptoms_data.get("symptoms", [])
        severity = calculate_severity(symptoms)
        retrieval = retrieve(symptoms) or {}
        ranked = rank_recommendations(symptoms, retrieval.get("remedies", {}))
        response = build_response(retrieval)
        save_message(user_id, "assistant", response)

        return JsonResponse({
            "status": "success",
            "input": message,
            "language": lang,
            "intent": intent,
            "symptoms": symptoms,
            "severity": severity,
            "ranked_recommendations": ranked,
            "response": response,
            "history": history
        })

    except Exception as e:
        print("\n--- ERROR TRACE ---")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(e), "type": "server_error"}, status=500)
