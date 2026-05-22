from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

import tempfile
import os

from .services.ocr_engine import extract_text


class ImageToTextView(APIView):

    parser_classes = [MultiPartParser]

    def post(self, request):

        try:

            # ---------- GET IMAGE ----------
            image = request.FILES.get("image")

            if not image:

                return Response({
                    "success": False,
                    "message": "No image uploaded"
                }, status=400)

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

            # ---------- DELETE TEMP IMAGE ----------
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # ---------- FINAL RESPONSE ----------
            return Response({

                "success": True,

                "extracted_text":
                extracted_text

            })

        except Exception as e:

            print("ERROR:", e)

            return Response({

                "success": False,

                "error":
                str(e)

            }, status=500)