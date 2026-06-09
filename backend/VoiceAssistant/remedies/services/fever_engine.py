# fever_engine.py
# Handles fever-specific flow: detect fever intent, ask for temperature,
# classify severity, and give multilingual advice. No API keys used.

import re

# ===========================
# FEVER KEYWORD TRIGGERS
# ===========================

FEVER_TRIGGERS = {
    "en":       ["fever", "high temperature", "body heat", "temperature"],
    "hi":       ["bukhar", "bukhaar", "jwar", "tap", "taap", "garmi", "tez garmi"],
    "hinglish": ["bukhar hai", "fever hai", "body hot hai", "temperature hai", "bukhar ho gaya"],
    "mr":       ["ताप", "जवर", "taap", "javar"],
    "gu":       ["तावा", "bukhar", "fever"],
}

ALL_FEVER_WORDS = set()
for words in FEVER_TRIGGERS.values():
    ALL_FEVER_WORDS.update(words)


# ===========================
# SEVERITY THRESHOLDS (°F)
# ===========================

THRESHOLDS = {
    "normal":    (95.0,  99.0),   # Normal
    "low_grade": (99.1, 100.3),   # Low-grade — monitor
    "moderate":  (100.4, 102.2),  # Moderate — home care
    "high":      (102.3, 104.0),  # High — consult doctor
    "very_high": (104.1, 999.0),  # Very high — emergency
}


# ===========================
# MULTILINGUAL QUESTION PROMPTS
# ===========================

FEVER_ASK_TEMP = {
    "en":       "You mentioned fever. Please tell me your temperature (in °F or °C) so I can help better. Example: '102 F' or '39 C'.",
    "hi":       "आपने बुखार का उल्लेख किया। कृपया अपना तापमान बताएं (°F या °C में) ताकि मैं बेहतर सहायता कर सकूं। उदाहरण: '102 F' या '39 C'।",
    "hinglish": "Aapne fever mention kiya. Apna temperature batao (°F ya °C mein) taaki main aapki zyada madad kar sakun. Example: '102 F' ya '39 C'.",
    "mr":       "तुम्ही तापाचा उल्लेख केला. कृपया तुमचे तापमान सांगा (°F किंवा °C मध्ये) जेणेकरून मी अधिक चांगली मदत करू शकेन. उदाहरण: '102 F' किंवा '39 C'.",
    "gu":       "તmaine fever નો ઉ Monhle leach  ₹ ₹ ₹ ₹ (°F ₹ °C) ₹ ₹ ₹.",
}


# ===========================
# MULTILINGUAL RESPONSES BY SEVERITY
# ===========================

FEVER_RESPONSES = {
    "normal": {
        "en":       "✅ Your temperature ({temp}°F) is within normal range. You're doing well! Stay hydrated and monitor if symptoms change.",
        "hi":       "✅ आपका तापमान ({temp}°F) सामान्य है। अच्छे से हाइड्रेटेड रहें और नज़र रखें।",
        "hinglish": "✅ Aapka temperature ({temp}°F) normal hai. Hydrated raho aur nazar rakho.",
        "mr":       "✅ तुमचे तापमान ({temp}°F) सामान्य आहे. हायड्रेटेड राहा.",
        "gu":       "✅ ₹ temperature ({temp}°F) ₹ ₹.",
    },
    "low_grade": {
        "en":       "🌡️ Low-grade fever ({temp}°F). Rest well, drink plenty of fluids (water, ORS, coconut water). Use a damp cloth on forehead. Monitor every 4 hours.",
        "hi":       "🌡️ हल्का बुखार ({temp}°F)। अच्छे से आराम करें, खूब तरल पियें। माथे पर गीला कपड़ा रखें। हर 4 घंटे में जांचें।",
        "hinglish": "🌡️ Halka bukhar ({temp}°F). Rest karo, bahut paani aur ORS piyein. Maathey par geela kapda rakhein. Har 4 ghante mein check karo.",
        "mr":       "🌡️ हलका ताप ({temp}°F). आराम करा, भरपूर द्रव प्या. कपाळावर ओला कापड ठेवा. दर 4 तासांनी तपासा.",
        "gu":       "🌡️ ₹ fever ({temp}°F). ₹ ₹ ₹.",
    },
    "moderate": {
        "en":       "⚠️ Moderate fever ({temp}°F). Recommendations:\n• Rest completely\n• Drink ORS, water, coconut water\n• Use damp cloth or cold compress\n• Wear light clothes\n• Avoid heavy food\n• If fever doesn't reduce in 24-48 hours, consult a doctor.",
        "hi":       "⚠️ मध्यम बुखार ({temp}°F)। सिफारिशें:\n• पूरी तरह आराम करें\n• ORS, पानी, नारियल पानी पियें\n• गीला कपड़ा लगाएं\n• हल्के कपड़े पहनें\n• 24-48 घंटे में ठीक न हो तो डॉक्टर से मिलें।",
        "hinglish": "⚠️ Moderate bukhar ({temp}°F):\n• Puri tarah rest karo\n• ORS, paani, coconut water piyein\n• Geela kapda lagao\n• Halke kapde pahano\n• 24-48 ghante mein theek na ho toh doctor se milo.",
        "mr":       "⚠️ मध्यम ताप ({temp}°F):\n• पूर्ण आराम करा\n• ORS, पाणी, नारळपाणी प्या\n• ओला कापड लावा\n• हलके कपडे घाला\n• 24-48 तासांत बरे न झाल्यास डॉक्टरांना भेटा.",
        "gu":       "⚠️ ₹ fever ({temp}°F):\n• ₹ rest ₹\n• ORS, ₹, coconut water ₹\n• ₹ ₹ ₹ 24-48 ₹ ₹ ₹ doctor ₹.",
    },
    "high": {
        "en":       "🚨 High fever ({temp}°F)! Please consult a doctor soon.\n• Rest immediately\n• Apply cold compress\n• Take paracetamol if available (as per dosage)\n• Drink fluids continuously\n• Watch for: rash, severe headache, stiff neck, difficulty breathing → Go to ER immediately.",
        "hi":       "🚨 तेज बुखार ({temp}°F)! कृपया जल्दी डॉक्टर से मिलें।\n• तुरंत आराम करें\n• ठंडी पट्टी लगाएं\n• पेरासिटामोल लें (खुराक के अनुसार)\n• लगातार तरल पियें\n• अगर चकत्ते, तेज सिरदर्द, गर्दन अकड़न, सांस लेने में दिक्कत हो तो तुरंत अस्पताल जाएं।",
        "hinglish": "🚨 Tez bukhar ({temp}°F)! Jald doctor se milo.\n• Turant rest karo\n• Thanda compress lagao\n• Paracetamol lo agar available ho\n• Lagatar fluid piyein\n• Agar rash, sar dard, gardan akdan, saans mein dikkat ho toh turant hospital jao.",
        "mr":       "🚨 तीव्र ताप ({temp}°F)! लवकर डॉक्टरांना भेटा.\n• लगेच आराम करा\n• थंड शेकणे लावा\n• पॅरासिटामॉल घ्या\n• सतत द्रव प्या\n• पुरळ, तीव्र डोकेदुखी, मान कडक होणे, श्वास घेण्यास त्रास झाल्यास तत्काळ रुग्णालयात जा.",
        "gu":       "🚨 ₹ fever ({temp}°F)! ₹ ₹ doctor ₹.\n• Paracetamol ₹ • ₹ ₹ hospital ₹.",
    },
    "very_high": {
        "en":       "🆘 EMERGENCY! Very high fever ({temp}°F / above 104°F).\n\n🏥 GO TO HOSPITAL IMMEDIATELY — Call 108 / 112\n\nWhile waiting:\n• Sponge body with lukewarm water\n• Do NOT use ice directly\n• Remove excess clothing\n• Fan the person gently\n• Do NOT give aspirin to children",
        "hi":       "🆘 आपातकाल! बहुत तेज बुखार ({temp}°F / 104°F से ऊपर)।\n\n🏥 तुरंत अस्पताल जाएं — 108 / 112 पर कॉल करें\n\nइंतज़ार के दौरान:\n• गुनगुने पानी से शरीर पोंछें\n• सीधे बर्फ न लगाएं\n• अतिरिक्त कपड़े हटाएं",
        "hinglish": "🆘 Emergency! Bahut tez bukhar ({temp}°F)!\n\n🏥 Abhi hospital jao — 108 / 112 call karo\n\nIntezaar ke dauran:\n• Gungune paani se body ponchhein\n• Seedha ice mat lagao\n• Extra kapde hatao",
        "mr":       "🆘 आणीबाणी! अत्यंत तीव्र ताप ({temp}°F)!\n\n🏥 ताबडतोब रुग्णालयात जा — 108 / 112 कॉल करा\n\nप्रतीक्षा करताना:\n• कोमट पाण्याने अंग पुसा\n• थेट बर्फ लावू नका",
        "gu":       "🆘 Emergency! ₹ fever ({temp}°F)!\n\n🏥 ₹ hospital ₹ — 108 / 112 ₹\n\n• ₹ ₹ ₹ ₹ body ₹",
    },
}


# ===========================
# HELPERS
# ===========================

def _celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def _extract_temperature(text: str):
    """
    Parses temperature from user text.
    Returns (temp_f: float, unit: str) or (None, None)
    """
    text = text.lower().strip()

    # Patterns: 102f, 102 f, 102°f, 39c, 39 c, 39°c, 102.5 f
    pattern = r"(\d+\.?\d*)\s*[°]?\s*([cfCF])\b"
    match = re.search(pattern, text)

    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        if unit == "c":
            return _celsius_to_fahrenheit(value), "C"
        else:
            return value, "F"

    # Bare number: if > 45, likely Fahrenheit; if <= 45, likely Celsius
    bare = re.search(r"\b(\d+\.?\d*)\b", text)
    if bare:
        value = float(bare.group(1))
        if value > 45:
            return value, "F"
        elif 30 <= value <= 45:
            return _celsius_to_fahrenheit(value), "C"

    return None, None


def _classify_fever(temp_f: float) -> str:
    for level, (low, high) in THRESHOLDS.items():
        if low <= temp_f <= high:
            return level
    return "very_high"


# ===========================
# PUBLIC API
# ===========================

def is_fever_query(text: str) -> bool:
    """Returns True if the user's text is primarily about fever."""
    t = text.lower()
    for word in ALL_FEVER_WORDS:
        if word in t:
            return True
    return False


def ask_for_temperature(lang: str) -> dict:
    """
    Returns a follow-up question asking for temperature.
    """
    lang_key = _resolve_lang(lang)
    return {
        "status": "needs_temperature",
        "question": FEVER_ASK_TEMP.get(lang_key, FEVER_ASK_TEMP["en"]),
        "lang": lang_key,
    }


def analyze_fever(temp_text: str, lang: str) -> dict:
    """
    Given a temperature string and detected language, return full analysis.
    """
    lang_key = _resolve_lang(lang)
    temp_f, unit = _extract_temperature(temp_text)

    if temp_f is None:
        return {
            "status": "needs_temperature",
            "question": FEVER_ASK_TEMP.get(lang_key, FEVER_ASK_TEMP["en"]),
        }

    severity = _classify_fever(temp_f)
    temp_c = round((temp_f - 32) * 5 / 9, 1)

    response_template = FEVER_RESPONSES[severity].get(lang_key, FEVER_RESPONSES[severity]["en"])
    response_text = response_template.replace("{temp}", str(temp_f))

    return {
        "status": "ok",
        "fever_severity": severity,
        "temperature_f": temp_f,
        "temperature_c": temp_c,
        "is_emergency": severity == "very_high",
        "see_doctor": severity in ("high", "very_high"),
        "advice": response_text,
        "lang": lang_key,
    }


def _resolve_lang(lang) -> str:
    """Normalize language code from language_engine output."""
    if isinstance(lang, dict):
        lang = lang.get("language", "en")
    mapping = {
        "en": "en", "hi": "hi", "hinglish": "hinglish",
        "mr": "mr", "gu": "gu", "others": "en",
    }
    return mapping.get(str(lang).lower(), "en")