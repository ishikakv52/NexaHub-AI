from django.urls import path
from . import views

app_name = "TextToSpeech"

urlpatterns = [
    path("",           views.index,           name="index"),
    path("generate/",  views.generate_speech, name="generate"),
    path("translate/", views.translate_speech, name="translate"),
]