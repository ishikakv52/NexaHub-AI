# vitals_engine.py
# Handles BP, Blood Glucose, Heart Rate (BPM), SpO2 parsing and advice.
# NO API KEYS USED. Pure rule-based multilingual engine.

import re

# ===========================
# LANGUAGE RESOLVER
# ===========================

def _resolve_lang(lang) -> str:
    if isinstance(lang, dict):
        lang = lang.get("language", "en")
    mapping = {"en": "en", "hi": "hi", "hinglish": "hinglish", "mr": "mr", "gu": "gu", "others": "en"}
    return mapping.get(str(lang).lower(), "en")


# ===========================
# VITAL KEYWORDS DETECTOR
# ===========================

BP_WORDS       = ["bp", "blood pressure", "raktachaap", "ब्लड प्रेशर", "रक्तचाप", "raktdaab", "bldpressure"]
SUGAR_WORDS    = ["sugar", "glucose", "blood glucose", "blood sugar", "diabetes", "शुगर", "ग्लूकोज", "madhumeh", "शर्करा"]
HEART_WORDS    = ["bpm", "heart rate", "pulse", "heartrate", "dil ki dhadkan", "dil tez", "dhadkan tez", "dhadkan", "dil dheere", "dhadkan slow", "dil bahut tez", "heart beat", "धड़कन", "धड़कन तेज", "धड़कन धीमी", "hृदय गति"]
SPO2_WORDS     = ["spo2", "oxygen", "o2", "saturation", "oxygen level", "ऑक्सीजन", "oxygen saturation", "pulseox"]

def detect_vital_type(text: str):
    """Returns the vital type string or None."""
    t = text.lower()
    # Check heart rate BEFORE bp (both share 'bpm' / 'pulse' words)
    if any(w in t for w in HEART_WORDS):    return "heart_rate"
    if any(w in t for w in SPO2_WORDS):     return "spo2"
    if any(w in t for w in SUGAR_WORDS):    return "sugar"
    if any(w in t for w in BP_WORDS):       return "bp"
    return None


# ===========================
# VALUE PARSERS
# ===========================

def _parse_bp(text: str):
    """Extract systolic/diastolic: 120/80, 120 over 80, 120 80"""
    m = re.search(r"(\d{2,3})\s*[/\\over\s]+\s*(\d{2,3})", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    # single number — might be systolic only
    m2 = re.search(r"\b(\d{2,3})\b", text)
    if m2:
        return int(m2.group(1)), None
    return None, None

def _parse_glucose(text: str):
    """Extract glucose value (mg/dL or mmol/L)."""
    m = re.search(r"\b(\d+\.?\d*)\s*(mg|mmol|mg/dl|mmol/l)?\b", text.lower())
    if m:
        val = float(m.group(1))
        unit = (m.group(2) or "mg").lower()
        if "mmol" in unit:
            val = round(val * 18, 1)   # convert to mg/dL
            unit = "mg/dL (converted)"
        return val, "mg/dL"
    return None, None

def _parse_heartrate(text: str):
    m = re.search(r"\b(\d{2,3})\b", text)
    return int(m.group(1)) if m else None

def _parse_spo2(text: str):
    m = re.search(r"\b(\d{2,3})\s*%?\b", text)
    if m:
        val = int(m.group(1))
        if 50 <= val <= 100:
            return val
    return None


# ===========================
# ASK-FOR-VALUE PROMPTS
# ===========================

ASK_VALUE = {
    "bp": {
        "en":       "Please share your BP reading (e.g., '130/85'). I'll analyze it for you.",
        "hi":       "कृपया अपना बीपी बताएं (जैसे '130/85')। मैं आपके लिए विश्लेषण करूंगा।",
        "hinglish": "Apna BP batao (jaise '130/85'). Main analyse karunga.",
        "mr":       "कृपया तुमचे BP सांगा (उदा. '130/85'). मी विश्लेषण करेन.",
        "gu":       "₹ BP ₹ (₹. '130/85'). ₹ ₹.",
    },
    "sugar": {
        "en":       "Please share your blood sugar/glucose level (e.g., '140 mg/dL' or '7.8 mmol/L'). Is this fasting or post-meal?",
        "hi":       "कृपया अपना ब्लड शुगर स्तर बताएं (जैसे '140 mg/dL'). क्या यह खाली पेट है या खाने के बाद?",
        "hinglish": "Apna blood sugar level batao (jaise '140 mg/dL'). Kya yeh fasting hai ya khane ke baad?",
        "mr":       "कृपया तुमची रक्तातील साखर सांगा (उदा. '140 mg/dL'). हे उपाशी पोटी आहे की जेवणानंतर?",
        "gu":       "₹ blood sugar ₹ (₹. '140 mg/dL'). ₹ fasting ₹ ₹?",
    },
    "heart_rate": {
        "en":       "Please share your heart rate in BPM (e.g., '88 BPM'). Are you resting or after activity?",
        "hi":       "कृपया अपनी हार्ट रेट बताएं (जैसे '88 BPM'). क्या आप आराम में हैं या व्यायाम के बाद?",
        "hinglish": "Apni heart rate BPM mein batao (jaise '88 BPM'). Rest mein ho ya exercise ke baad?",
        "mr":       "कृपया तुमचा हृदय गती सांगा (उदा. '88 BPM'). आराम करत आहात की व्यायामानंतर?",
        "gu":       "₹ heart rate BPM ₹ (₹. '88 BPM'). ₹ rest ₹ exercise ₹?",
    },
    "spo2": {
        "en":       "Please share your SpO2 (oxygen saturation) reading in % (e.g., '97%').",
        "hi":       "कृपया अपना SpO2 (ऑक्सीजन सैचुरेशन) प्रतिशत में बताएं (जैसे '97%')।",
        "hinglish": "Apna SpO2 percentage mein batao (jaise '97%').",
        "mr":       "कृपया तुमचे SpO2 टक्केवारीत सांगा (उदा. '97%').",
        "gu":       "₹ SpO2 % ₹ (₹. '97%').",
    },
}


# ===========================
# ANALYSIS: BLOOD PRESSURE
# ===========================

def _analyze_bp(sys_val, dia_val, lang_key):
    advices = {
        "normal": {
            "en":       "✅ BP {bp} is normal (below 120/80). Great! Maintain healthy lifestyle.",
            "hi":       "✅ BP {bp} सामान्य है (120/80 से कम)। बढ़िया! स्वस्थ जीवनशैली बनाए रखें।",
            "hinglish": "✅ BP {bp} normal hai. Badiya! Healthy lifestyle maintain karo.",
            "mr":       "✅ BP {bp} सामान्य आहे. उत्कृष्ट! निरोगी जीवनशैली ठेवा.",
            "gu":       "✅ BP {bp} ₹ normal ₹.",
        },
        "elevated": {
            "en":       "⚠️ BP {bp} is elevated (120-129/below 80). Reduce salt, exercise regularly, manage stress. Monitor daily.",
            "hi":       "⚠️ BP {bp} थोड़ा बढ़ा हुआ है। नमक कम करें, नियमित व्यायाम करें, तनाव प्रबंधन करें।",
            "hinglish": "⚠️ BP {bp} thoda elevated hai. Salt kam karo, exercise karo, stress manage karo.",
            "mr":       "⚠️ BP {bp} थोडा वाढलेला आहे. मीठ कमी करा, व्यायाम करा.",
            "gu":       "⚠️ BP {bp} ₹ elevated ₹. ₹ ₹ ₹.",
        },
        "stage1": {
            "en":       "🚨 Stage 1 Hypertension ({bp}). See a doctor. Lifestyle changes essential: reduce salt, exercise, reduce alcohol, manage weight.",
            "hi":       "🚨 Stage 1 उच्च रक्तचाप ({bp})। डॉक्टर से मिलें। नमक कम करें, व्यायाम करें।",
            "hinglish": "🚨 Stage 1 High BP ({bp}). Doctor se milo. Salt, exercise, weight manage karo.",
            "mr":       "🚨 Stage 1 उच्च रक्तदाब ({bp}). डॉक्टरांना भेटा.",
            "gu":       "🚨 Stage 1 High BP ({bp}). ₹ doctor ₹.",
        },
        "stage2": {
            "en":       "🆘 Stage 2 Hypertension ({bp}). Consult doctor urgently. Medication likely needed. Avoid stress, heavy exertion, and salt.",
            "hi":       "🆘 Stage 2 उच्च रक्तचाप ({bp})। तुरंत डॉक्टर से मिलें। दवाई जरूरी हो सकती है।",
            "hinglish": "🆘 Stage 2 High BP ({bp}). Turant doctor se milo. Dawai zaroor chahiye ho sakti hai.",
            "mr":       "🆘 Stage 2 उच्च रक्तदाब ({bp}). ताबडतोब डॉक्टरांना भेटा.",
            "gu":       "🆘 Stage 2 High BP ({bp}). ₹ ₹ doctor ₹.",
        },
        "crisis": {
            "en":       "🆘 HYPERTENSIVE CRISIS ({bp})! Go to Emergency Room IMMEDIATELY. Call 108. Sit calmly. Don't exert yourself.",
            "hi":       "🆘 हाइपरटेंसिव संकट ({bp})! तुरंत आपातकालीन कक्ष जाएं। 108 पर कॉल करें।",
            "hinglish": "🆘 BP Crisis ({bp})! Turant Emergency Room jao. 108 call karo.",
            "mr":       "🆘 BP संकट ({bp})! ताबडतोब Emergency Room ला जा. 108 कॉल करा.",
            "gu":       "🆘 BP Crisis ({bp})! ₹ Emergency ₹ 108 ₹.",
        },
        "low": {
            "en":       "⬇️ Low BP ({bp}) detected. Drink water and ORS immediately. Lie down, elevate legs. Eat salty snacks. Avoid standing suddenly.",
            "hi":       "⬇️ कम BP ({bp})। तुरंत पानी और ORS पियें। लेटकर पैर ऊपर करें। नमकीन खाएं।",
            "hinglish": "⬇️ Low BP ({bp}). Turant paani aur ORS piyein. Let jao, pair upar karo. Namkeen khao.",
            "mr":       "⬇️ कमी BP ({bp}). लगेच पाणी आणि ORS प्या. झोपा, पाय वर करा.",
            "gu":       "⬇️ Low BP ({bp}). ₹ ₹ ORS ₹.",
        },
    }

    bp_str = f"{sys_val}/{dia_val}" if dia_val else f"{sys_val}"

    if sys_val < 90:
        level = "low"
    elif sys_val <= 120 and (dia_val is None or dia_val <= 80):
        level = "normal"
    elif sys_val <= 129 and (dia_val is None or dia_val < 80):
        level = "elevated"
    elif sys_val <= 139 or (dia_val and dia_val <= 89):
        level = "stage1"
    elif sys_val <= 179 or (dia_val and dia_val <= 119):
        level = "stage2"
    else:
        level = "crisis"

    template = advices[level].get(lang_key, advices[level]["en"])
    return {
        "status": "ok",
        "vital_type": "bp",
        "value": bp_str,
        "level": level,
        "is_emergency": level == "crisis",
        "see_doctor": level in ("stage1", "stage2", "crisis"),
        "advice": template.replace("{bp}", bp_str),
        "lang": lang_key,
    }


# ===========================
# ANALYSIS: BLOOD SUGAR
# ===========================

def _analyze_sugar(val, lang_key):
    advices = {
        "normal_fasting": {
            "en":       "✅ Blood sugar {val} mg/dL is in normal fasting range (70-99). Excellent! Keep up the healthy diet.",
            "hi":       "✅ ब्लड शुगर {val} mg/dL सामान्य (70-99) है। बढ़िया!",
            "hinglish": "✅ Blood sugar {val} mg/dL normal hai. Badiya!",
            "mr":       "✅ रक्तातील साखर {val} mg/dL सामान्य आहे.",
            "gu":       "✅ Blood sugar {val} mg/dL normal ₹.",
        },
        "prediabetes": {
            "en":       "⚠️ Blood sugar {val} mg/dL indicates prediabetes range (100-125 fasting). Action needed:\n• Reduce sugar and refined carbs\n• Exercise 30 min/day\n• Maintain healthy weight\n• Get HbA1c test",
            "hi":       "⚠️ {val} mg/dL प्रीडायबिटीज स्तर है। कदम उठाएं:\n• शुगर और मैदा कम करें\n• 30 मिनट व्यायाम करें\n• HbA1c टेस्ट कराएं",
            "hinglish": "⚠️ {val} mg/dL prediabetes range hai. Action lo:\n• Sugar aur maida kam karo\n• 30 min exercise karo\n• HbA1c test karao",
            "mr":       "⚠️ {val} mg/dL प्रीडायबेटिस आहे. साखर कमी करा. व्यायाम करा.",
            "gu":       "⚠️ {val} mg/dL prediabetes ₹.",
        },
        "diabetic": {
            "en":       "🚨 Blood sugar {val} mg/dL is in diabetic range (126+ fasting or 200+ post-meal).\n• Take prescribed medication\n• Avoid sweets, refined carbs, fruit juice\n• Walk 30-45 min after meals\n• Monitor glucose daily\n• Consult doctor for HbA1c and management plan",
            "hi":       "🚨 {val} mg/dL डायबिटीज स्तर है। डॉक्टर की दवा लें, मीठा बंद करें, रोज 30-45 मिनट चलें।",
            "hinglish": "🚨 {val} mg/dL diabetes range mein hai. Doctor ki dawai lo, meetha avoid karo, 30-45 min walk karo.",
            "mr":       "🚨 {val} mg/dL मधुमेह आहे. डॉक्टरांची औषधे घ्या, गोड टाळा.",
            "gu":       "🚨 {val} mg/dL diabetes ₹. ₹ doctor ₹.",
        },
        "hypoglycemia": {
            "en":       "🆘 LOW BLOOD SUGAR ({val} mg/dL) — Hypoglycemia!\n• Eat 15g fast sugar NOW (glucose tablets, juice, candy)\n• Recheck in 15 minutes\n• If not improving, call 108 immediately\n• Do NOT drive or be alone",
            "hi":       "🆘 कम ब्लड शुगर ({val} mg/dL) — हाइपोग्लाइसीमिया!\n• तुरंत 15g तेज शुगर खाएं (ग्लूकोज, जूस, मिठाई)\n• 15 मिनट में फिर जांचें\n• अकेले न रहें",
            "hinglish": "🆘 Low blood sugar ({val} mg/dL)! Turant 15g fast sugar khaein. 15 min baad check karo. Akele mat raho.",
            "mr":       "🆘 कमी रक्तातील साखर ({val} mg/dL)! लगेच 15g जलद साखर खा. 15 मिनटांत पुन्हा तपासा.",
            "gu":       "🆘 Low blood sugar ({val} mg/dL)! ₹ ₹ 15g sugar ₹.",
        },
    }

    val_str = f"{val}"

    if val < 70:
        level = "hypoglycemia"
    elif val <= 99:
        level = "normal_fasting"
    elif val <= 125:
        level = "prediabetes"
    else:
        level = "diabetic"

    template = advices[level].get(lang_key, advices[level]["en"])
    return {
        "status": "ok",
        "vital_type": "sugar",
        "value": f"{val} mg/dL",
        "level": level,
        "is_emergency": level == "hypoglycemia",
        "see_doctor": level in ("diabetic", "prediabetes"),
        "advice": template.replace("{val}", val_str),
        "lang": lang_key,
    }


# ===========================
# ANALYSIS: HEART RATE
# ===========================

def _analyze_heart_rate(bpm, lang_key):
    advices = {
        "bradycardia_critical": {
            "en": "🆘 CRITICAL: Heart rate {bpm} BPM is dangerously low. Go to Emergency Room. Call 108.",
            "hi": "🆘 गंभीर: हार्ट रेट {bpm} BPM बहुत कम है। तुरंत आपातकाल कक्ष जाएं। 108 कॉल करें।",
            "hinglish": "🆘 Critical: Heart rate {bpm} BPM bahut kam hai. Emergency Room jao. 108 call karo.",
            "mr": "🆘 गंभीर: हृदय गती {bpm} BPM खूप कमी आहे. Emergency Room ला जा.",
            "gu": "🆘 ₹ Heart rate {bpm} BPM ₹ ₹. 108 ₹.",
        },
        "bradycardia": {
            "en": "⚠️ Heart rate {bpm} BPM is lower than normal (below 60). Rest. See a doctor soon if you feel faint, dizzy, or short of breath.",
            "hi": "⚠️ हार्ट रेट {bpm} BPM कम है। आराम करें। डॉक्टर से मिलें।",
            "hinglish": "⚠️ Heart rate {bpm} BPM low hai. Rest karo. Doctor se milo agar dizziness ya saans ki dikkat ho.",
            "mr": "⚠️ हृदय गती {bpm} BPM कमी आहे. डॉक्टरांना भेटा.",
            "gu": "⚠️ Heart rate {bpm} BPM ₹ low ₹.",
        },
        "normal": {
            "en": "✅ Heart rate {bpm} BPM is normal (60-100 at rest). Keep it up!",
            "hi": "✅ हार्ट रेट {bpm} BPM सामान्य है। बढ़िया!",
            "hinglish": "✅ Heart rate {bpm} BPM normal hai. Badiya!",
            "mr": "✅ हृदय गती {bpm} BPM सामान्य आहे.",
            "gu": "✅ Heart rate {bpm} BPM normal ₹.",
        },
        "tachycardia": {
            "en": "⚠️ Heart rate {bpm} BPM is elevated (above 100). Rest immediately. Practice slow deep breathing. Avoid caffeine. If it persists, see a doctor.",
            "hi": "⚠️ हार्ट रेट {bpm} BPM बढ़ा हुआ है। तुरंत आराम करें। गहरी सांस लें। कैफीन से बचें।",
            "hinglish": "⚠️ Heart rate {bpm} BPM high hai. Turant rest karo. Deep breathing karo. Caffeine avoid karo.",
            "mr": "⚠️ हृदय गती {bpm} BPM वाढलेली आहे. लगेच आराम करा. खोल श्वास घ्या.",
            "gu": "⚠️ Heart rate {bpm} BPM high ₹. ₹ ₹ deep breathing ₹.",
        },
        "tachycardia_critical": {
            "en": "🆘 DANGER: Heart rate {bpm} BPM is critically high. Go to Emergency Room NOW. Call 108. Sit calmly. Do NOT exert.",
            "hi": "🆘 खतरा: हार्ट रेट {bpm} BPM बहुत ज़्यादा है। तुरंत आपातकाल जाएं। 108 कॉल करें।",
            "hinglish": "🆘 Danger: Heart rate {bpm} BPM bahut zyada hai. Emergency Room jao. 108 call karo.",
            "mr": "🆘 धोका: हृदय गती {bpm} BPM खूप जास्त आहे. ताबडतोब Emergency Room ला जा.",
            "gu": "🆘 Heart rate {bpm} BPM ₹ critical ₹. 108 ₹.",
        },
    }

    if bpm < 40:      level = "bradycardia_critical"
    elif bpm < 60:    level = "bradycardia"
    elif bpm <= 100:  level = "normal"
    elif bpm <= 150:  level = "tachycardia"
    else:             level = "tachycardia_critical"

    template = advices[level].get(lang_key, advices[level]["en"])
    return {
        "status": "ok",
        "vital_type": "heart_rate",
        "value": f"{bpm} BPM",
        "level": level,
        "is_emergency": level in ("bradycardia_critical", "tachycardia_critical"),
        "see_doctor": level in ("bradycardia", "tachycardia", "bradycardia_critical", "tachycardia_critical"),
        "advice": template.replace("{bpm}", str(bpm)),
        "lang": lang_key,
    }


# ===========================
# ANALYSIS: SPO2
# ===========================

def _analyze_spo2(val, lang_key):
    advices = {
        "normal": {
            "en": "✅ SpO2 {val}% is normal (95-100%). Excellent oxygen levels!",
            "hi": "✅ SpO2 {val}% सामान्य है। बढ़िया ऑक्सीजन स्तर!",
            "hinglish": "✅ SpO2 {val}% normal hai. Badiya!",
            "mr": "✅ SpO2 {val}% सामान्य आहे.",
            "gu": "✅ SpO2 {val}% normal ₹.",
        },
        "low": {
            "en": "⚠️ SpO2 {val}% is low (90-94%). Action needed:\n• Sit upright\n• Take slow deep breaths\n• Move to fresh air\n• Avoid exertion\n• If it doesn't improve in 10-15 min, see a doctor.",
            "hi": "⚠️ SpO2 {val}% कम है। सीधे बैठें, गहरी सांस लें, ताज़ी हवा में जाएं। 10-15 मिनट में ठीक न हो तो डॉक्टर से मिलें।",
            "hinglish": "⚠️ SpO2 {val}% low hai. Sidha baithein, deep breathing karo, fresh air mein jao. 10-15 min mein theek na ho toh doctor.",
            "mr": "⚠️ SpO2 {val}% कमी आहे. सरळ बसा, खोल श्वास घ्या, ताज्या हवेत जा.",
            "gu": "⚠️ SpO2 {val}% ₹ low ₹. ₹ ₹ ₹.",
        },
        "critical": {
            "en": "🆘 EMERGENCY: SpO2 {val}% is critically low (below 90%)!\n• Call 108 immediately\n• Sit upright — do NOT lie flat\n• Breathe slowly and deliberately\n• This is a medical emergency",
            "hi": "🆘 आपातकाल: SpO2 {val}% बहुत कम है!\n• तुरंत 108 पर कॉल करें\n• सीधे बैठें — लेटें नहीं\n• यह चिकित्सा आपातकाल है",
            "hinglish": "🆘 Emergency: SpO2 {val}% bahut low hai! Turant 108 call karo. Sidha baithein. Let mat jao.",
            "mr": "🆘 आणीबाणी: SpO2 {val}% खूप कमी आहे! लगेच 108 कॉल करा. सरळ बसा.",
            "gu": "🆘 Emergency: SpO2 {val}% ₹ critical ₹! 108 ₹.",
        },
    }

    if val >= 95:     level = "normal"
    elif val >= 90:   level = "low"
    else:             level = "critical"

    template = advices[level].get(lang_key, advices[level]["en"])
    return {
        "status": "ok",
        "vital_type": "spo2",
        "value": f"{val}%",
        "level": level,
        "is_emergency": level == "critical",
        "see_doctor": level in ("low", "critical"),
        "advice": template.replace("{val}", str(val)),
        "lang": lang_key,
    }


# ===========================
# PUBLIC API
# ===========================

def ask_for_vital(vital_type: str, lang) -> dict:
    lang_key = _resolve_lang(lang)
    q_map = ASK_VALUE.get(vital_type, ASK_VALUE["bp"])
    return {
        "status": "needs_value",
        "vital_type": vital_type,
        "question": q_map.get(lang_key, q_map["en"]),
        "lang": lang_key,
    }


def analyze_vital(vital_type: str, value_text: str, lang) -> dict:
    lang_key = _resolve_lang(lang)
    t = value_text.lower()

    if vital_type == "bp":
        sys_val, dia_val = _parse_bp(t)
        if sys_val is None:
            return ask_for_vital("bp", lang)
        return _analyze_bp(sys_val, dia_val, lang_key)

    elif vital_type == "sugar":
        val, _ = _parse_glucose(t)
        if val is None:
            return ask_for_vital("sugar", lang)
        return _analyze_sugar(val, lang_key)

    elif vital_type == "heart_rate":
        val = _parse_heartrate(t)
        if val is None:
            return ask_for_vital("heart_rate", lang)
        return _analyze_heart_rate(val, lang_key)

    elif vital_type == "spo2":
        val = _parse_spo2(t)
        if val is None:
            return ask_for_vital("spo2", lang)
        return _analyze_spo2(val, lang_key)

    return {"status": "error", "message": "Unknown vital type"}