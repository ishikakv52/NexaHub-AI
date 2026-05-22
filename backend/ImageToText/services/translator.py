from deep_translator import GoogleTranslator


def translate_text(text, from_lang, to_lang):

    try:
        translated = GoogleTranslator(
            source=from_lang,
            target=to_lang
        ).translate(text)

        return translated

    except Exception as e:
        print("Translation Error:", e)
        return text