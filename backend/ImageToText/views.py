from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

import tempfile
import os

from .services.ocr_engine import extract_text
from .services.language_detector import detect_language
from .services.translator import (
    translate_text
)

class ImageToTextView(APIView):

    parser_classes = [MultiPartParser]

    def post(self, request):

        try:

            image = request.FILES.get('image')

            # ---------- IMAGE CHECK ----------

            if not image:

                return Response({

                    "success": False,

                    "message": "No image uploaded"

                })

            # ---------- SAVE TEMP IMAGE ----------

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            ) as temp:

                for chunk in image.chunks():

                    temp.write(chunk)

                temp_path = temp.name

            # ---------- OCR ----------

            extracted_text = extract_text(
                temp_path
            )

            # ---------- LANGUAGE DETECTION ----------

            detected_language = detect_language(
                extracted_text
            )
            target_language = request.data.get(
            "target_language",
            "hi"
            )
            translated_text = translate_text(

            extracted_text,

            from_lang=detected_language,

            to_lang=target_language
)

            # ---------- CLEAN TEMP FILE ----------

            if os.path.exists(temp_path):

                os.remove(temp_path)

            # ---------- RESPONSE ----------

            return Response({

                "success": True,

                "detected_language":
                detected_language,

                "text_length":
                len(extracted_text),

                "extracted_text":
                extracted_text,
                "translated_text":
                translated_text

            })

        except Exception as e:

            return Response({

            "success": True,

            "detected_language":
            detected_language,

            "text_length":
            len(extracted_text),

            "extracted_text":
            extracted_text,

            "translated_text":
            translated_text

        })
