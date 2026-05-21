import easyocr
import pytesseract

from PIL import Image

from .preprocess import preprocess_image

from .image_classifier import (
    is_handwritten
)

# ONLY stable EasyOCR languages
easyocr_reader = easyocr.Reader([
    'en',
    'hi'
])

# Mac Tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r'/opt/homebrew/bin/tesseract'
)


def extract_text(image_path):

    # ---------- PREPROCESS ----------
    processed_image = preprocess_image(
        image_path
    )

    # ---------- HANDWRITTEN CHECK ----------
    handwritten = is_handwritten(
        processed_image
    )

    extracted_text = ""

    try:

        # =================================================
        # HANDWRITTEN → EASYOCR
        # =================================================

        if handwritten:

            result = easyocr_reader.readtext(
                processed_image
            )

            easy_text = " ".join([
                item[1]
                for item in result
            ])

            extracted_text = easy_text

        # =================================================
        # PRINTED → TRY EASYOCR FIRST
        # =================================================

        else:

            result = easyocr_reader.readtext(
                processed_image
            )

            easy_text = " ".join([
                item[1]
                for item in result
            ])

            # If EasyOCR gives good output
            if len(easy_text.strip()) > 5:

                extracted_text = easy_text

            # Otherwise fallback to Tesseract
            else:

                extracted_text = (
                    pytesseract.image_to_string(
                        Image.open(processed_image),

                        lang=(
                            'eng+hin+ben+tam+tel+'
                            'kan+mal+guj+pan+'
                            'mar+urd+san+ori'
                        )
                    )
                )

    except Exception as e:

        print(
            "OCR Error:",
            e
        )

    # ---------- CLEAN DUPLICATES ----------

    lines = extracted_text.splitlines()

    cleaned_lines = []

    for line in lines:

        cleaned = line.strip()

        if cleaned and cleaned not in cleaned_lines:

            cleaned_lines.append(cleaned)

    final_text = "\n".join(cleaned_lines)

    return final_text