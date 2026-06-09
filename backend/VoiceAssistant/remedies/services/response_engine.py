# response_engine.py — Dual-response multilingual builder
# Returns BOTH a home remedy response AND a general medical advice response.
# No API keys used.

# ===========================
# MULTILINGUAL STATIC STRINGS
# ===========================

FALLBACK_MESSAGE = {
    "en":       "I couldn't clearly identify the issue. Please rephrase your symptoms.",
    "hi":       "मैं समस्या स्पष्ट रूप से पहचान नहीं सका। कृपया अपने लक्षण फिर से बताएं।",
    "hinglish": "Mujhe clearly samajh nahi aaya. Please apne symptoms dobara batao.",
    "mr":       "मला समस्या स्पष्टपणे समजली नाही. कृपया तुमची लक्षणे पुन्हा सांगा.",
    "gu":       "મને સ્પષ્ટ સમજ ન આવી. કૃপા કરીને તમારા લક્ષણો ફરીથી કહો.",
}

UNKNOWN_REMEDY = {
    "en":       "No specific home remedy found for this. Try rest and hydration.",
    "hi":       "इसके लिए कोई विशेष घरेलू उपाय नहीं मिला। आराम करें और पानी पियें।",
    "hinglish": "Iske liye koi specific ghar ka nuskha nahi mila. Rest karo aur paani piyein.",
    "mr":       "यासाठी विशिष्ट घरगुती उपाय सापडला नाही. आराम करा आणि पाणी प्या.",
    "gu":       "આ માટે ઘremi ₹ ₹ ₹ ₹. ₹ ₹.",
}

DOCTOR_ADVICE = {
    "en":       "⚕️ Please consult a doctor for proper diagnosis and treatment.",
    "hi":       "⚕️ उचित निदान और इलाज के लिए कृपया डॉक्टर से मिलें।",
    "hinglish": "⚕️ Sahi diagnosis aur treatment ke liye doctor se zaroor milo.",
    "mr":       "⚕️ योग्य निदान आणि उपचारासाठी कृपया डॉक्टरांना भेटा.",
    "gu":       "⚕️ ₹ ₹ ₹ ₹ doctor ₹.",
}

# General medical advice per symptom (non-home-remedy guidance)
GENERAL_ADVICE = {
    "headache": {
        "en": "Headaches can result from dehydration, stress, eye strain, or tension. If headaches are frequent or severe, consult a neurologist. OTC pain relievers like paracetamol can help temporarily.",
        "hi": "सिरदर्द के कारण: डिहाइड्रेशन, तनाव, आंखों पर जोर। बार-बार या तेज दर्द हो तो न्यूरोलॉजिस्ट से मिलें। पेरासिटामोल अस्थायी राहत दे सकता है।",
        "hinglish": "Headache ka karan dehydration, stress, ya eye strain ho sakta hai. Baar baar ho toh neurologist se milo. Paracetamol temporarily help kar sakta hai.",
        "mr": "डोकेदुखी निर्जलीकरण, ताण किंवा डोळ्यांवरील ताणामुळे होऊ शकते. वारंवार होत असल्यास न्यूरोलॉजिस्टला भेटा.",
        "gu": "₹ ₹ ₹ ₹. ₹ ₹ doctor ₹.",
    },
    "fever": {
        "en": "Fever is your body fighting infection. Monitor temperature regularly. Paracetamol (per dosage) helps reduce fever. See a doctor if fever persists over 2 days or rises above 103°F.",
        "hi": "बुखार संक्रमण से लड़ने की शरीर की प्रतिक्रिया है। पेरासिटामोल लें। 2 दिन से ज़्यादा रहे या 103°F से ऊपर जाए तो डॉक्टर से मिलें।",
        "hinglish": "Fever body ka infection se ladne ka tarika hai. Paracetamol lo. 2 din se zyada rahe ya 103°F se upar jaye toh doctor se milo.",
        "mr": "ताप हे संसर्गाशी लढण्याचे शरीराचे साधन आहे. पॅरासिटामॉल घ्या. 2 दिवसांपेक्षा जास्त राहिल्यास डॉक्टरांकडे जा.",
        "gu": "₹ ₹ ₹. Paracetamol ₹. 2 ₹ ₹ ₹ doctor ₹.",
    },
    "cold": {
        "en": "Common cold is viral — antibiotics don't help. Rest, fluids, and antihistamines can manage symptoms. See a doctor if symptoms worsen or last over 10 days.",
        "hi": "सर्दी वायरल है — एंटीबायोटिक काम नहीं करते। आराम, तरल पदार्थ और एंटीहिस्टामाइन लक्षण नियंत्रित करते हैं।",
        "hinglish": "Sardi viral hai — antibiotics nahi chalenge. Rest aur antihistamine lo. 10 din se zyada ho toh doctor.",
        "mr": "सर्दी विषाणूजन्य असते — प्रतिजैविक उपयुक्त नाहीत. आराम आणि द्रव प्या.",
        "gu": "₹ ₹ viral ₹. ₹ ₹ ₹.",
    },
    "cough": {
        "en": "Cough can be viral, allergic, or due to acid reflux. Cough syrups can soothe. See a doctor if cough is persistent (over 3 weeks), has blood, or causes breathing difficulty.",
        "hi": "खांसी वायरल, एलर्जिक या एसिड रिफ्लक्स से हो सकती है। 3 हफ्ते से ज़्यादा रहे, खून आए या सांस में तकलीफ हो तो डॉक्टर से मिलें।",
        "hinglish": "Khansi viral, allergic ya acid reflux se ho sakti hai. 3 hafton se zyada ho ya blood aaye toh doctor.",
        "mr": "खोकला विषाणूजन्य, ऍलर्जीमुळे किंवा ऍसिड रिफ्लक्समुळे होऊ शकतो. 3 आठवड्यांपेक्षा जास्त असल्यास डॉक्टर.",
        "gu": "₹ viral ₹. 3 ₹ ₹ doctor ₹.",
    },
    "stomach_pain": {
        "en": "Stomach pain can be due to gas, indigestion, ulcers, or infection. Antacids can help for mild cases. See a doctor if pain is severe, sudden, or accompanied by vomiting/fever.",
        "hi": "पेट दर्द गैस, अपच, अल्सर या संक्रमण से हो सकता है। एंटासिड हल्के मामलों में मदद करता है।",
        "hinglish": "Pet dard gas, indigestion ya ulcer se ho sakta hai. Antacid help kar sakta hai. Severe ho toh doctor.",
        "mr": "पोटदुखी गॅस, अपचन किंवा संसर्गामुळे होऊ शकते. तीव्र असल्यास डॉक्टर.",
        "gu": "₹ ₹ ₹ gas ₹. ₹ doctor ₹.",
    },
    "vomiting": {
        "en": "Vomiting can be due to food poisoning, viral infection, or motion sickness. Stay hydrated with ORS. See a doctor if vomiting is persistent or has blood.",
        "hi": "उल्टी फूड पॉइज़निंग, वायरल या मोशन सिकनेस से हो सकती है। ORS से हाइड्रेटेड रहें।",
        "hinglish": "Ulti food poisoning ya viral se ho sakti hai. ORS se hydrated raho. Baar baar ho toh doctor.",
        "mr": "उलटी अन्न विषबाधा किंवा संसर्गामुळे होऊ शकते. ORS प्या.",
        "gu": "₹ ₹ food poisoning ₹. ORS ₹.",
    },
    "diarrhea": {
        "en": "Diarrhea can be viral or bacterial. Key concern is dehydration — drink ORS regularly. See a doctor if it lasts over 2 days, has blood, or you have high fever.",
        "hi": "दस्त वायरल या बैक्टीरियल हो सकती है। ORS पियें। 2 दिन से ज़्यादा रहे, खून आए या तेज बुखार हो तो डॉक्टर।",
        "hinglish": "Diarrhea viral ya bacterial ho sakta hai. ORS piyein. 2 din se zyada ho toh doctor.",
        "mr": "अतिसार विषाणूजन्य किंवा जीवाणूजन्य असू शकतो. ORS नियमित प्या.",
        "gu": "₹ ₹. ORS ₹. 2 ₹ doctor ₹.",
    },
    "high_bp": {
        "en": "High blood pressure (hypertension) is a chronic condition requiring medical management. Medication, low-sodium diet, regular exercise, and stress reduction are key. Regular BP monitoring is essential.",
        "hi": "उच्च रक्तचाप एक दीर्घकालिक स्थिति है। दवा, कम नमक का खाना, नियमित व्यायाम और तनाव कम करना जरूरी है।",
        "hinglish": "High BP chronic condition hai. Dawai, low-salt diet, exercise aur stress management zaruri hai. Regular BP monitor karo.",
        "mr": "उच्च रक्तदाब ही दीर्घकालीन स्थिती आहे. औषधे, कमी मीठ, व्यायाम आणि ताण कमी करणे आवश्यक आहे.",
        "gu": "₹ BP chronic ₹. ₹ ₹ exercise ₹.",
    },
    "low_bp": {
        "en": "Low blood pressure can cause dizziness and fainting. Stay hydrated, avoid sudden position changes. Consult doctor to identify underlying cause.",
        "hi": "कम रक्तचाप से चक्कर और बेहोशी हो सकती है। हाइड्रेटेड रहें। डॉक्टर से कारण पता करें।",
        "hinglish": "Low BP se chakkar aur behoshi ho sakti hai. Hydrated raho. Doctor se karan puchho.",
        "mr": "कमी रक्तदाबामुळे चक्कर येऊ शकते. पाणी प्या. डॉक्टरांकडे जा.",
        "gu": "₹ BP ₹ ₹. ₹ ₹ doctor ₹.",
    },
    "high_sugar": {
        "en": "High blood glucose needs medical supervision. Work with your doctor on medication, dietary control (low glycemic foods), and regular exercise. HbA1c test every 3 months.",
        "hi": "उच्च रक्त शर्करा को चिकित्सा निगरानी की जरूरत है। डॉक्टर के साथ दवा, आहार नियंत्रण और व्यायाम पर काम करें।",
        "hinglish": "High blood sugar ko medical supervision chahiye. Doctor ke saath diet, exercise aur dawai manage karo. HbA1c test karwao.",
        "mr": "उच्च रक्तातील साखर वैद्यकीय देखरेखीखाली ठेवणे आवश्यक आहे. डॉक्टरांशी औषधे आणि आहार व्यवस्थापन करा.",
        "gu": "₹ blood sugar ₹ doctor ₹. ₹ diet ₹ exercise ₹.",
    },
    "low_sugar": {
        "en": "Hypoglycemia requires immediate sugar intake. Diabetic patients should always carry glucose tablets. Regular meals and proper insulin dosing prevent recurrence.",
        "hi": "हाइपोग्लाइसीमिया में तुरंत शुगर लेना जरूरी है। डायबिटीज के मरीज़ हमेशा ग्लूकोज टैबलेट रखें।",
        "hinglish": "Hypoglycemia mein turant sugar lena zaruri hai. Diabetic patients ke paas hamesha glucose tablets honi chahiye.",
        "mr": "हायपोग्लायसेमियामध्ये लगेच साखर घ्या. मधुमेही रुग्णांनी नेहमी ग्लूकोज गोळ्या जवळ ठेवाव्यात.",
        "gu": "₹ low sugar ₹ ₹ glucose ₹.",
    },
    "high_heart_rate": {
        "en": "Elevated heart rate (tachycardia) can be due to stress, dehydration, caffeine, or cardiac issues. If persistent or with chest pain, seek emergency care.",
        "hi": "तेज़ हृदय गति तनाव, डिहाइड्रेशन, कैफीन या दिल की समस्या से हो सकती है। लगातार रहे तो आपातकाल जाएं।",
        "hinglish": "High heart rate stress, caffeine ya cardiac issue se ho sakta hai. Persist kare ya chest pain ho toh emergency.",
        "mr": "जास्त हृदय गती ताण, कॉफी किंवा हृदयाच्या समस्येमुळे होऊ शकते. सतत असल्यास आपत्कालीन काळजी घ्या.",
        "gu": "₹ heart rate ₹ stress ₹ ₹. ₹ ₹ emergency ₹.",
    },
    "low_heart_rate": {
        "en": "Low heart rate (bradycardia) can be normal for athletes but may indicate a heart condition. See a doctor if below 50 BPM with symptoms like dizziness.",
        "hi": "धीमी हृदय गति एथलीट के लिए सामान्य हो सकती है लेकिन दिल की स्थिति भी हो सकती है। 50 BPM से कम और चक्कर हो तो डॉक्टर।",
        "hinglish": "Low heart rate athletes mein normal ho sakta hai par cardiac condition bhi ho sakta hai. 50 BPM se kam ho toh doctor.",
        "mr": "कमी हृदय गती खेळाडूंसाठी सामान्य असू शकते पण हृदयाची समस्या असू शकते. 50 BPM पेक्षा कमी असल्यास डॉक्टर.",
        "gu": "₹ heart rate athletes ₹ normal ₹. 50 BPM ₹ doctor ₹.",
    },
    "low_spo2": {
        "en": "Low SpO2 indicates reduced oxygen in blood. Normal is 95-100%. Below 94% needs medical attention. Below 90% is a medical emergency — call 108.",
        "hi": "कम SpO2 रक्त में ऑक्सीजन की कमी दर्शाता है। 95-100% सामान्य है। 94% से कम पर डॉक्टर। 90% से कम आपातकाल — 108 पर कॉल करें।",
        "hinglish": "Low SpO2 ka matlab blood mein oxygen ki kami hai. 95-100% normal hai. 94% se kam ho toh doctor. 90% se kam = emergency 108.",
        "mr": "कमी SpO2 म्हणजे रक्तात ऑक्सिजन कमी. 95-100% सामान्य. 94% पेक्षा कमी = डॉक्टर. 90% पेक्षा कमी = आणीबाणी.",
        "gu": "₹ SpO2 ₹. 95-100% normal. 94% ₹ ₹ doctor. 90% ₹ emergency 108.",
    },
    "dengue_symptoms": {
        "en": "Dengue requires medical supervision. Platelet count monitoring is critical. No self-medication with NSAIDs (ibuprofen, aspirin). Hospitalization may be needed.",
        "hi": "डेंगू में चिकित्सा निगरानी जरूरी है। प्लेटलेट काउंट की जांच करें। NSAIDs न लें।",
        "hinglish": "Dengue mein medical supervision zaruri hai. Platelet count monitor karo. NSAIDs mat lo. Hospitalization ki zarurat ho sakti hai.",
        "mr": "डेंगूसाठी वैद्यकीय देखरेख आवश्यक आहे. प्लेटलेट संख्या तपासा. NSAIDs घेऊ नका.",
        "gu": "Dengue ₹ medical ₹. Platelet ₹. NSAIDs ₹.",
    },
    "malaria_symptoms": {
        "en": "Malaria needs a blood smear test for confirmation. Anti-malarial drugs must be doctor-prescribed. Complete the full course of medication.",
        "hi": "मलेरिया में ब्लड स्मियर टेस्ट जरूरी है। डॉक्टर द्वारा निर्धारित एंटी-मलेरियल दवाएं लें।",
        "hinglish": "Malaria mein blood test zaruri hai. Doctor prescribed anti-malarial dawai lo. Poora course complete karo.",
        "mr": "मलेरियासाठी रक्त तपासणी आवश्यक आहे. डॉक्टरांनी सांगितलेली औषधे घ्या.",
        "gu": "Malaria ₹ blood test ₹. Doctor ₹ anti-malarial ₹.",
    },
    "typhoid_symptoms": {
        "en": "Typhoid requires antibiotics prescribed by a doctor. Drink boiled water. Complete the full antibiotic course to prevent relapse.",
        "hi": "टाइफॉइड में डॉक्टर द्वारा एंटीबायोटिक जरूरी है। उबला पानी पियें। पूरा कोर्स करें।",
        "hinglish": "Typhoid mein doctor prescribed antibiotic zaruri hai. Ubla paani piyein. Poora course complete karo.",
        "mr": "टायफॉइडसाठी डॉक्टरांचे प्रतिजैविक आवश्यक आहे. उकळलेले पाणी प्या.",
        "gu": "Typhoid ₹ antibiotic ₹ doctor ₹. ₹ ₹ ₹.",
    },
    "jaundice": {
        "en": "Jaundice needs liver function tests (LFT, bilirubin). Identify cause (hepatitis, obstruction). Strict alcohol abstinence. Medical supervision required.",
        "hi": "पीलिया में LFT और बिलीरुबिन टेस्ट जरूरी है। हेपेटाइटिस की जांच करें। शराब बिल्कुल नहीं।",
        "hinglish": "Jaundice mein LFT aur bilirubin test zaruri hai. Hepatitis check karo. Alcohol bilkul band karo.",
        "mr": "काविळीसाठी LFT आणि बिलीरुबिन तपासणी आवश्यक आहे. मद्यपान पूर्णपणे टाळा.",
        "gu": "Jaundice ₹ LFT test ₹. Alcohol ₹.",
    },
    "migraine": {
        "en": "Migraines can be managed with triptans (prescription) or OTC pain relievers. Keep a migraine diary. Avoid known triggers. A neurologist can create a prevention plan.",
        "hi": "माइग्रेन को ट्रिप्टन या OTC दर्दनाशक से नियंत्रित किया जा सकता है। ट्रिगर से बचें। न्यूरोलॉजिस्ट से परामर्श लें।",
        "hinglish": "Migraine ko triptans ya OTC painkillers se manage kar sakte ho. Triggers avoid karo. Neurologist se milo.",
        "mr": "माइग्रेन ट्रिप्टन्स किंवा वेदनाशामकांनी व्यवस्थापित करता येतो. ट्रिगर टाळा.",
        "gu": "₹ Migraine ₹ triptans ₹. Triggers ₹.",
    },
    "body_pain": {
        "en": "Body pain can be due to viral infection, overexertion, or fibromyalgia. Rest and OTC pain relievers help. See a doctor if pain is severe or unexplained.",
        "hi": "बदन दर्द वायरल संक्रमण, थकान या फाइब्रोमाइल्जिया से हो सकता है। आराम करें। गंभीर हो तो डॉक्टर।",
        "hinglish": "Body pain viral infection ya overexertion se ho sakta hai. Rest karo. Severe ho toh doctor.",
        "mr": "बदन दुखणे विषाणूजन्य संसर्ग किंवा जास्त थकव्यामुळे होऊ शकते. आराम करा.",
        "gu": "₹ body pain ₹ ₹. ₹ rest ₹.",
    },
}

# Generic fallback general advice for symptoms not in GENERAL_ADVICE
GENERIC_GENERAL = {
    "en":       "Monitor your symptoms closely. If they worsen or persist beyond 2-3 days, please consult a qualified doctor. Do not self-medicate beyond basic OTC remedies.",
    "hi":       "अपने लक्षणों पर ध्यान दें। 2-3 दिन में सुधार न हो या बिगड़ें तो डॉक्टर से मिलें। बिना सलाह के दवा न लें।",
    "hinglish": "Apne symptoms monitor karo. 2-3 din mein theek na ho toh doctor se milo. Bina salah ke dawai mat lo.",
    "mr":       "तुमच्या लक्षणांवर लक्ष ठेवा. 2-3 दिवसांत सुधारणा न झाल्यास डॉक्टरांना भेटा.",
    "gu":       "₹ ₹ ₹. 2-3 ₹ ₹ doctor ₹.",
}

HOME_REMEDY_HEADER = {
    "en":       "🏠 Home Remedy Suggestions",
    "hi":       "🏠 घरेलू उपाय",
    "hinglish": "🏠 Ghar ke Nuskhe",
    "mr":       "🏠 घरगुती उपाय",
    "gu":       "🏠 ₹ ₹",
}

GENERAL_ADVICE_HEADER = {
    "en":       "🩺 General Medical Advice",
    "hi":       "🩺 सामान्य चिकित्सा सलाह",
    "hinglish": "🩺 General Medical Advice",
    "mr":       "🩺 सामान्य वैद्यकीय सल्ला",
    "gu":       "🩺 ₹ ₹",
}

DISCLAIMER = {
    "en":       "⚠️ Disclaimer: These are general suggestions only, not professional medical advice. Always consult a certified doctor.",
    "hi":       "⚠️ अस्वीकरण: ये केवल सामान्य सुझाव हैं, पेशेवर चिकित्सा सलाह नहीं। हमेशा डॉक्टर से मिलें।",
    "hinglish": "⚠️ Disclaimer: Ye sirf general suggestions hain, professional medical advice nahi. Doctor se zaroor milo.",
    "mr":       "⚠️ अस्वीकरण: हे फक्त सामान्य सुझाव आहेत, व्यावसायिक वैद्यकीय सल्ला नाही. डॉक्टरांना भेटा.",
    "gu":       "⚠️ ₹ general suggestions ₹. Doctor ₹.",
}


# ===========================
# HELPERS
# ===========================

def _resolve_lang(lang) -> str:
    if isinstance(lang, dict):
        lang = lang.get("language", "en")
    mapping = {"en": "en", "hi": "hi", "hinglish": "hinglish", "mr": "mr", "gu": "gu", "others": "en"}
    return mapping.get(str(lang).lower(), "en")


def _get_remedy_in_lang(advice, lang_key):
    """Extract advice for the right language from multilingual dict or list."""
    if isinstance(advice, dict):
        return advice.get(lang_key) or advice.get("en") or []
    if isinstance(advice, list):
        return advice
    return [str(advice)]


def _get_general_advice(symptom: str, lang_key: str) -> str:
    block = GENERAL_ADVICE.get(symptom)
    if block:
        return block.get(lang_key) or block.get("en") or GENERIC_GENERAL.get(lang_key, GENERIC_GENERAL["en"])
    return GENERIC_GENERAL.get(lang_key, GENERIC_GENERAL["en"])


# ===========================
# MAIN BUILDER
# ===========================

def build_response(retrieval_result: dict, lang=None) -> dict:
    """
    Returns a dict with TWO separate response sections:
      - home_remedy_response: list of {symptom, remedy_steps}
      - general_advice_response: list of {symptom, general_advice}
      - headers, disclaimer, status
    """
    lang_key = _resolve_lang(lang or "en")

    if not retrieval_result:
        return {
            "status": "error",
            "message": FALLBACK_MESSAGE.get(lang_key, FALLBACK_MESSAGE["en"]),
            "home_remedy_response": [],
            "general_advice_response": [],
        }

    # EMERGENCY CASE
    if retrieval_result.get("status") == "emergency":
        emerg = retrieval_result.get("emergency", {})
        emerg_msg = emerg.get("message", {})
        if isinstance(emerg_msg, dict):
            msg_text = emerg_msg.get(lang_key) or emerg_msg.get("en", "")
        else:
            msg_text = str(emerg_msg)
        return {
            "status": "emergency",
            "symptom": emerg.get("symptom", ""),
            "message": msg_text,
            "home_remedy_response": [],
            "general_advice_response": [],
        }

    symptoms = retrieval_result.get("symptoms", [])
    remedies = retrieval_result.get("remedies", {})

    if not symptoms:
        return {
            "status": "ok",
            "message": FALLBACK_MESSAGE.get(lang_key, FALLBACK_MESSAGE["en"]),
            "home_remedy_response": [],
            "general_advice_response": [],
        }

    home_blocks = []
    general_blocks = []

    for symptom in symptoms:
        # --- HOME REMEDY ---
        raw_advice = remedies.get(symptom)
        if raw_advice:
            advice_list = _get_remedy_in_lang(raw_advice, lang_key)
            if not isinstance(advice_list, list):
                advice_list = [str(advice_list)]
        else:
            advice_list = [UNKNOWN_REMEDY.get(lang_key, UNKNOWN_REMEDY["en"])]

        home_blocks.append({
            "symptom": symptom,
            "remedy_steps": advice_list,
        })

        # --- GENERAL MEDICAL ADVICE ---
        general_blocks.append({
            "symptom": symptom,
            "general_advice": _get_general_advice(symptom, lang_key),
        })

    return {
        "status": "ok",
        "count": len(symptoms),
        "lang": lang_key,
        "home_remedy_header": HOME_REMEDY_HEADER.get(lang_key, HOME_REMEDY_HEADER["en"]),
        "general_advice_header": GENERAL_ADVICE_HEADER.get(lang_key, GENERAL_ADVICE_HEADER["en"]),
        "home_remedy_response": home_blocks,
        "general_advice_response": general_blocks,
        "doctor_note": DOCTOR_ADVICE.get(lang_key, DOCTOR_ADVICE["en"]),
        "disclaimer": DISCLAIMER.get(lang_key, DISCLAIMER["en"]),
    }