import re
import unicodedata

# =========================
# CLEANER (PRODUCTION)
# =========================

def clean(text: str) -> str:
    """
    Cleans multilingual medical input safely.
    Supports:
    - Hindi (Devanagari)
    - Chinese
    - Latin (English, Spanish, French, etc.)
    - Numbers
    """

    if not text:
        return ""

    # ensure string
    text = str(text)

    # lowercase
    text = text.lower()

    # normalize unicode (important for accents)
    text = unicodedata.normalize("NFKC", text)

    # remove emojis & symbols (keep letters + multilingual scripts)
    text = re.sub(
        r"[^\w\s\u0900-\u097F\u4e00-\u9fff\u00C0-\u017F]",
        " ",
        text
    )

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()