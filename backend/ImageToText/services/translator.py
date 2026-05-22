# Fully offline translation via argostranslate
# Install: pip install argostranslate
# Download packs: python -c "
#   from argostranslate import package
#   package.update_package_index()
#   pkgs = package.get_available_packages()
#   [package.install_from_path(p.download())
#    for p in pkgs if p.from_code == 'en' or p.to_code == 'en']
# "
  
try:
    from argostranslate import translate as argo_translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False


def _get_installed_lang(code):
    """Installed language object by code, or None"""
    try:
        langs = argo_translate.get_installed_languages()
        return next((l for l in langs if l.code == code), None)
    except Exception:
        return None


def translate_text(text, target_lang='en', source_lang='auto'):
    """
    Offline translation via argostranslate.
    source_lang='auto' → langdetect se already detect ho chuka hoga views.py mein,
    isliye 'auto' aaye toh translation skip karo.
    """

    # --- Guard: empty text ---
    if not text or not text.strip():
        return {
            'translated_text': text,
            'success': False,
            'note': 'Empty text - nothing to translate'
        }

    # --- Guard: same language ---
    if source_lang == target_lang:
        return {
            'translated_text': text,
            'success': False,
            'note': 'Source and target language are the same'
        }

    # --- Guard: auto not supported ---
    if source_lang == 'auto':
        return {
            'translated_text': text,
            'success': False,
            'note': (
                'source_lang=auto is not supported by argostranslate. '
                'Pass detected language from language_detector instead.'
            )
        }

    # --- Guard: argostranslate not installed ---
    if not ARGOS_AVAILABLE:
        return {
            'translated_text': text,
            'success': False,
            'note': 'argostranslate not installed. Run: pip install argostranslate'
        }

    # --- Main translation ---
    try:
        from_lang = _get_installed_lang(source_lang)
        to_lang   = _get_installed_lang(target_lang)

        # Language pack missing
        if not from_lang or not to_lang:
            missing = []
            if not from_lang: missing.append(source_lang)
            if not to_lang:   missing.append(target_lang)
            return {
                'translated_text': text,
                'success': False,
                'note': (
                    f'Language pack not installed for: {", ".join(missing)}. '
                    f'Re-run the package download command above.'
                )
            }

        translation_obj = from_lang.get_translation(to_lang)
        if not translation_obj:
            return {
                'translated_text': text,
                'success': False,
                'note': f'No translation route found: {source_lang} → {target_lang}'
            }

        translated = translation_obj.translate(text)
        return {
            'translated_text': translated,
            'source_language': source_lang,
            'target_language': target_lang,
            'success': True,
            'note': 'Offline translation via argostranslate'
        }

    except Exception as e:
        return {
            'translated_text': text,
            'success': False,
            'note': f'Translation error: {e}'
        }