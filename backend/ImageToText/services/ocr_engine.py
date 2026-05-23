import pytesseract
from PIL import Image
import numpy as np

# Windows users ye uncomment karo:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# EasyOCR - handwriting ke liye best (CPU pe bhi kaam karta hai)
try:
    import easyocr
    EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

CONFIGS = {
    'screenshot': [
        '--oem 3 --psm 6',
    ],
    # 'handwritten': [
    #     '--oem 1 --psm 6',   # LSTM only - cleaner for handwriting
    #     '--oem 1 --psm 11',  # Sparse text
    #     '--oem 1 --psm 13',  # Raw line - single line handwriting ke liye
    # ]
    'handwritten': [
    '--oem 3 --psm 7',
],
    'mixed': [
        '--oem 3 --psm 6',
        '--oem 1 --psm 6',
    ]
}


def _run_easyocr(img_array):
    """EasyOCR se text extract karo - handwriting ke liye best"""
    if not EASYOCR_AVAILABLE:
        return None, 0

    try:
        results = EASYOCR_READER.readtext(img_array, detail=1, paragraph=True)
        if not results:
            return None, 0

        lines = []
        total_conf = 0
        count = 0
        for (_, text, conf) in results:
            lines.append(text)
            total_conf += conf
            count += 1

        full_text = "\n".join(lines).strip()
        avg_conf = (total_conf / count * 100) if count else 0
        return full_text, avg_conf
    except Exception:
        return None, 0


def _run_tesseract(pil_img, configs, ocr_mode):
    """Tesseract se text extract karo"""
    results = []

    langs = ['eng']
    # Agar Hindi bhi chahiye: langs = ['eng', 'hin']

    for config in configs:
        for lang in langs:
            try:
                text = pytesseract.image_to_string(
                    pil_img, lang=lang, config=config
                ).strip()

                if len(text) < 3:
                    continue

                try:
                    data = pytesseract.image_to_data(
                        pil_img, lang=lang, config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    confs = [int(c) for c in data['conf']
                             if str(c).isdigit() and int(c) > 0]
                    avg_conf = sum(confs) / len(confs) if confs else 0
                except Exception:
                    avg_conf = 50

                results.append({
                    'version': 'tesseract',
                    'lang': lang,
                    'config': config,
                    'text': text,
                    'confidence': round(avg_conf, 1),
                    # Word count boost hataya - sirf confidence pe rank karo
                    'score': avg_conf
                })

            except Exception:
                continue

    return results


def run_ocr_on_image(preprocessed_versions, ocr_mode='mixed'):
    """
    Sabhi versions pe OCR run karo, best result lo.
    Handwritten mode mein EasyOCR ko priority milti hai.
    """
    configs = CONFIGS.get(ocr_mode, CONFIGS['mixed'])
    all_results = []
    best_text = ""
    best_score = 0

    # --- Handwritten: EasyOCR first (much better for handwriting) ---
    if ocr_mode == 'handwritten' and EASYOCR_AVAILABLE:
        # Best preprocessed version try karo - upscaled ya clahe
        priority_versions = ['upscaled_thresh', 'clahe_upscaled', 'upscaled_text', 'clahe', 'otsu']
        for vname in priority_versions:
            img_array = preprocessed_versions.get(vname)
            if img_array is None:
                continue

            text, conf = _run_easyocr(img_array)
            if text and len(text) >= 3:
                all_results.append({
                    'version': vname,
                    'lang': 'en',
                    'config': 'easyocr',
                    'text': text,
                    'confidence': round(conf, 1)
                })
                score = conf
                if score > best_score:
                    best_text = text
                    best_score = score
                break  # First good EasyOCR result lo

    # --- Tesseract fallback (ya screenshot/mixed mode) ---
    for version_name, img_array in preprocessed_versions.items():
        if img_array is None:
            continue

        pil_img = Image.fromarray(img_array)
        tess_results = _run_tesseract(pil_img, configs, ocr_mode)

        for r in tess_results:
            r['version'] = version_name
            all_results.append(r)
            if r['score'] > best_score:
                best_text = r['text']
                best_score = r['score']

    return {
        'best_text': best_text,
        'total_attempts': len(all_results),
        'all_results': all_results,
        'method': 'easyocr_primary_tesseract_fallback'
            if (ocr_mode == 'handwritten' and EASYOCR_AVAILABLE)
            else 'tesseract_only'
    }
# Existing priority_versions list update karo:
priority_versions = [
    'ink_isolated_upscaled',  # ← NEW: best for blue/black pen
    'ink_isolated',           # ← NEW
    'upscaled_padded',        # ← NEW: edge characters ke liye
    'upscaled_thresh',
    'clahe_upscaled_padded',  # ← NEW
    'clahe_upscaled',
    'upscaled_text',
    'clahe',
    'otsu',
]