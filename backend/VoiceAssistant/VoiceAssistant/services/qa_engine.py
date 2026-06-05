"""
NEXA HUB — QA Engine (Properly Fixed)
======================================

Dataset ka SAHI use:
  - 10,223 utterances → LogisticRegression train → METRIC intent detect
    (steps_today, sleep_duration, water_intake, etc.)

Q&A type alag se detect hota hai keyword rules se:
  - "improve", "tips"  → improve
  - "compare", "trend" → compare
  - "goal", "kab"      → goal
  - "kyu", "explain"   → explain
  - "effect", "impact" → impact
  - "predict"          → predict

Phir in dono ko combine karke personalized DB response banta hai.
"""

import os, json, glob, re, datetime, pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'VoiceAssistant', 'datasets',
                           'healthcare', 'fitness_tracker')
MODEL_PATH  = os.path.join(BASE_DIR, 'VoiceAssistant', 'intent_model.pkl')


# ═════════════════════════════════════════════════════════════
class QAEngine:

    def __init__(self):
        self.pipeline = None
        self.encoder  = LabelEncoder()
        self.ready    = False
        self._load_or_train()

    # ── Load saved model OR train fresh from dataset ──────────
    def _load_or_train(self):
        # Try loading saved model first
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    saved = pickle.load(f)
                if isinstance(saved, tuple) and len(saved) >= 2:
                    self.pipeline, self.encoder = saved[0], saved[1]
                    self.ready = True
                    print(f"[QAEngine] Loaded model: {MODEL_PATH}")
                    return
            except Exception as e:
                print(f"[QAEngine] Load failed: {e}, retraining...")

        # Train from dataset
        self._train_from_dataset()

    def _train_from_dataset(self):
        texts, labels = [], []

        # Load all JSON files from dataset
        pattern = os.path.join(DATASET_DIR, '*.json')
        files   = [f for f in glob.glob(pattern) if '__MACOSX' not in f]

        for fpath in sorted(files):
            try:
                items = json.load(open(fpath, encoding='utf-8'))
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    utt    = (item.get('utterance') or item.get('text') or
                              item.get('question') or '')
                    intent = (item.get('intent') or item.get('label') or '')
                    if utt and intent:
                        # Clean trailing difficulty labels
                        utt = re.sub(r'\s+(simple|medium|complex)\s*$',
                                     '', utt.strip(), flags=re.I)
                        texts.append(utt.lower())
                        labels.append(intent.strip().lower())
            except Exception:
                pass

        if len(texts) < 10:
            print("[QAEngine] Not enough data to train!")
            return

        # Train LogisticRegression — much better than cosine similarity
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                sublinear_tf=True,
                min_df=1,
                strip_accents='unicode',
                analyzer='word',
            )),
            ('clf', LogisticRegression(
                max_iter=500,
                C=5.0,
                solver='lbfgs',
                multi_class='auto',
            ))
        ])

        encoded = self.encoder.fit_transform(labels)
        self.pipeline.fit(texts, encoded)
        self.ready = True

        # Save for next time
        try:
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump((self.pipeline, self.encoder, True), f)
        except Exception:
            pass

        print(f"[QAEngine] Trained on {len(texts)} utterances, "
              f"{len(set(labels))} intents")

    # ── Detect METRIC intent from question ────────────────────
    def detect_metric_intent(self, question: str) -> dict:
        """
        Uses trained LogisticRegression to detect which metric
        the user is asking about.
        Returns: {intent, confidence}
        """
        if not self.ready:
            return {'intent': 'unknown', 'confidence': 0.0}

        q = question.lower()
        try:
            encoded    = self.pipeline.predict([q])[0]
            intent     = self.encoder.inverse_transform([encoded])[0]
            probs      = self.pipeline.predict_proba([q])[0]
            confidence = float(probs.max())
            return {'intent': intent, 'confidence': round(confidence, 3)}
        except Exception:
            return {'intent': 'unknown', 'confidence': 0.0}

    # ── Detect Q&A TYPE from question ─────────────────────────
    @staticmethod
    def detect_qa_type(question: str) -> str:
        """
        Pure keyword rules — detects WHAT the user wants to know.
        This is separate from WHICH metric they're asking about.
        """
        q = question.lower()

        if any(w in q for w in [
            'improve', 'kaise badhaye', 'better', 'tips', 'advice',
            'suggest', 'kya karu', 'behtar', 'increase', 'boost',
            'kaise sudhar', 'kaise improve', 'help me improve',
            'improvement', 'best way', 'kaise bana'
        ]):
            return 'improve'

        if any(w in q for w in [
            'compare', 'last week', 'yesterday', 'pichle', 'pehle',
            'difference', 'change hua', 'kitna badla', 'trend',
            'before', 'previously', 'vs', 'versus', 'aur pehle'
        ]):
            return 'compare'

        if any(w in q for w in [
            'goal kab', 'target kab', 'kab milega', 'kab achieve',
            'kab hoga', 'kab tak', 'kab poora', 'goal complete',
            'goal reach', 'target reach', 'achieve hoga',
            'kitne din', 'kitna time', 'deadline'
        ]):
            return 'goal'

        if any(w in q for w in [
            'kyu', 'why', 'reason', 'cause', 'wajah', 'matlab',
            'explain', 'samjhao', 'what is', 'kya hota', 'define',
            'iska matlab', 'kya hai yeh', 'describe', 'batao kya'
        ]):
            return 'explain'

        if any(w in q for w in [
            'effect', 'impact', 'health', 'body', 'kya hoga',
            'problem', 'risk', 'nuksan', 'consequence', 'affect karta',
            'body pe kya', 'sehat pe', 'dangerous', 'harmful'
        ]):
            return 'impact'

        if any(w in q for w in [
            'predict', 'forecast', 'next week', 'agle hafte',
            'future', 'kal ka', 'aage kya', 'projection',
            'estimate', 'prediction', 'trend kya hoga'
        ]):
            return 'predict'

        if any(w in q for w in [
            'kam', 'low', 'less', 'chhota', 'insufficient',
            'nahi hai', 'nahi hua', 'bahut kam'
        ]):
            return 'low'

        if any(w in q for w in [
            'zyada', 'high', 'jyada', 'bahut zyada', 'too much',
            'exceeded', 'above'
        ]):
            return 'high'

        return 'general'

    # ═══════════════════════════════════════════════════════════
    # MAIN METHOD — called from health.py
    # Takes: question + user's real DB data → personalized response
    # ═══════════════════════════════════════════════════════════
    def answer(self, question: str, user_data: dict,
               report_context: dict = None, goals: dict = None) -> str:
        """
        1. Detect METRIC intent (from ML model trained on 10K+ dataset)
        2. Detect Q&A type (from keywords)
        3. Build personalized response with user's real numbers
        """
        goals       = goals or {}
        report_type = (report_context or {}).get('type', 'unknown')
        report_data = (report_context or {}).get('data', {})

        # Merge report data with live DB data
        merged = {**report_data}
        for k, v in user_data.items():
            if v is not None:
                merged[k] = v

        # Step 1: Detect metric from ML model
        ml_result  = self.detect_metric_intent(question)
        ml_intent  = ml_result['intent']
        ml_conf    = ml_result['confidence']

        # Use report_type if ML confidence is low
        metric_intent = ml_intent if ml_conf >= 0.35 else report_type

        # Step 2: Detect Q&A type from keywords
        qa_type = self.detect_qa_type(question)

        # Step 3: Build response
        return self._build(metric_intent, qa_type, merged, goals, question)

    # ── Response builder ──────────────────────────────────────
    def _build(self, intent: str, qa_type: str,
               data: dict, goals: dict, question: str) -> str:

        # Map intent to builder
        builders = {
            'steps_today':        self._steps,
            'steps_weekly':       self._steps_weekly,
            'sleep_duration':     self._sleep,
            'sleep_score':        self._sleep,
            'deep_sleep':         self._deep_sleep,
            'rem_sleep':          self._rem_sleep,
            'water_intake':       self._water,
            'water_goal':         self._water,
            'calories_today':     self._calories,
            'calories_weekly':    self._calories,
            'heart_rate_current': self._heart,
            'heart_rate_average': self._heart,
            'heart_rate_zone':    self._heart,
            'weight_current':     self._weight,
            'weight_progress':    self._weight,
            'bmi_check':          self._weight,
            'stress_level':       self._stress,
            'recovery_score':     self._recovery,
            'daily_summary':      self._summary,
            'weekly_summary':     self._summary,
            'monthly_summary':    self._summary,
            'distance_today':     self._distance,
            'goal_progress':      self._goal_progress,
        }

        fn = builders.get(intent, self._generic)
        return fn(qa_type, data, goals, question)

    # ── Helper: safely get value ──────────────────────────────
    @staticmethod
    def _v(key, data, default='N/A', unit=''):
        val = data.get(key)
        if val is None:
            return default
        if isinstance(val, float):
            val = round(val, 1)
        return f"{val}{unit}"

    # ── STEPS ─────────────────────────────────────────────────
    def _steps(self, qt, d, goals, q):
        steps = d.get('steps')
        if steps is None:
            return "Steps data nahi mila. Pehle form mein steps enter karo! 🚶"

        goal = goals.get('steps', 10000)
        pct  = round((steps / goal) * 100)
        gap  = max(0, goal - steps)
        dist = d.get('distance_km') or round(steps * 0.00076, 2)
        cal  = d.get('calories_burned') or round(steps * 0.04)

        if qt == 'improve':
            mins = round(gap / 100)
            return (
                f"🚶 **{steps:,} steps — Improvement Tips:**\n\n"
                f"Goal: {goal:,} | Progress: {pct}% | Baki: {gap:,} steps\n\n"
                f"Tumhare liye specific plan:\n"
                f"• {f'Sirf {mins} mins walk aur karo — goal complete!' if gap > 0 else 'Goal already complete!'}\n"
                f"• Lunch break: 15 min walk = ~1500 steps\n"
                f"• Phone calls pe walk karo\n"
                f"• Har lift ki jagah stairs use karo"
            )
        if qt == 'impact':
            return (
                f"❤️ **{steps:,} steps ka health impact:**\n\n"
                f"Distance: {dist} km | Cal burned: ~{cal} kcal\n\n"
                + ("✅ Active day! Heart health improve ho rahi hai\n✅ Blood sugar control better\n✅ Metabolism active"
                   if steps >= 7500 else
                   "⚠️ Low activity aaj\n⚠️ Sedentary lifestyle se long-term: diabetes, heart disease risk\n💡 Kal se consistency rakho!")
            )
        if qt == 'goal':
            eta_days = round(gap / max(steps, 1) * 1) if gap > 0 else 0
            return (
                f"🎯 **Steps Goal:**\n\nAaj: {steps:,} / Goal: {goal:,} ({pct}%)\n"
                f"{'✅ Goal complete!' if gap == 0 else f'Baki: {gap:,} steps (~{round(gap/100)} min walk)'}\n\n"
                f"Goal change karne ke liye: **'Set steps goal 12000'**"
            )
        if qt == 'explain':
            return (
                f"📚 **Steps tracking kyu?**\n\n"
                f"Tumhare {steps:,} steps = {dist} km = ~{cal} kcal burned\n\n"
                f"10,000 steps/day science:\n"
                f"• ~400-500 kcal burn\n"
                f"• 30% cardiovascular risk reduce\n"
                f"• Blood pressure naturally control\n"
                f"• Mental health boost (endorphins)\n\n"
                f"{'Tumhara {pct}% = good effort! 💪' if pct >= 70 else 'Thoda aur — consistency most important!'}"
            )
        if qt == 'compare':
            return f"📊 Steps comparison ke liye 7 days data chahiye. Roz log karo aur kal accurate comparison milega!"
        return (
            f"🚶 **Steps: {steps:,}** ({pct}% of {goal:,} goal)\n"
            f"Distance: {dist} km | Cal: ~{cal} kcal\n"
            f"{'🏆 Goal complete!' if pct >= 100 else f'💪 {gap:,} more steps needed!'}"
        )

    def _steps_weekly(self, qt, d, goals, q):
        avg = d.get('avg_steps', 0) or d.get('average', 0)
        total = d.get('total_steps', 0) or d.get('total', 0)
        best  = d.get('best_day', 'N/A')
        cons  = d.get('consistency', 0)
        if qt == 'improve':
            g = goals.get('steps', 10000)
            return (
                f"📊 **Weekly avg {avg:,} steps — Improve kaise kare:**\n\n"
                f"Daily goal: {g:,} | Tumhara avg: {avg:,} ({round(avg/g*100) if g else 0}%)\n\n"
                f"• Best day tha: {best} — wahi routine roz follow karo\n"
                f"• Consistency: {cons}% — roz log karo\n"
                f"• Target: 7 din mein 70,000+ steps = 10k/day average"
            )
        return (
            f"📊 **Weekly Steps:**\nAvg: {avg:,}/day | Total: {total:,} | Best: {best}\n"
            f"Consistency: {cons}% {'✅' if cons >= 80 else '⚠️ Improve karo!'}"
        )

    # ── SLEEP ─────────────────────────────────────────────────
    def _sleep(self, qt, d, goals, q):
        hrs  = d.get('sleep_hours')
        if hrs is None:
            return "Sleep data nahi mila. Form mein sleep hours fill karo! 😴"
        goal = goals.get('sleep_hours', 8.0)
        debt = round(goal - hrs, 1)
        qual = d.get('sleep_quality') or ('Good' if hrs >= 7 else 'Fair')

        if qt == 'improve':
            return (
                f"😴 **{hrs} hrs sleep → {goal} hrs goal ({debt} hrs ki kami):**\n\n"
                f"Tumhare liye plan:\n"
                f"• Aaj **{round(debt*60)} mins pehle** soyo\n"
                f"• Screen off: sone se **1 hour pehle**\n"
                f"• Room temp: 18-20°C optimal\n"
                f"• Caffeine: **6 PM ke baad avoid** karo\n"
                + ("• Magnesium supplement consider karo (doctor se poochho)\n" if hrs < 5 else "")
                + f"\n💡 3 consecutive nights {goal} hrs = habit banti hai!"
            )
        if qt == 'impact':
            return (
                f"🧠 **{hrs} hrs sleep ka body impact:**\n\n"
                + ("✅ REM cycles complete\n✅ Memory & focus sharp\n✅ Hormones balanced\n✅ Immune system strong"
                   if hrs >= 7 else
                   f"⚠️ {debt} hrs short sleep:\n"
                   f"• Ghrelin (hunger hormone) badh jaata hai → cravings increase\n"
                   f"• Cortisol high → belly fat storage\n"
                   f"• Focus {round(debt*15)}% slower\n"
                   f"• Mood: irritable")
            )
        if qt == 'goal':
            mins_early = round(debt * 60) if debt > 0 else 0
            return (
                f"🎯 **Sleep Goal:** {hrs} hrs aaj / {goal} hrs target\n\n"
                f"{'✅ Goal met!' if hrs >= goal else f'Aaj {mins_early} mins pehle soyo → goal achieve hoga!'}\n"
                f"Quality: **{qual}**\n\nChange: **'Set sleep goal 8'**"
            )
        if qt == 'explain':
            return (
                f"📚 **{hrs} hrs sleep — stages breakdown:**\n\n"
                f"• Light sleep: ~{round(hrs*0.5,1)} hrs (50%)\n"
                f"• Deep sleep: ~{round(hrs*0.22,1)} hrs (22%) ← muscle repair\n"
                f"• REM sleep: ~{round(hrs*0.20,1)} hrs (20%) ← memory, mood\n\n"
                f"WHO recommendation: **7-9 hrs** for adults\n"
                f"{'✅ Tumhara pattern optimal hai!' if hrs >= 7 else '⚠️ Below recommended — health impact dekh rahe hain'}"
            )
        return (
            f"😴 **Sleep: {hrs} hrs** (Quality: {qual})\n"
            f"Goal: {goal} hrs {'✅' if hrs >= goal else f'| {debt} hrs ki kami'}\n"
            f"{'Perfect recovery!' if hrs >= 8 else 'Kal thodi jaldi soyo!'}"
        )

    def _deep_sleep(self, qt, d, goals, q):
        total = d.get('sleep_hours', 0) or 0
        deep  = d.get('deep_sleep_hours') or round(total * 0.22, 1)
        if qt == 'improve':
            return (
                f"🌙 **Deep sleep {deep} hrs improve karne ke tips:**\n\n"
                f"• Exercise karo — aerobic activity deep sleep badhata hai\n"
                f"• Alcohol avoid karo — deep sleep disrupt karta hai\n"
                f"• Consistent sleep schedule follow karo\n"
                f"• Magnesium-rich foods: nuts, seeds, dark chocolate"
            )
        if qt == 'explain':
            return (
                f"📚 **Deep sleep (Stage N3) kya hota hai?**\n\n"
                f"Tumhara deep sleep: {deep} hrs (~22% of {total} hrs)\n\n"
                f"Deep sleep mein:\n"
                f"• Growth hormone release → muscle repair\n"
                f"• Brain waste products clear hote hain\n"
                f"• Immune system strengthen hota hai\n"
                f"• Target: 1.5-2 hrs (20-25%)\n\n"
                f"{'✅ Good deep sleep!' if deep >= 1.5 else '⚠️ Improve karo!'}"
            )
        return f"🌙 **Deep Sleep: {deep} hrs** (target: 1.5-2 hrs)\n{'✅ Good!' if deep >= 1.5 else '⚠️ Kam hai — consistent schedule rakho!'}"

    def _rem_sleep(self, qt, d, goals, q):
        total = d.get('sleep_hours', 0) or 0
        rem   = d.get('rem_sleep_hours') or round(total * 0.20, 1)
        return (
            f"🌙 **REM Sleep: {rem} hrs**\n\n"
            f"REM mein: dreams, emotional processing, memory formation\n"
            f"Target: 1.5-2 hrs\n"
            f"{'✅ Good REM!' if rem >= 1.5 else '⚠️ REM low — consistent 7+ hrs sleep se improve hoga'}"
        )

    # ── WATER ─────────────────────────────────────────────────
    def _water(self, qt, d, goals, q):
        ltrs = d.get('water_liters')
        if ltrs is None:
            return "Water data nahi mila! Form mein fill karo 💧"
        goal = goals.get('water_liters', 3.0)
        pct  = round((ltrs / goal) * 100)
        left = round(goal - ltrs, 1)
        glasses_left = max(0, int(left * 4))

        if qt == 'improve':
            return (
                f"💧 **{ltrs} L → {goal} L goal — Hydration tips:**\n\n"
                f"Abhi {left} L ({glasses_left} glasses) aur chahiye\n\n"
                f"• Subah uthke: **2 glasses** immediately\n"
                f"• Har meal se pehle: **1 glass**\n"
                f"• Har ghante: **1 glass** (alarm set karo)\n"
                f"• Lemon ya cucumber infused water try karo\n\n"
                f"💡 Body weight × 0.033 = tumhara ideal daily intake"
            )
        if qt == 'impact':
            return (
                f"💧 **{ltrs} L water — Health impact:**\n\n"
                + ("✅ Well hydrated! Kidney, skin, digestion sab optimal\n✅ Energy levels stable\n✅ Metabolism running efficiently"
                   if pct >= 80 else
                   f"⚠️ Dehydration at {pct}% target:\n"
                   f"• Brain performance {round((100-pct)*0.3)}% slower\n"
                   f"• Kidney filtration stressed\n"
                   f"• Headache & fatigue risk high\n"
                   f"• Metabolism slow ho raha hai")
            )
        if qt == 'goal':
            return (
                f"🎯 **Water Goal:** {ltrs} L / {goal} L ({pct}%)\n\n"
                f"{'🎉 Hydration complete!' if pct >= 100 else f'Baki: {left} L = {glasses_left} glasses'}\n"
                f"Goal change: **'Set water goal 3.5'**"
            )
        return (
            f"💧 **Water: {ltrs} L** ({pct}% of {goal} L goal)\n"
            f"{'✅ Hydrated!' if pct >= 100 else f'⚠️ {left} L ({glasses_left} glasses) aur chahiye!'}"
        )

    # ── CALORIES ──────────────────────────────────────────────
    def _calories(self, qt, d, goals, q):
        burned   = d.get('calories_burned')
        consumed = d.get('calories_consumed')
        goal_b   = goals.get('calories_burned', 500)
        if burned is None and consumed is None:
            return "Calorie data nahi mila! 🔥"
        deficit = (consumed - burned) if (consumed and burned) else None

        if qt == 'improve':
            return (
                f"🔥 **Calorie optimization:**\n\n"
                + (f"Burned: {burned} kcal (goal: {goal_b})\n" if burned else "")
                + (f"Consumed: {consumed} kcal\n" if consumed else "")
                + (f"Net: {'surplus' if deficit and deficit > 0 else 'deficit'} {abs(deficit) if deficit else '?'} kcal\n\n" if deficit else "\n")
                + f"• {'✅ Calorie goal met!' if burned and burned >= goal_b else f'{goal_b - (burned or 0)} kcal aur burn karo — 30 min walk se!'}\n"
                f"• Protein 30% intake → satiety badhti hai\n"
                f"• Liquid calories (juice, cola) avoid karo"
            )
        if qt == 'explain':
            return (
                f"📚 **Calorie deficit kya hota hai?**\n\n"
                f"Tumhara: Burned {burned or '?'} | Consumed {consumed or '?'}\n\n"
                f"500 kcal deficit/day = 0.5 kg/week weight loss\n"
                f"1000 kcal deficit = 1 kg/week (maximum safe)\n"
                f"7,700 kcal = 1 kg body fat\n\n"
                f"{'✅ Weight loss trajectory!' if deficit and deficit < 0 else '📊 Maintain mode hai abhi'}"
            )
        return (
            f"🔥 **Calories:**\n"
            + (f"Burned: {burned} kcal | " if burned else "")
            + (f"Consumed: {consumed} kcal\n" if consumed else "\n")
            + (f"Net: {'surplus' if deficit and deficit > 0 else 'deficit'} {abs(deficit) if deficit else '?'} kcal" if deficit else "")
        )

    # ── HEART RATE ────────────────────────────────────────────
    def _heart(self, qt, d, goals, q):
        bpm = d.get('heart_rate_resting') or d.get('heart_rate_avg')
        if not bpm:
            return "Heart rate data nahi mila! ❤️"
        status = 'Normal' if 60 <= bpm <= 100 else ('Athletic/Low' if bpm < 60 else 'High ⚠️')
        pct_max = round((bpm / 190) * 100)
        zone = ('Rest' if pct_max < 50 else 'Fat Burn' if pct_max < 70
                else 'Cardio' if pct_max < 85 else 'Peak')
        if qt == 'improve':
            return (
                f"❤️ **HR {bpm} BPM improve karne ke tips:**\n\n"
                f"{'✅ Already excellent! Athletes: 40-60 BPM' if bpm <= 65 else 'Lower resting HR = better cardiovascular fitness'}\n\n"
                f"• Zone 2 cardio (60-70% max HR): 3x/week, 30 mins\n"
                f"• Consistent sleep: {goals.get('sleep_hours', 8)} hrs target\n"
                f"• Stress kam karo — high stress = elevated HR\n"
                f"• Hydration: {goals.get('water_liters', 3)} L/day"
            )
        if qt == 'explain':
            return (
                f"📚 **Heart Rate Zones ({bpm} BPM):**\n\n"
                f"Tumhara current zone: **{zone}** ({pct_max}% max HR)\n\n"
                f"Zone 1 (50-60%): Recovery\n"
                f"Zone 2 (60-70%): Fat Burn ← best for fat loss!\n"
                f"Zone 3 (70-85%): Cardio fitness\n"
                f"Zone 4 (85%+): Peak performance\n\n"
                f"Max HR estimate: 190 BPM (formula: 220 - 30 age)"
            )
        if qt in ('low', 'general'):
            return (
                f"❤️ **HR: {bpm} BPM ({status})**\n"
                f"Zone: {zone} ({pct_max}% max HR)\n\n"
                f"{'✅ Healthy!' if 60 <= bpm <= 100 else '⚠️ Unusual — doctor se consult karo!'}"
            )
        return f"❤️ HR: {bpm} BPM ({status}) | Zone: {zone}"

    # ── WEIGHT ────────────────────────────────────────────────
    def _weight(self, qt, d, goals, q):
        w   = d.get('weight_kg')
        bmi = d.get('bmi')
        cat = d.get('bmi_category', '')
        h   = d.get('height_cm')
        if not w:
            return "Weight data nahi mila! ⚖️"
        goal_w = goals.get('weight_kg', w)
        diff   = round(w - goal_w, 1)
        weeks  = round(abs(diff) * 2)

        if qt == 'improve':
            return (
                f"⚖️ **{w} kg → {goal_w} kg goal — Plan:**\n\n"
                f"{'✅ Goal already achieved!' if diff <= 0 else f'Difference: {diff} kg ({weeks} weeks at 0.5kg/week)'}\n\n"
                f"• Daily calorie deficit: ~500 kcal\n"
                f"• Steps: {goals.get('steps',10000):,}/day (aaj: {d.get('steps','?')})\n"
                f"• Sleep: {d.get('sleep_hours','?')} hrs → 7+ hrs for leptin balance\n"
                f"• Water: {d.get('water_liters','?')} L → {goals.get('water_liters',3)} L goal"
            )
        if qt == 'goal':
            target_date = (datetime.date.today() + datetime.timedelta(weeks=weeks)).strftime('%d %b %Y')
            return (
                f"🎯 **Weight Goal:** {w} kg → {goal_w} kg\n\n"
                f"{'🎉 Achieved!' if diff <= 0 else f'Baki: {abs(diff)} kg'}\n"
                f"{'At 0.5kg/week → **' + target_date + '** tak ho jayega!' if weeks > 0 else ''}\n\n"
                f"BMI: {bmi} ({cat})\nChange: **'Set weight goal 65'**"
            )
        if qt == 'explain':
            return (
                f"📚 **BMI {bmi} ({cat}) explained:**\n\n"
                f"Weight: {w} kg" + (f" | Height: {h} cm" if h else "") + f"\n\n"
                f"BMI ranges:\n• <18.5: Underweight\n• 18.5-24.9: Normal ✅\n"
                f"• 25-29.9: Overweight\n• ≥30: Obese\n\n"
                f"{'✅ Normal range mein ho!' if cat == 'Normal' else f'{cat} category — lifestyle changes helpful honge'}"
            )
        return f"⚖️ **Weight: {w} kg** | BMI: {bmi} ({cat})\nGoal: {goal_w} kg → {'✅ Done!' if diff <= 0 else f'{abs(diff)} kg remaining ({weeks} weeks)'}"

    # ── STRESS ────────────────────────────────────────────────
    def _stress(self, qt, d, goals, q):
        score = d.get('stress_score')
        if score is None:
            return "Stress data nahi mila! 🧠"
        level = ('Low' if score < 30 else 'Moderate' if score < 55
                 else 'High' if score < 75 else 'Very High')
        emoji = {'Low':'😊','Moderate':'😐','High':'😰','Very High':'🆘'}[level]

        if qt == 'improve':
            return (
                f"🧠 **Stress {score}/100 ({level}) — Reduction plan:**\n\n"
                f"• 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s — roz {3 if score >= 55 else 1}x\n"
                f"• Walk {round(max(10, score//5))} mins bahar — cortisol reducer\n"
                f"• Sleep: {d.get('sleep_hours','?')} hrs → 7+ hrs = natural stress buffer\n"
                f"• Journal likhna: 5 min daily\n"
                + ("• Urgent: professional support consider karo ❤️" if score >= 75 else "")
            )
        if qt == 'impact':
            return (
                f"🧠 **Stress {score}/100 — Body impact:**\n\n"
                + ("✅ Stress managed! Cortisol balanced, recovery optimal" if score < 40 else
                   f"⚠️ Score {score}:\n"
                   f"• Cortisol high → belly fat storage\n"
                   f"• Recovery {round(score*0.4)}% slower\n"
                   f"• Sleep REM disrupted\n"
                   f"• Appetite: more cravings")
            )
        return f"🧠 **Stress: {emoji} {level} ({score}/100)**\n{'✅ Managed!' if score < 40 else '⚠️ High — immediate action lo!'}"

    # ── RECOVERY ──────────────────────────────────────────────
    def _recovery(self, qt, d, goals, q):
        score = d.get('recovery_score')
        if score is None:
            return "Recovery data nahi mila! 🔋"
        grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 55 else 'D'
        workout = ('Full intense workout ✅' if score >= 80
                   else 'Moderate workout 💛' if score >= 60 else 'Rest/light stretching ⚠️')
        if qt == 'improve':
            sleep = d.get('sleep_hours', '?')
            return (
                f"🔋 **Recovery {score}/100 ({grade}) — Improve karo:**\n\n"
                f"Tumhara sleep: {sleep} hrs | Stress: {d.get('stress_score','?')}/100\n\n"
                f"• {'Sleep ' + str(round(max(0, 8-(sleep if isinstance(sleep,(int,float)) else 7)),1)) + ' hrs aur — biggest recovery booster' if isinstance(sleep,(int,float)) and sleep < 8 else 'Sleep good hai!'}\n"
                f"• Post-workout: 20g protein within 30 mins\n"
                f"• Foam rolling / stretching: 10 mins daily\n"
                f"• Cold shower 60 sec — proven recovery boost"
            )
        if qt in ('low', 'general'):
            return (
                f"🔋 **Recovery: {score}/100 ({grade})**\n\n"
                f"Aaj recommendation: **{workout}**\n\n"
                f"Key factors: Sleep {d.get('sleep_hours','?')}h | Stress {d.get('stress_score','?')}/100"
            )
        return f"🔋 Recovery: {score}/100 ({grade}) — {workout}"

    # ── SUMMARY ───────────────────────────────────────────────
    def _summary(self, qt, d, goals, q):
        score = d.get('overall_score', 0)
        date  = d.get('date', str(datetime.date.today()))

        if qt == 'improve':
            metrics = {}
            if d.get('steps'):    metrics['Steps']    = round(d['steps'] / goals.get('steps',10000) * 100)
            if d.get('sleep_hours'): metrics['Sleep'] = round(d['sleep_hours'] / goals.get('sleep_hours',8) * 100)
            if d.get('water_liters'): metrics['Water']= round(d['water_liters'] / goals.get('water_liters',3) * 100)
            if metrics:
                weakest = min(metrics, key=metrics.get)
                return (
                    f"📊 **Score {score}/100 → Improve kaise kare:**\n\n"
                    f"Sabse kamzor area aaj: **{weakest}** ({metrics[weakest]}%)\n\n"
                    f"Focus on {weakest} kal:\n"
                    + self._quick_tip(weakest.lower(), d, goals)
                )

        if qt == 'predict':
            proj = min(100, round(score * 1.08))
            return (
                f"🔮 **Score {score}/100 — Prediction:**\n\n"
                f"Is effort ko maintain karo → Next week est: **~{proj}/100** (+{proj-score} pts)\n\n"
                f"Best lever: "
                + ("Steps badhao!" if (d.get('steps') or 0) < 8000 else
                   "Sleep improve karo!" if (d.get('sleep_hours') or 0) < 7 else
                   "Consistency maintain karo!")
            )

        return (
            f"📋 **{date} — Score: {score}/100**\n\n"
            + (f"🚶 {d['steps']:,} steps\n" if d.get('steps') else "")
            + (f"😴 {d['sleep_hours']} hrs sleep\n" if d.get('sleep_hours') else "")
            + (f"💧 {d['water_liters']} L water\n" if d.get('water_liters') else "")
            + (f"🔥 {d['calories_burned']} kcal burned\n" if d.get('calories_burned') else "")
            + (f"🧠 Stress: {d['stress_score']}/100\n" if d.get('stress_score') else "")
            + (f"🔋 Recovery: {d['recovery_score']}/100\n" if d.get('recovery_score') else "")
            + f"\n{'🏆 Excellent!' if score >= 80 else '💪 Good effort!' if score >= 60 else '📈 Keep going!'}"
        )

    def _distance(self, qt, d, goals, q):
        km = d.get('distance_km') or (round(d['steps']*0.00076,2) if d.get('steps') else None)
        if not km: return "Distance data nahi mila!"
        return f"📍 **Distance: {km} km** ({round(km*0.621,2)} miles)\n{'5+ km = very active day! 🏆' if km >= 5 else '3-5 km = moderately active 💪'}"

    def _goal_progress(self, qt, d, goals, q):
        lines = []
        for name, (key, g_key, default_g) in {
            'Steps': ('steps','steps',10000),
            'Water': ('water_liters','water_liters',3.0),
            'Sleep': ('sleep_hours','sleep_hours',8.0),
            'Calories': ('calories_burned','calories_burned',500),
        }.items():
            val = d.get(key); g = goals.get(g_key, default_g)
            if val: lines.append(f"{'✅' if val>=g else '📈'} {name}: {round(val/g*100)}% ({val}/{g})")
        if not lines: return "Goal progress ke liye pehle data enter karo!"
        return "🎯 **Goal Progress:**\n\n" + '\n'.join(lines)

    def _generic(self, qt, d, goals, q):
        return (
            f"📊 Tumhare data ke basis pe:\n\n"
            + '\n'.join(f"• {k.replace('_',' ').title()}: {v}"
                        for k, v in d.items()
                        if v is not None and k not in ('date','source','notes','bmi_category'))
        )

    def _quick_tip(self, metric, d, goals):
        tips = {
            'steps': "• Lunch break 15 min walk\n• Stairs use karo\n• Evening 20 min walk fix karo",
            'sleep': "• Aaj 30 min pehle soyo\n• Screen off 1 hr before bed\n• Room cool karo",
            'water': "• Ab ek glass pi lo immediately\n• Har meal se pehle 1 glass\n• Bottle paas rakho",
            'calories': "• 20 min brisk walk = ~100 kcal\n• Protein snack lo",
        }
        return tips.get(metric, "• Consistent daily effort sabse important! 💪")


# ── Singleton ──────────────────────────────────────────────────
_engine_instance = None

def get_engine() -> QAEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = QAEngine()
    return _engine_instance