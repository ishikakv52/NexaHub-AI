from django.urls import path
from . import views
from .views import home
app_name = 'voice_assistant'

urlpatterns = [
    path("", home),
    path('api/process/',        views.process_input,   name='process_input'),
    path('api/save-fitness/',   views.save_fitness,    name='save_fitness'),
    path('api/qa/',             views.report_qa,       name='report_qa'),
    path('api/history/',        views.get_history,     name='get_history'),
    path('api/set-goal/',       views.set_goal,        name='set_goal'),
    path('api/tts/',            views.text_to_speech,  name='tts'),
    path('api/email/',          views.send_email_view, name='send_email'),
]