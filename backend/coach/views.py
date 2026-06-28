"""
views.py — All Django Function Based Views for AI English Coach.
Uses local dataset only — NO external API key needed.
"""
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Sum

from .models import UserProfile, ChatSession, ChatMessage, DailyActivity, QuizResult, Achievement, VocabularyEntry
from . import dataset


# ── Helpers ───────────────────────────────────────────────────────
def _profile(user):
    p, _ = UserProfile.objects.get_or_create(user=user)
    return p

def _add_xp(user, xp):
    p = _profile(user)
    p.total_xp += xp
    p.level = p.get_level_from_xp()
    p.save()

def _record(user, **kw):
    today = date.today()
    act, _ = DailyActivity.objects.get_or_create(user=user, date=today)
    for f, v in kw.items():
        setattr(act, f, (getattr(act, f, 0) or 0) + v)
    act.save()
    _profile(user).update_streak()

def _history(session_id, user):
    try:
        s = ChatSession.objects.get(id=session_id, user=user)
        return [{"role": m.role, "content": m.content} for m in s.messages.all()]
    except ChatSession.DoesNotExist:
        return []

def _csrf(request):
    from django.middleware.csrf import get_token
    return get_token(request)


# ══════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════
def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    error = None
    if request.method == 'POST':
        u = authenticate(request, username=request.POST.get('username',''), password=request.POST.get('password',''))
        if u:
            login(request, u); _profile(u); return redirect('home')
        error = "Invalid username or password."
    return render(request, 'coach/login.html', {'error': error})

def register_view(request):
    if request.user.is_authenticated: return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username','').strip()
        email    = request.POST.get('email','').strip()
        pw       = request.POST.get('password','')
        pw2      = request.POST.get('password2','')
        fname    = request.POST.get('first_name','').strip()
        if pw != pw2: error = "Passwords do not match."
        elif User.objects.filter(username=username).exists(): error = "Username already taken."
        elif len(pw) < 6: error = "Password must be at least 6 characters."
        else:
            u = User.objects.create_user(username=username, email=email, password=pw, first_name=fname)
            _profile(u); login(request, u); return redirect('home')
    return render(request, 'coach/register.html', {'error': error})

def logout_view(request):
    logout(request); return redirect('login')


# ══════════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════════
def home(request):
    ctx = {}
    if request.user.is_authenticated:
        ctx['profile'] = _profile(request.user)
    return render(request, 'coach/home.html', ctx)

@login_required
def dashboard(request):
    user = request.user
    p    = _profile(user)
    today = date.today()
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        try: a = DailyActivity.objects.get(user=user, date=d); week.append({'date': d.strftime('%a'), 'xp': a.xp_earned})
        except DailyActivity.DoesNotExist: week.append({'date': d.strftime('%a'), 'xp': 0})
    totals = DailyActivity.objects.filter(user=user).aggregate(total_xp=Sum('xp_earned'), total_min=Sum('minutes_practiced'), total_msg=Sum('messages_sent'))
    return render(request, 'coach/dashboard.html', {
        'profile': p, 'week_data': json.dumps(week),
        'quizzes': QuizResult.objects.filter(user=user).order_by('-completed_at')[:10],
        'achievements': Achievement.objects.filter(user=user).order_by('-earned_at'),
        'totals': totals,
        'vocab_count': VocabularyEntry.objects.filter(user=user).count(),
    })

@login_required
def text_chat(request):
    s = ChatSession.objects.create(user=request.user, session_type='text')
    return render(request, 'coach/text_chat.html', {'session_id': s.id})

@login_required
def voice_chat(request):
    s = ChatSession.objects.create(user=request.user, session_type='voice')
    return render(request, 'coach/voice_chat.html', {'session_id': s.id})

@login_required
def grammar_coach(request):
    return render(request, 'coach/grammar_coach.html')

@login_required
def vocabulary_coach(request):
    saved = VocabularyEntry.objects.filter(user=request.user).order_by('-saved_at')[:20]
    words_preview = list(dataset.VOCABULARY.keys())[:20]
    return render(request, 'coach/vocabulary_coach.html', {'saved_words': saved, 'words_preview': words_preview})

@login_required
def speaking_practice(request):
    topics = [{'id': k, 'title': v['title'], 'prompt': v['prompt']} for k, v in dataset.SPEAKING_TOPICS.items()]
    return render(request, 'coach/speaking_practice.html', {'topics': topics})

@login_required
def interview_practice(request):
    categories = [
        {'id':'hr','title':'HR Interview','emoji':'👔','desc':'Common HR questions'},
        {'id':'behavioral','title':'Behavioral Questions','emoji':'🧠','desc':'STAR method practice'},
        {'id':'professional_communication','title':'Professional Communication','emoji':'🤝','desc':'Email, meetings, presentations'},
    ]
    return render(request, 'coach/interview_practice.html', {'categories': categories})

@login_required
def interview_simulator(request):
    """Premium AI Interview Simulator — new page."""
    return render(request, 'coach/interview_simulator.html', {
        'profile': _profile(request.user),
    })

@login_required
def translation(request):
    patterns = dataset.TRANSLATION_PATTERNS['common_hindi_english'][:6]
    mistakes  = dataset.TRANSLATION_PATTERNS['common_mistakes_indians'][:6]
    return render(request, 'coach/translation.html', {'patterns': patterns, 'mistakes': mistakes})

@login_required
def pronunciation_coach(request):
    guide     = dataset.PRONUNCIATION_GUIDE['common_indian_mistakes']
    twisters  = dataset.PRONUNCIATION_GUIDE['tongue_twisters']
    rules     = dataset.PRONUNCIATION_GUIDE['word_stress_rules']
    return render(request, 'coach/pronunciation_coach.html', {'guide': guide, 'twisters': twisters, 'rules': rules})

@login_required
def daily_challenge(request):
    today_results = QuizResult.objects.filter(user=request.user, completed_at__date=date.today())
    completed = set(r.quiz_type for r in today_results)
    return render(request, 'coach/daily_challenge.html', {'completed_types': list(completed), 'today_results': today_results})


# ══════════════════════════════════════════════════════════════════
#  AJAX ENDPOINTS (return JSON)
# ══════════════════════════════════════════════════════════════════

@login_required
@require_POST
def ajax_chat(request):
    try:
        data    = json.loads(request.body)
        msg     = data.get('message','').strip()
        sid     = data.get('session_id')
        if not msg: return JsonResponse({'error':'Empty message'}, status=400)

        try: session = ChatSession.objects.get(id=sid, user=request.user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(user=request.user, session_type='text')

        reply = dataset.get_chat_response(msg)

        ChatMessage.objects.create(session=session, role='user',      content=msg)
        ChatMessage.objects.create(session=session, role='assistant', content=reply)

        _record(request.user, messages_sent=1, xp_earned=5, minutes_practiced=1)
        _add_xp(request.user, 5)

        if ChatMessage.objects.filter(session__user=request.user).count() == 1:
            Achievement.objects.get_or_create(user=request.user, badge='first_chat')

        return JsonResponse({'reply': reply, 'session_id': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_grammar(request):
    try:
        data = json.loads(request.body)
        text = data.get('text','').strip()
        if not text: return JsonResponse({'error':'No text provided'}, status=400)
        result = dataset.get_grammar_feedback(text, user_id=request.user.id)
        _record(request.user, grammar_checks=1, xp_earned=10, minutes_practiced=2)
        _add_xp(request.user, 10)
        p = _profile(request.user); p.grammar_score = min(100, p.grammar_score+1); p.save()
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ajax_grammar_raw(request):
    """Returns raw structured grammar analysis for rich UI rendering."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        from .grammar_engine import check as engine_check
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
        result = engine_check(text, user_id=str(request.user.id))
        _record(request.user, grammar_checks=1, xp_earned=10, minutes_practiced=2)
        _add_xp(request.user, 10)
        p = _profile(request.user)
        p.grammar_score = min(100, p.grammar_score + 1)
        p.save()
        return JsonResponse({'result': result})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@csrf_exempt
def ajax_grammar_practice(request):
    """Returns practice questions for grammar practice mode."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    try:
        from .grammar_engine import get_practice
        mode     = request.GET.get('mode', 'error_correction')
        category = request.GET.get('category', None)
        n        = int(request.GET.get('n', 5))
        questions = get_practice(mode=mode, category=category, n=n)
        return JsonResponse({'questions': questions})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ajax_grammar_weak(request):
    """Returns user's weak grammar topics."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    try:
        from .grammar_engine import get_weak_topics, get_personalized_tip
        weak = get_weak_topics(str(request.user.id))
        tip  = get_personalized_tip(str(request.user.id))
        return JsonResponse({'weak_topics': weak, 'tip': tip})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ajax_grammar_rules(request):
    """Returns the grammar rule library."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    try:
        from .grammar_engine import get_rule_library
        category = request.GET.get('category', None)
        rules = get_rule_library(category)
        return JsonResponse({'rules': rules})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_vocabulary(request):
    try:
        data = json.loads(request.body)
        word = data.get('word','').strip().lower()
        if not word: return JsonResponse({'error':'No word provided'}, status=400)
        result = dataset.get_vocabulary_info(word)
        _record(request.user, vocab_lookups=1, xp_earned=8, minutes_practiced=1)
        _add_xp(request.user, 8)
        p = _profile(request.user); p.vocabulary_score = min(100, p.vocabulary_score+1); p.save()
        return JsonResponse({'result': result, 'word': word})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_save_word(request):
    try:
        data    = json.loads(request.body)
        word    = data.get('word','').strip()
        meaning = data.get('meaning','').strip()
        hindi   = data.get('hindi','').strip()
        example = data.get('example','').strip()
        if not word: return JsonResponse({'error':'No word'}, status=400)
        entry, created = VocabularyEntry.objects.get_or_create(
            user=request.user, word=word,
            defaults={'meaning':meaning,'hindi_meaning':hindi,'example':example}
        )
        count = VocabularyEntry.objects.filter(user=request.user).count()
        if count >= 100:
            Achievement.objects.get_or_create(user=request.user, badge='vocab_100')
        return JsonResponse({'saved': created, 'total': count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_speaking(request):
    try:
        data   = json.loads(request.body)
        topic  = data.get('topic','').strip()
        speech = data.get('speech','').strip()
        if not speech: return JsonResponse({'error':'No speech provided'}, status=400)
        result = dataset.get_speaking_feedback(topic, speech)
        _record(request.user, speaking_sessions=1, xp_earned=15, minutes_practiced=5)
        _add_xp(request.user, 15)
        p = _profile(request.user); p.speaking_score = min(100, p.speaking_score+2); p.save()
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_interview(request):
    try:
        data     = json.loads(request.body)
        question = data.get('question','').strip()
        answer   = data.get('answer','').strip()
        if not answer: return JsonResponse({'error':'No answer provided'}, status=400)
        result = dataset.get_interview_feedback(question, answer)
        _record(request.user, xp_earned=20, minutes_practiced=5)
        _add_xp(request.user, 20)
        p = _profile(request.user); p.interview_score = min(100, p.interview_score+3); p.save()
        count = QuizResult.objects.filter(user=request.user).count()
        if count >= 10:
            Achievement.objects.get_or_create(user=request.user, badge='interview_ace')
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_translate(request):
    try:
        data      = json.loads(request.body)
        text      = data.get('text','').strip()
        direction = data.get('direction','hi_to_en')
        if not text: return JsonResponse({'error':'No text provided'}, status=400)
        result = dataset.get_translation_help(text, direction)
        if result is None:
            result = "Translation not found in offline dataset."
        _record(request.user, xp_earned=5, minutes_practiced=1)
        _add_xp(request.user, 5)
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_pronunciation(request):
    try:
        data     = json.loads(request.body)
        sentence = data.get('sentence','').strip()
        if not sentence: return JsonResponse({'error':'No sentence provided'}, status=400)
        result = dataset.get_pronunciation_analysis(sentence)
        _record(request.user, xp_earned=10, minutes_practiced=2)
        _add_xp(request.user, 10)
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def ajax_challenge(request):
    try:
        data   = json.loads(request.body)
        action = data.get('action','generate')
        ctype  = data.get('type','grammar')
        diff   = data.get('difficulty','medium')

        if action == 'generate':
            result = dataset.get_daily_challenge(ctype, diff)
            return JsonResponse({'result': result})
        elif action == 'submit':
            score   = int(data.get('score',0))
            correct = int(data.get('correct',0))
            total   = int(data.get('total',5))
            QuizResult.objects.create(user=request.user, quiz_type=ctype, score=score, total_questions=total, correct_answers=correct)
            xp = max(score // 5, 5)
            _record(request.user, xp_earned=xp, minutes_practiced=5)
            _add_xp(request.user, xp)
            if score == 100:
                Achievement.objects.get_or_create(user=request.user, badge='perfect_score')
            p = _profile(request.user)
            if p.current_streak >= 7:
                Achievement.objects.get_or_create(user=request.user, badge='streak_7')
            if p.current_streak >= 30:
                Achievement.objects.get_or_create(user=request.user, badge='streak_30')
            return JsonResponse({'saved': True, 'xp_earned': xp})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════════
#  INTERVIEW SIMULATOR — NEW AJAX ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@csrf_exempt
def ajax_interview_start(request):
    """Start a new interview session. Returns first question."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        from .interview_engine import generate_first_question
        data = json.loads(request.body)
        interview_type   = data.get('interview_type', 'mixed')
        experience_level = data.get('experience_level', 'experienced')
        job_role         = data.get('job_role', '').strip()
        company          = data.get('company', '').strip()
        years_exp        = data.get('years_experience', '').strip()
        resume_text      = data.get('resume_text', '').strip()
        jd_text          = data.get('jd_text', '').strip()

        session = ChatSession.objects.create(user=request.user, session_type='interview')
        config  = {
            'interview_type': interview_type, 'experience_level': experience_level,
            'job_role': job_role, 'company': company,
            'years_experience': years_exp, 'resume_text': resume_text, 'jd_text': jd_text,
        }
        ChatMessage.objects.create(session=session, role='assistant',
                                   content=f'__CONFIG__:{json.dumps(config)}')

        result = generate_first_question(interview_type, job_role, experience_level,
                                         company, resume_text, jd_text)
        result['session_id']      = session.id
        result['asked_questions'] = [result['question']]

        ChatMessage.objects.create(session=session, role='assistant',
                                   content=f'__Q__:{result["question"]}')
        _record(request.user, xp_earned=5, minutes_practiced=1)
        return JsonResponse(result)
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@csrf_exempt
def ajax_interview_answer(request):
    """Submit an answer, get evaluation + next question."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        from .interview_engine import evaluate_answer, generate_next_question
        data            = json.loads(request.body)
        session_id      = data.get('session_id')
        question        = data.get('question', '').strip()
        answer          = data.get('answer', '').strip()
        question_type   = data.get('question_type', 'general')
        asked_questions = data.get('asked_questions', [])

        if not answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

        config = {}
        for msg in session.messages.all():
            if msg.content.startswith('__CONFIG__:'):
                config = json.loads(msg.content[11:])
                break

        history = [{'role': m.role, 'content': m.content}
                   for m in session.messages.all() if not m.content.startswith('__')]

        ChatMessage.objects.create(session=session, role='user', content=answer)
        history.append({'role': 'user', 'content': answer})

        evaluation = evaluate_answer(
            question, answer, question_type,
            config.get('interview_type', 'mixed'),
            config.get('experience_level', 'experienced'),
            history
        )
        next_q = generate_next_question(
            config.get('interview_type', 'mixed'),
            config.get('job_role', ''),
            config.get('experience_level', 'experienced'),
            config.get('company', ''),
            history, evaluation, asked_questions,
            config.get('resume_text', ''), config.get('jd_text', '')
        )
        if next_q:
            ChatMessage.objects.create(session=session, role='assistant',
                                       content=f'__Q__:{next_q["question"]}')

        _record(request.user, xp_earned=15, minutes_practiced=3)
        _add_xp(request.user, 15)
        p = _profile(request.user)
        p.interview_score = min(100, p.interview_score + 2)
        p.save()

        return JsonResponse({
            'evaluation':        evaluation,
            'next_question':     next_q,
            'interview_complete': next_q is None,
        })
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@csrf_exempt
def ajax_interview_report(request):
    """Generate the final interview report."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        from .interview_engine import generate_final_report
        data        = json.loads(request.body)
        session_id  = data.get('session_id')
        evaluations = data.get('evaluations', [])
        questions   = data.get('questions', [])

        config = {}
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
                for msg in session.messages.all():
                    if msg.content.startswith('__CONFIG__:'):
                        config = json.loads(msg.content[11:])
                        break
            except ChatSession.DoesNotExist:
                pass

        report = generate_final_report(
            config.get('interview_type', 'mixed'),
            config.get('job_role', ''),
            config.get('company', ''),
            config.get('experience_level', 'experienced'),
            evaluations,
            questions,
        )
        if evaluations:
            avg_score = report.get('overall_score', 5)
            QuizResult.objects.create(
                user=request.user, quiz_type='interview',
                score=int(avg_score * 10),
                total_questions=len(evaluations),
                correct_answers=len([e for e in evaluations if e.get('score', 0) >= 6])
            )
            _add_xp(request.user, 50)
            _record(request.user, xp_earned=50, minutes_practiced=len(evaluations) * 3)
            if avg_score >= 8:
                Achievement.objects.get_or_create(user=request.user, badge='interview_ace')

        return JsonResponse({'report': report})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)

# ══════════════════════════════════════════════════════════════════
#  SPEAKING COACH — Premium AI Endpoints
# ══════════════════════════════════════════════════════════════════

@login_required
def speaking_coach(request):
    """Premium AI Speaking Coach page."""
    from .speaking_engine import SPEAKING_MODES
    from .models import UserProfile
    profile = _profile(request.user)
    modes = [
        {'id': k, 'title': v['title'], 'emoji': v['emoji'],
         'desc': v['desc'], 'color': v['color'], 'difficulty': v['difficulty']}
        for k, v in SPEAKING_MODES.items()
    ]
    return render(request, 'coach/speaking_practice.html', {
        'modes': modes,
        'profile': profile,
        'username': request.user.username,
    })


@login_required
@require_POST
def ajax_speaking_start(request):
    """Start a new speaking coach session."""
    try:
        from .speaking_engine import SPEAKING_MODES, get_ai_response
        data = json.loads(request.body)
        mode = data.get('mode', 'daily_conversation')
        
        if mode not in SPEAKING_MODES:
            return JsonResponse({'error': 'Invalid mode'}, status=400)
        
        # Create a new speaking session
        session = ChatSession.objects.create(user=request.user, session_type='speaking')
        
        # Store mode in first message
        mode_config = SPEAKING_MODES[mode]
        ChatMessage.objects.create(
            session=session, role='assistant',
            content=f'__mode:{mode}__'
        )
        
        # Get opening message
        opening = get_ai_response(mode, '', [], 0)
        ChatMessage.objects.create(session=session, role='assistant', content=opening)
        
        return JsonResponse({
            'session_id': session.id,
            'opening': opening,
            'mode': mode,
            'mode_title': mode_config['title'],
            'mode_emoji': mode_config['emoji'],
            'focus_areas': mode_config.get('focus', []),
        })
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def ajax_speaking_respond(request):
    """Process a user's spoken response and return analysis + AI reply."""
    try:
        from .speaking_engine import (
            generate_full_analysis, get_ai_response, SPEAKING_MODES
        )
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_text = data.get('text', '').strip()
        session_scores = data.get('session_scores', [])  # accumulated scores from frontend
        
        if not user_text:
            return JsonResponse({'error': 'No speech provided'}, status=400)
        
        # Get session
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Get mode from session
        messages = list(session.messages.all())
        mode = 'daily_conversation'
        for m in messages:
            if m.content.startswith('__mode:'):
                mode = m.content[7:].rstrip('__')
                break
        
        # Count turns (user messages only)
        turn_number = sum(1 for m in messages if m.role == 'user')
        
        # Session issues tracking (simple in-memory approach via frontend)
        session_issues = data.get('session_issues', {"grammar": {}, "fillers": 0, "short_answers": 0})
        
        # Generate analysis
        analysis = generate_full_analysis(mode, user_text, turn_number, session_issues)
        
        # Get AI response
        history = [{"role": m.role, "content": m.content} for m in messages[-6:]]
        ai_reply = get_ai_response(mode, user_text, history, turn_number + 1)
        
        # Save messages
        ChatMessage.objects.create(session=session, role='user', content=user_text)
        ChatMessage.objects.create(session=session, role='assistant', content=ai_reply)
        
        # Award XP
        _record(request.user, speaking_sessions=1, xp_earned=12, minutes_practiced=2)
        _add_xp(request.user, 12)
        p = _profile(request.user)
        score_boost = max(1, int(analysis['scores']['overall']))
        p.speaking_score = min(100, p.speaking_score + score_boost * 0.5)
        p.save()
        
        return JsonResponse({
            'ai_reply': ai_reply,
            'analysis': analysis,
            'turn_number': turn_number + 1,
        })
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
@require_POST
def ajax_speaking_report(request):
    """Generate end-of-session report."""
    try:
        from .speaking_engine import generate_session_report
        data = json.loads(request.body)
        session_id = data.get('session_id')
        all_scores = data.get('all_scores', [])
        session_issues = data.get('session_issues', {})
        mode = data.get('mode', 'daily_conversation')
        turn_count = data.get('turn_count', 0)
        
        report = generate_session_report(mode, all_scores, session_issues, turn_count)
        
        # Save result
        if all_scores and turn_count >= 2:
            avg_score = report.get('overall_score', 5)
            QuizResult.objects.create(
                user=request.user, quiz_type='speaking',
                score=int(avg_score * 10),
                total_questions=turn_count,
                correct_answers=len([s for s in all_scores if s.get('overall', 0) >= 7])
            )
            xp = report.get('xp_earned', 30)
            _add_xp(request.user, xp)
            _record(request.user, speaking_sessions=1, xp_earned=xp, minutes_practiced=turn_count * 2)
            
            if avg_score >= 9:
                Achievement.objects.get_or_create(request.user, badge='perfect_score')
        
        return JsonResponse({'report': report})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)