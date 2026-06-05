"""
IntentRouter — NEXA HUB (Enhanced)
Routes fitness tracker intents + post-report Q&A intents
"""

from .health import get_report_context


class IntentRouter:

    def __init__(self, service):
        self.service = service

        self.routes = {
            # ── Metrics ───────────────────────────────────────
            "steps_today":          self.steps_today,
            "steps_weekly":         self.steps_weekly,
            "sleep_duration":       self.sleep_duration,
            "sleep_score":          self.sleep_score,
            "deep_sleep":           self.deep_sleep,
            "rem_sleep":            self.rem_sleep,
            "water_intake":         self.water_intake,
            "water_goal":           self.water_goal,
            "calories_today":       self.calories_today,
            "calories_weekly":      self.calories_weekly,
            "heart_rate_current":   self.heart_rate_current,
            "heart_rate_average":   self.heart_rate_average,
            "heart_rate_zone":      self.heart_rate_zone,
            "weight_current":       self.weight_current,
            "stress_level":         self.stress_level,
            "recovery_score":       self.recovery_score,
            "distance_today":       self.distance_today,
            "goal_progress":        self.goal_progress,
            "daily_summary":        self.daily_summary,
            "weekly_summary":       self.weekly_summary,
            "monthly_summary":      self.monthly_summary,
            "set_reminder":         self.set_reminder,
            "smart_remainder":      self.smart_reminder,
            "delete_remainder":     self.delete_reminder,

            # ── Q&A intents ───────────────────────────────────
            "qa_improve":           self.qa_improve,
            "qa_compare":           self.qa_compare,
            "qa_goal_check":        self.qa_goal_check,
            "qa_why":               self.qa_why,
            "qa_impact":            self.qa_impact,
            "qa_predict":           self.qa_predict,
            "qa_explain":           self.qa_explain,
        }

    def handle(self, intent: str, text: str, ctx: dict) -> dict:
        fn = self.routes.get(intent)
        if fn:
            return fn(text, ctx)
        # Fallback: try Q&A with current report context
        return self._smart_fallback(text, ctx)

    # ── METRIC HANDLERS ────────────────────────────────────────
    def steps_today(self, text, ctx):        return self.service.get_steps_today()
    def steps_weekly(self, text, ctx):       return self.service.get_steps_weekly()
    def sleep_duration(self, text, ctx):     return self.service.get_sleep_duration()
    def sleep_score(self, text, ctx):        return self.service.get_sleep_score()
    def deep_sleep(self, text, ctx):         return self.service.get_deep_sleep()
    def rem_sleep(self, text, ctx):          return self.service.get_rem_sleep()
    def water_intake(self, text, ctx):       return self.service.get_water_intake()
    def water_goal(self, text, ctx):         return self.service.get_water_goal()
    def calories_today(self, text, ctx):     return self.service.get_calories_today()
    def calories_weekly(self, text, ctx):    return self.service.get_calories_weekly()
    def heart_rate_current(self, text, ctx): return self.service.get_heart_rate_current()
    def heart_rate_average(self, text, ctx): return self.service.get_heart_rate_average()
    def heart_rate_zone(self, text, ctx):    return self.service.get_heart_rate_zone()
    def weight_current(self, text, ctx):     return self.service.get_weight()
    def stress_level(self, text, ctx):       return self.service.get_stress_level()
    def recovery_score(self, text, ctx):     return self.service.get_recovery_score()
    def distance_today(self, text, ctx):     return self.service.get_distance_today()
    def goal_progress(self, text, ctx):      return self.service.get_goal_progress()
    def daily_summary(self, text, ctx):      return self.service.get_daily_summary()
    def weekly_summary(self, text, ctx):     return self.service.get_weekly_summary()
    def monthly_summary(self, text, ctx):    return self.service.get_monthly_summary()
    def set_reminder(self, text, ctx):       return self.service.set_reminder()
    def smart_reminder(self, text, ctx):     return self.service.smart_reminder()
    def delete_reminder(self, text, ctx):    return self.service.delete_reminder()

    # ── Q&A HANDLERS ───────────────────────────────────────────
    def qa_improve(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_compare(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_goal_check(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_why(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_impact(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_predict(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def qa_explain(self, text, ctx):
        report_ctx = ctx.get("report_context") or get_report_context()
        return self.service.answer_report_question(text, report_ctx)

    def _smart_fallback(self, text: str, ctx: dict) -> dict:
        """
        If intent is unknown, check if we have a recent report context
        and treat the message as a Q&A question about that report.
        """
        report_ctx = ctx.get("report_context") or get_report_context()
        if report_ctx:
            return self.service.answer_report_question(text, report_ctx)
        return {
            "response": (
                "🤔 Samajh nahi aaya. Try these commands:\n\n"
                "📊 'Daily summary' — aaj ka full report\n"
                "🚶 'Steps today' — aaj ke steps\n"
                "😴 'Sleep duration' — neend kitni hui\n"
                "💧 'Water intake' — pani kitna piya\n"
                "❤️ 'Heart rate' — dhadkan check karo\n\n"
                "Ya koi bhi health question poochho!"
            ),
            "type": "fallback"
        }