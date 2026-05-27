from django.urls import path
from . import views

urlpatterns = [
    path("",                       views.index,                name="voicetotext_index"),
    path("transcribe/audio/",      views.transcribe_audio,     name="transcribe_audio"),
    path("transcribe/video/",      views.transcribe_video,     name="transcribe_video"),
    path("transcribe/microphone/", views.transcribe_microphone,name="transcribe_microphone"),
]