from langdetect import detect
from langdetect import DetectorFactory

DetectorFactory.seed = 0


def detect_language(text):

    try:

        if len(text.strip()) < 3:
            return "unknown"

        lang = detect(text)

        return lang

    except:

        return "unknown"