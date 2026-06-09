from django.urls import path
from .views import process_remedy, ai_chat, index

urlpatterns = [
    path("",         index,           name="remedies_index"),
    path("process/", process_remedy,  name="process_remedy"),
    path("chat/",    ai_chat,         name="ai_chat"),
]