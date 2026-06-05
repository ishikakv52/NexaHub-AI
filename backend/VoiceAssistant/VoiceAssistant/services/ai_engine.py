"""
NEXA HUB AI Engine (DB-backed)
Session_id is passed through so HealthDataService
reads the actual user's DB data for every response.
"""

import random, datetime, re
from .intent_detector import IntentDetector
from .intent_router    import IntentRouter
from .health   import HealthDataService, get_report_context


class VoiceAssistantAI:

    def __init__(self):
        self.tasks    = []
        self.projects = []

    def detect_language(self, text):
        if re.search(r'[\u0900-\u097F]', text): return 'hi'
        if re.search(r'[\u0C00-\u0C7F]', text): return 'te'
        return 'en'

    def get_response(self, model, sub_model, user_input, context=None):
        context    = context or {}
        session_id = context.get('session_id', 'default')
        lang       = self.detect_language(user_input)
        text_l     = user_input.lower()

        if any(g in text_l for g in ['hello','hi','hey','namaste','hii']):
            return {'response': self._greeting(lang), 'type': 'normal'}

        handlers = {
            'healthcare': {
                'fitness_tracker': self._fitness,
                'home_remedies':   self._remedies,
                'workout':         self._workout,
                'diet_planner':    self._diet,
            },
            'education': {
                'english_coach':    self._english,
                'exam_preparation': self._exam,
                'task_manager':     self._tasks,
            },
            'daily_life': {
                'decoration_ideas': self._decor,
                'news':             self._news,
                'weather_alerts':   self._weather,
                'casual_talks':     self._casual,
            },
            'productivity': {
                'email_assistant':  self._email,
                'project_tracker':  self._projects,
            },
        }
        handler = handlers.get(model, {}).get(sub_model, self._default)
        return handler(user_input, context, session_id)

    def _greeting(self, lang):
        msgs = {
            'hi': "नमस्ते! मैं ARIA हूँ। आपका data save करके accurate health reports दे सकता हूँ! 💪",
            'en': "Hey! I'm NEXA — your AI health assistant. Enter your fitness data and I'll give you real insights! 🏃"
        }
        return msgs.get(lang, msgs['en'])

    # ── FITNESS TRACKER (fully DB-backed) ─────────────────────
    def _fitness(self, text, ctx, session_id):
        detector = IntentDetector()
        intent   = detector.detect(text)
        t        = text.lower()

        # Keyword priority overrides
        if 'weekly' in t and ('summary' in t or 'report' in t): intent = 'weekly_summary'
        elif 'monthly' in t and ('summary' in t or 'report' in t): intent = 'monthly_summary'
        elif ('daily' in t or 'aaj' in t) and ('summary' in t or 'report' in t): intent = 'daily_summary'

        # ── Inline goal-set command ────────────────────────────
        # "set steps goal 12000" / "set water goal 3.5"
        goal_m = re.search(r'set\s+(\w+)\s+goal\s+([\d.]+)', t)
        if goal_m:
            metric_map = {
                'steps':'steps', 'step':'steps',
                'sleep':'sleep_hours', 'water':'water_liters',
                'weight':'weight_kg', 'calorie':'calories_burned',
                'calories':'calories_burned', 'recovery':'recovery_score',
            }
            raw_m = goal_m.group(1)
            metric = metric_map.get(raw_m)
            if metric:
                try:
                    from VoiceAssistant.VoiceAssistant.db_service import set_goal
                    val = float(goal_m.group(2))
                    set_goal(session_id, metric, val)
                    return {'response': f"🎯 Goal set ho gaya!\n\n**{metric.replace('_',' ').title()}** = **{val}**\n\nAb jab bhi yeh metric check karoge, isi goal se compare hoga! 💪", 'type': 'goal_set'}
                except Exception:
                    pass

        # ── Build service with session_id ──────────────────────
        service = HealthDataService(session_id=session_id)
        router  = IntentRouter(service)

        # ── Q&A intents ──────────────────────────────────────────
        is_qa          = detector.is_qa_intent(intent)
        report_ctx     = ctx.get('report_context') or get_report_context() or {}
        has_report_ctx = bool(report_ctx)

        # Q&A condition:
        # 1. Explicitly a Q&A intent (qa_improve, qa_compare, etc.)
        # 2. Intent unknown but user has an active report context
        # 3. Any question-like text when report context exists
        is_question = any(w in text.lower() for w in [
            'kyu', 'why', 'kaise', 'how', 'kab', 'when', 'kya', 'what',
            'improve', 'better', 'compare', 'goal', 'predict', 'effect',
            'tip', 'advice', 'suggest', 'explain', 'matlab', 'wajah',
        ])

        if is_qa or (has_report_ctx and (intent == 'unknown' or is_question)):
            result = service.answer_report_question(text, report_ctx)
            result['report_context'] = report_ctx
            result['qa_enabled']     = True
            return result

        # ── Normal metric intent ───────────────────────────────
        result = router.handle(intent, text, ctx)

        if result.get('data'):
            result['report_context'] = get_report_context()
            result['qa_enabled']     = True

        return result

    # ── OTHER MODELS (unchanged) ───────────────────────────────
    def _remedies(self, text, ctx, sid):
        t = text.lower()
        remedies = {
            'cold':     "🤧 **Cold Remedies:**\n\n🍵 Ginger-honey-lemon tea (3x/day)\n🧄 Raw garlic with honey\n💨 Eucalyptus steam 10 mins\n🌶️ Turmeric milk at bedtime",
            'headache': "🤕 **Headache Relief:**\n\n🧊 Cold compress on forehead\n🌿 Peppermint oil on temples\n💧 2 glasses water immediately\n🧘 Deep breathing 5 mins",
            'cough':    "😮‍💨 **Cough Remedies:**\n\n🍯 Honey + warm water\n🧅 Onion juice + honey\n🍵 Tulsi tea + black pepper\n🧂 Saltwater gargle 3x daily",
            'fever':    "🌡️ **Fever:**\n\n💧 Drink plenty of fluids\n🧊 Cool cloth on forehead\n🌿 Tulsi + ginger kadha\n⚠️ 103°F+ → doctor!",
            'stomach':  "🫃 **Stomach Ache:**\n\n🍵 Ajwain + warm water\n🌿 Jeera water\n🫚 Hing + warm water\n🍌 Banana for upset stomach",
        }
        for k, v in remedies.items():
            if k in t: return {'response': v, 'type': 'normal'}
        return {'response': "🌿 **Home Remedies**\n\nBatao kya problem hai:\n🤧 Cold | 🤕 Headache | 😮‍💨 Cough\n🌡️ Fever | 🫃 Stomach ache", 'type': 'normal'}

    def _workout(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['beginner','start','new','shuru']):
            return {'response': "🏋️ **Beginner Plan:**\n\nMon: Push-ups 3×10 + Rows 3×12\nWed: Squats 3×15 + Lunges 3×12\nFri: Plank 3×30s + 20 min walk\n\nHydrate! 💧", 'type': 'normal'}
        if any(w in t for w in ['home','ghar','no equipment']):
            return {'response': "🏠 **Home Workout (No Equipment):**\n\n3 rounds:\n• 20 Push-ups\n• 30 Squats\n• 15 Tricep dips (chair)\n• 1 min Plank\n• 20 Glute bridges\n\nTotal: ~35 mins!", 'type': 'normal'}
        return {'response': "🏋️ **Workout Planner**\n\n🟢 Beginner / Intermediate / Advanced\n💪 Chest, Back, Legs, Core\n🏠 Home workouts | 🏃 Cardio\n\nApna fitness level batao!", 'type': 'normal'}

    def _diet(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['veg','vegetarian']):
            return {'response': "🥗 **Veg Diet (2000 cal):**\n\nBreakfast: 2 roti + paneer + milk\nLunch: Dal + rice + sabzi + curd\nEvening: Sprouts chaat\nDinner: 2 roti + dal\n\nProtein: ~65g", 'type': 'normal'}
        if any(w in t for w in ['weight loss','fat loss','patla']):
            return {'response': "📉 **Weight Loss Diet:**\n\n500 cal deficit = 0.5 kg/week\n\nMorning: Lemon water + almonds\nBreakfast: Oats / 2 eggs\nLunch: Grilled protein + salad\nDinner: Dal + vegetables (no rice)\n\n❌ Avoid: Sugar, maida, cold drinks", 'type': 'normal'}
        return {'response': "🍽️ **Diet Planner**\n\n🥗 Vegetarian | 🍗 Non-veg\n📉 Weight loss | 💪 Muscle gain\n\nApna goal batao!", 'type': 'normal'}

    def _english(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['grammar','correct','sentence']):
            return {'response': "📝 **Grammar Tips:**\n\n✅ Subject-Verb: 'He runs' not 'He run'\n✅ Present Perfect: 'I have eaten'\n✅ Articles: 'a' consonant, 'an' vowel\n\nSentence share karo — main correct karunga!", 'type': 'normal'}
        return {'response': "🗣️ **English Coach**\n\n📝 Grammar | 📚 Vocabulary\n🎤 Pronunciation | ✍️ Writing\n\nKya practice karna hai?", 'type': 'normal'}

    def _exam(self, text, ctx, sid):
        return {'response': "📚 **Exam Prep**\n\n🔢 Maths | 🔬 Science | 📖 English\n🏛️ UPSC, JEE, NEET, CAT, SSC\n\n⏱️ Pomodoro: 25 min study + 5 min break\nKaunsa subject?", 'type': 'normal'}

    def _tasks(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['add','create','new']):
            name = re.sub(r'add|create|new|task', '', text, flags=re.I).strip()
            if name:
                self.tasks.append({'task': name, 'done': False})
                return {'response': f"✅ Task added: **{name}**\n\nTotal: {len(self.tasks)}", 'type': 'normal'}
        if any(w in t for w in ['show','list','all']):
            if not self.tasks: return {'response': "📋 No tasks! Say 'Add task [name]'", 'type': 'normal'}
            return {'response': "📋 **Tasks:**\n\n" + '\n'.join([f"{'✅' if t['done'] else '⏳'} {t['task']}" for t in self.tasks]), 'type': 'normal'}
        return {'response': "📋 **Task Manager**\n\n➕ 'Add task [name]'\n📋 'Show tasks'\n✅ 'Complete task'", 'type': 'normal'}

    def _decor(self, text, ctx, sid):
        return {'response': "🏡 **Decoration Ideas**\n\n🛋️ Living Room | 🛏️ Bedroom | 🍳 Kitchen\n\n2024 trends: Biophilic, Japandi, Quiet Luxury\n\nKaunsa room?", 'type': 'normal'}

    def _news(self, text, ctx, sid):
        return {'response': "📰 **News**\n\n💻 Tech | 🏏 Sports | 🌍 World | 💰 Finance\n\nLive news: NDTV.com\n\nKoi specific topic?", 'type': 'normal'}

    def _weather(self, text, ctx, sid):
        t = text.lower()
        cities = {'mumbai': "🌤️ Mumbai: 28-32°C, Humid", 'delhi': "🌤️ Delhi: Hot summers 40°C+", 'bangalore': "🌤️ Bengaluru: Pleasant 18-28°C"}
        for c, info in cities.items():
            if c in t: return {'response': info + "\n\nmausam.imd.gov.in", 'type': 'normal'}
        return {'response': "🌤️ **Weather**\n\nApna shehar batao!\n\nReal-time: mausam.imd.gov.in", 'type': 'normal'}

    def _casual(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['joke','funny']): return {'response': random.choice(["😄 Why don't scientists trust atoms?\nBecause they make up everything!", "😂 Maine computer ko bola: aaram kar!\nUsne kaha: Windows update hona hai! 😩"]), 'type': 'normal'}
        if any(w in t for w in ['fact','amazing']): return {'response': random.choice(["🤯 Honey never spoils! 3000-year-old honey was still edible!", "🧠 Brain generates enough electricity to power an LED bulb!"]) + "\n\nAur facts? Bol dena!", 'type': 'normal'}
        return {'response': "Interesting! Aur kuch batao? 😊", 'type': 'normal'}

    def _email(self, text, ctx, sid):
        stage = ctx.get('email_stage', 'start')
        if stage == 'start' or 'email' in text.lower():
            return {'response': "📧 **Email Assistant**\n\nStep 1: Subject kya hai?", 'type': 'email_flow', 'next_stage': 'get_subject'}
        return {'response': "📧 Email ready! Dobara shuru karo: 'Write email'", 'type': 'normal'}

    def _projects(self, text, ctx, sid):
        t = text.lower()
        if any(w in t for w in ['add','new','create']):
            name = re.sub(r'add|new|create|project', '', text, flags=re.I).strip()
            if name:
                self.projects.append({'name': name, 'status': 'In Progress', 'progress': 0})
                return {'response': f"🚀 Project **{name}** created!\nStatus: In Progress | 0%", 'type': 'normal'}
        if any(w in t for w in ['show','list']):
            if not self.projects: return {'response': "📊 No projects! Say 'Add project [name]'", 'type': 'normal'}
            return {'response': "📊 **Projects:**\n\n" + '\n'.join([f"🔵 **{p['name']}** — {p['status']}" for p in self.projects]), 'type': 'normal'}
        return {'response': "📊 **Project Tracker**\n\n🚀 'Add project [name]'\n📋 'Show projects'", 'type': 'normal'}

    def _default(self, text, ctx, sid):
        return {'response': f"Samajh gaya: *\"{text}\"*\n\nSidebar se koi tool select karo ya health data enter karo! 😊", 'type': 'normal'}


_ai = VoiceAssistantAI()

def get_ai_response(model, sub_model, user_input, context=None):
    return _ai.get_response(model, sub_model, user_input, context)