from deep_translator import GoogleTranslator


def translate_text(text, source_lang, target_lang):

    try:

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated

    except Exception as e:

        print("Translation Error:", e)

        return text