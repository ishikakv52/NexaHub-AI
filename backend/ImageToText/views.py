from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from .services.preprocess import preprocess_image
from .services.image_classifier import classify_image_content
from .services.ocr_engine import run_ocr_on_image
from .services.language_detector import detect_language
from .services.translator import translate_text

ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff'}
MAX_FILE_SIZE  = 10 * 1024 * 1024  # 10 MB


@method_decorator(csrf_exempt, name='dispatch')   # Correct CBV pattern
class ImageToTextView(View):

    def post(self, request):

        # --- Input validation ---
        if 'image' not in request.FILES:
            return JsonResponse(
                {'success': False, 'error': 'Image file chahiye'},
                status=400
            )

        uploaded = request.FILES['image']

        if uploaded.size > MAX_FILE_SIZE:
            return JsonResponse(
                {'success': False, 'error': 'File too large. Max 10MB allowed.'},
                status=400
            )

        if uploaded.content_type not in ALLOWED_TYPES:
            return JsonResponse(
                {'success': False, 'error': f'Unsupported file type: {uploaded.content_type}'},
                status=400
            )

        image_bytes  = uploaded.read()
        target_lang  = request.POST.get('translate_to', 'en')

        # --- Step 1: Classify ---
        try:
            classification = classify_image_content(image_bytes)
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Classification failed: {e}'},
                status=500
            )

        # --- Step 2: Preprocess (is_handwritten now correctly wired) ---
        try:
            versions, _ = preprocess_image(
                image_bytes,
                is_handwritten=classification['is_handwritten']  # ← THE FIX
            )
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Preprocessing failed: {e}'},
                status=500
            )

        # --- Step 3: OCR ---
        try:
            ocr  = run_ocr_on_image(versions, ocr_mode=classification['ocr_mode'])
            text = ocr['best_text']
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'OCR failed: {e}'},
                status=500
            )

        # --- Step 4: Language detect ---
        try:
            lang = detect_language(text) if text else {'language': 'unknown'}
        except Exception as e:
            lang = {'language': 'unknown', 'error': str(e)}

        # --- Step 5: Translate (optional, never crash main flow) ---
        # Step 5 mein ye change karo:
        translation = translate_text(
            text,
            target_lang=target_lang,
            source_lang=lang.get('language', 'en')  # 'auto' ki jagah detected lang pass karo
        )

        # --- Response ---
        return JsonResponse({
            'success':        True,
            'image_type':     classification['type'],
            'is_handwritten': classification['is_handwritten'],
            'extracted_text': text,
            'ocr_method':     ocr['method'],          # ← EasyOCR ya Tesseract
            'ocr_attempts':   ocr['total_attempts'],
            'ocr_confidence': _best_confidence(ocr),  # ← Average best confidence
            'language':       lang,
            'translation':    translation,
            'classifier_stats': classification['stats'],  # ← Debug ke liye
        })


def _best_confidence(ocr: dict) -> float:
    """All OCR attempts mein se best confidence nikalo"""
    results = ocr.get('all_results', [])
    if not results:
        return 0.0
    return round(max(r.get('confidence', 0) for r in results), 1)