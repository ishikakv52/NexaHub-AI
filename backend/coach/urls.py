from django.urls import path
from . import views

urlpatterns = [
    path('',                  views.home,                name='home'),
    path('login/',            views.login_view,          name='login'),
    path('register/',         views.register_view,       name='register'),
    path('logout/',           views.logout_view,         name='logout'),
    path('dashboard/',        views.dashboard,           name='dashboard'),
    path('chat/',             views.text_chat,           name='text_chat'),
    path('voice/',            views.voice_chat,          name='voice_chat'),
    path('grammar/',          views.grammar_coach,       name='grammar_coach'),
    path('vocabulary/',       views.vocabulary_coach,    name='vocabulary_coach'),
    path('speaking/',         views.speaking_coach,      name='speaking_practice'),
    path('interview/',        views.interview_practice,  name='interview_practice'),
    path('translation/',      views.translation,         name='translation'),
    path('pronunciation/',    views.pronunciation_coach, name='pronunciation_coach'),
    path('challenge/',        views.daily_challenge,     name='daily_challenge'),
    # AJAX endpoints
    path('ajax/chat/',        views.ajax_chat,           name='ajax_chat'),
    path('ajax/grammar/',     views.ajax_grammar,        name='ajax_grammar'),
    path('ajax/vocabulary/',  views.ajax_vocabulary,     name='ajax_vocabulary'),
    path('ajax/speaking/',    views.ajax_speaking,       name='ajax_speaking'),
    # Speaking Coach (Premium)
    path('ajax/speaking/start/',   views.ajax_speaking_start,   name='ajax_speaking_start'),
    path('ajax/speaking/respond/', views.ajax_speaking_respond, name='ajax_speaking_respond'),
    path('ajax/speaking/report/',  views.ajax_speaking_report,  name='ajax_speaking_report'),
    path('ajax/interview/',   views.ajax_interview,      name='ajax_interview'),
    path('ajax/translate/',   views.ajax_translate,      name='ajax_translate'),
    path('ajax/pronunciation/',views.ajax_pronunciation, name='ajax_pronunciation'),
    path('ajax/challenge/',   views.ajax_challenge,      name='ajax_challenge'),
    path('ajax/save-word/',   views.ajax_save_word,      name='ajax_save_word'),
    # Grammar Engine endpoints
    path('ajax/grammar/raw/',      views.ajax_grammar_raw,      name='ajax_grammar_raw'),
    path('ajax/grammar/practice/', views.ajax_grammar_practice, name='ajax_grammar_practice'),
    path('ajax/grammar/weak/',     views.ajax_grammar_weak,     name='ajax_grammar_weak'),
    path('ajax/grammar/rules/',    views.ajax_grammar_rules,    name='ajax_grammar_rules'),
    # Interview Simulator (Premium)
    path('interview/simulator/',       views.interview_simulator,      name='interview_simulator'),
    path('ajax/interview/start/',      views.ajax_interview_start,     name='ajax_interview_start'),
    path('ajax/interview/answer/',     views.ajax_interview_answer,    name='ajax_interview_answer'),
    path('ajax/interview/report/',     views.ajax_interview_report,    name='ajax_interview_report'),
]