"""
Hybrid Intent Detector — ML + Rule-based Fallback (Enhanced)
Includes post-report Q&A intents
"""

from ..ml.ml_intent_model import MLIntentModel


class IntentDetector:

    def __init__(self):
        self.ml = MLIntentModel()
        self.ml_loaded = self.ml.load()

        self.intents = {

            # ── STEPS ─────────────────────────────────────────
            "steps_today": [
                "steps", "step count", "today steps", "walk", "walking",
                "kitne steps", "aaj steps", "how many steps", "steps aaj",
                "step counter", "mera steps"
            ],
            "steps_weekly": [
                "weekly steps", "this week steps", "week steps",
                "total steps week", "weekly walk"
            ],

            # ── SLEEP ─────────────────────────────────────────
            "sleep_duration": [
                "sleep duration", "sleep time", "neend kitni", "how long sleep",
                "kitni neend", "sleep hours", "soya kitna"
            ],
            "sleep_score": [
                "sleep score", "sleep quality", "sleep rating", "neend quality",
                "sleep grade"
            ],
            "deep_sleep": ["deep sleep", "deep neend", "slow wave sleep"],
            "rem_sleep":  ["rem sleep", "rem neend", "dream sleep"],

            # ── WATER ─────────────────────────────────────────
            "water_intake": [
                "water intake", "water drank", "pani kitna", "hydration",
                "how much water", "paani", "water consumed", "peya pani"
            ],
            "water_goal": [
                "water goal", "daily water target", "goal water",
                "pani ka goal", "water target"
            ],

            # ── WEIGHT / BMI ───────────────────────────────────
            "weight_current": [
                "weight", "current weight", "bmi", "body weight",
                "mera wazan", "kitna wazan", "bmi check"
            ],

            # ── HEART RATE ────────────────────────────────────
            "heart_rate_current": [
                "heart rate", "pulse", "bpm", "current heart rate",
                "dil ki dhadkan", "heartbeat"
            ],
            "heart_rate_average": [
                "average heart rate", "avg heart rate", "mean heart rate"
            ],
            "heart_rate_zone": [
                "heart zone", "heart rate zone", "hr zone", "cardio zone"
            ],

            # ── CALORIES ──────────────────────────────────────
            "calories_today": [
                "calories today", "calorie burn", "calories burned",
                "kitna calorie", "aaj calorie", "calories consumed"
            ],
            "calories_weekly": [
                "weekly calories", "calories this week", "week calorie"
            ],

            # ── STRESS / RECOVERY ─────────────────────────────
            "stress_level": [
                "stress", "stress level", "tension", "pressure",
                "anxious", "anxiety", "stress kitna"
            ],
            "recovery_score": [
                "recovery", "recovery score", "body recovery",
                "kitna recover", "recovery status"
            ],

            # ── SUMMARY ───────────────────────────────────────
            "daily_summary": [
                "daily summary", "today summary", "aaj ka summary",
                "full report", "today report", "daily report",
                "health summary", "complete summary"
            ],
            "weekly_summary": [
                "weekly summary", "week report", "this week report",
                "is week ka summary", "weekly report"
            ],
            "monthly_summary": [
                "monthly summary", "month report", "is mahine ka summary",
                "monthly report"
            ],

            # ── DISTANCE ──────────────────────────────────────
            "distance_today": [
                "distance", "run distance", "today distance",
                "kitna chala", "kitna daudha", "km today"
            ],

            # ── GOALS ─────────────────────────────────────────
            "goal_progress": [
                "goal", "progress", "target progress",
                "kitna complete hua", "goal status", "goal progress"
            ],

            # ── REMINDERS ─────────────────────────────────────
            "set_reminder": [
                "set reminder", "remind me", "reminder banao",
                "alarm set", "mujhe yaad dilao"
            ],
            "smart_remainder": [
                "smart reminder", "auto reminder", "ai reminder",
                "intelligent reminder"
            ],
            "delete_remainder": [
                "delete reminder", "remove reminder",
                "reminder hatao", "cancel reminder"
            ],

            # ── POST-REPORT Q&A INTENTS ───────────────────────
            "qa_improve": [
                "improve kaise", "better kaise", "kaise badhaye",
                "tips do", "advice do", "suggest karo", "improve tips",
                "how to improve", "kaise sudhar", "better banao",
                "improve karna", "improvement tips", "kya karu",
                "kya karna chahiye", "suggest", "help me improve"
            ],
            "qa_compare": [
                "compare", "last week", "yesterday", "pichle hafte",
                "pichle din", "difference", "change hua", "pehle vs ab",
                "before after", "previous", "vs", "kitna badla"
            ],
            "qa_goal_check": [
                "goal kab", "target kab", "kab achieve", "goal complete",
                "kab hoga", "kab tak", "goal reach", "target reach",
                "goal met", "achieve hoga",
                "goal kab milega", "kab milega", "goal milega",
                "target milega", "kab poora", "goal poora"
            ],
            "qa_why": [
                "kyu", "why", "reason kya", "cause kya", "wajah",
                "matlab kya", "kyun", "explain karo", "samjhao",
                "what does it mean", "iska matlab"
            ],
            "qa_impact": [
                "effect kya", "impact kya", "health par effect",
                "body par kya", "kya hoga", "problem hogi",
                "consequences", "result kya", "health impact"
            ],
            "qa_predict": [
                "predict", "forecast", "future mein", "kal ka",
                "next week", "aage kya", "trend kya hoga",
                "prediction do", "estimate karo"
            ],
            "qa_explain": [
                "explain", "kya hota hai", "what is", "kya hai",
                "describe karo", "batao kya", "definition",
                "samjhao kya", "kya matlab"
            ],
        }

    def detect(self, text: str) -> str:
        if not text:
            return "unknown"

        text_l = text.lower()

        # 1. ML first (if model loaded)
        if self.ml_loaded:
            intent = self.ml.predict(text_l)
            if intent and intent != "unknown":
                return intent

        # 2. Rule-based fallback — longer phrases first (avoid false positives)
        sorted_intents = sorted(
            self.intents.items(),
            key=lambda x: max((len(k) for k in x[1]), default=0),
            reverse=True
        )
        for intent, keywords in sorted_intents:
            for kw in keywords:
                if kw in text_l:
                    return intent

        return "unknown"

    def is_qa_intent(self, intent: str) -> bool:
        """Check if the detected intent is a post-report Q&A intent."""
        return intent.startswith("qa_")