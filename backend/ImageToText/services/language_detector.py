from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

def detect_language(text):

    text = text.strip()

    if len(text) < 5:
        return "unknown"

    try:
        lang = detect(text)

        # force normalization
        if lang not in ["en", "hi"]:
            return "en"

        return lang

    except:
        return "en"