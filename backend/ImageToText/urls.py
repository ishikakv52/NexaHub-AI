from django.urls import path
from .views import *

urlpatterns = [
    path("ocr/", ocr_view, name="ocr"),
    path("translate/", translate_view, name="translate"),  # ✅ add this line

]