# response_engine.py

# =========================
# FALLBACK RESPONSES
# =========================

FALLBACK_MESSAGE = "I couldn't clearly identify the issue. Please rephrase your symptoms."

UNKNOWN_RESPONSE = "No specific recommendation available. Please consult a doctor if symptoms persist."


# =========================
# RESPONSE BUILDER
# =========================

def build_response(retrieval_result: dict):
    """
    Input from retrieval_engine

    Returns structured response for API / voice assistant
    """

    if not retrieval_result:
        return {
            "status": "error",
            "message": FALLBACK_MESSAGE
        }

    # =========================
    # EMERGENCY CASE
    # =========================

    if retrieval_result.get("status") == "emergency":
        return {
            "status": "emergency",
            "symptom": retrieval_result["emergency"]["symptom"],
            "message": retrieval_result["message"]
        }

    symptoms = retrieval_result.get("symptoms", [])
    remedies = retrieval_result.get("remedies", {})

    if not symptoms:
        return {
            "status": "ok",
            "message": FALLBACK_MESSAGE,
            "data": {}
        }

    # =========================
    # NORMAL RESPONSE BUILD
    # =========================

    response_blocks = []

    for symptom in symptoms:

        advice = remedies.get(symptom)

        if advice:
            if isinstance(advice, list):
                advice_text = ", ".join(advice)
            else:
                advice_text = str(advice)

            response_blocks.append({
                "symptom": symptom,
                "advice": advice_text
            })

        else:
            response_blocks.append({
                "symptom": symptom,
                "advice": UNKNOWN_RESPONSE
            })

    return {
        "status": "ok",
        "count": len(symptoms),
        "response": response_blocks
    }