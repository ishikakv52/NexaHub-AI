"""
NEXA HUB — HealthDataService (DB-backed)
Reads ONLY from user's actual DB data via db_service.
Falls back to graceful "no data" prompts.
"""

import datetime

# ── Lazy DB loader — avoids AppRegistryNotReady error ──────────
_DB_AVAILABLE = False
_db_funcs = {}

def _ensure_db() -> bool:
    """
    Load db_service lazily so Django's app registry is
    fully ready before we import models.
    """
    global _DB_AVAILABLE, _db_funcs
    if _DB_AVAILABLE:
        return True
    try:
        from VoiceAssistant.VoiceAssistant.db_service import (
            get_today, get_last_n_days, get_weekly_summary,
            get_monthly_summary, get_goals, compare_with_prev, has_any_data
        )
        _db_funcs = {
            'get_today':           get_today,
            'get_last_n_days':     get_last_n_days,
            'get_weekly_summary':  get_weekly_summary,
            'get_monthly_summary': get_monthly_summary,
            'get_goals':           get_goals,
            'compare_with_prev':   compare_with_prev,
            'has_any_data':        has_any_data,
        }
        _DB_AVAILABLE = True
        return True
    except Exception as e:
        import traceback
        print(f"[health.py] _ensure_db failed: {e}")
        traceback.print_exc()
        return False

# Convenience wrappers so the rest of the file reads cleanly
def get_today(sid):           return _db_funcs['get_today'](sid)           if _ensure_db() else {}
def get_last_n_days(sid, n):  return _db_funcs['get_last_n_days'](sid, n)  if _ensure_db() else []
def get_weekly_summary(sid):  return _db_funcs['get_weekly_summary'](sid)  if _ensure_db() else {}
def get_monthly_summary(sid): return _db_funcs['get_monthly_summary'](sid) if _ensure_db() else {}
def get_goals(sid):           return _db_funcs['get_goals'](sid)           if _ensure_db() else {}
def compare_with_prev(sid, metric, days): return _db_funcs['compare_with_prev'](sid, metric, days) if _ensure_db() else {}
def has_any_data(sid):        return _db_funcs['has_any_data'](sid)        if _ensure_db() else False

# QA Engine — ML model trained on 10,223+ dataset utterances
_QA_ENGINE = None
def _get_qa():
    global _QA_ENGINE
    if _QA_ENGINE is None:
        try:
            from .qa_engine import get_engine
            _QA_ENGINE = get_engine()
        except Exception as e:
            print(f"[QAEngine] Load failed: {e}")
    return _QA_ENGINE

_last_report_context: dict = {}

def set_report_context(ctx: dict):
    global _last_report_context
    _last_report_context = ctx

def get_report_context() -> dict:
    return _last_report_context


class HealthDataService:
    def __init__(self, session_id: str = 'default'):
        self.sid = session_id

    def _no_data(self, metric: str) -> dict:
        return {
            'response': (
                f"📭 **{metric} ka data nahi mila!**\n\n"
                f"Pehle apna data enter karo:\n"
                f"  👉 Form se data save karo\n"
                f"  👉 Ya bolo: 'Save my steps 8500 sleep 7 water 2.5'\n\n"
                f"Jab data save hoga tab main accurate report dunga! 💪"
            ),
            'type': 'no_data'
        }

    def _goal(self, metric: str, default: float) -> float:
        goals = get_goals(self.sid)
        return goals.get(metric, default)

    # ── STEPS ──────────────────────────────────────────────────
    def get_steps_today(self) -> dict:
        d = get_today(self.sid)
        if not d or d.get('steps') is None: return self._no_data('Steps Today')
        steps = d['steps']; goal = self._goal('steps', 10000)
        pct = round((steps/goal)*100); dist = d.get('distance_km') or round(steps*0.00076,2)
        data = {'steps': steps, 'goal': goal, 'percentage': pct, 'distance_km': dist}
        set_report_context({'type':'steps_today','data':data,'raw':d})
        return {
            'response': (
                f"🚶 **Aaj ke Steps: {steps:,}**\n\n"
                f"🎯 Goal: {goal:,}  |  Progress: {pct}%\n"
                f"📍 Distance: {dist} km\n"
                f"{'✅ Goal complete! 🏆' if pct>=100 else f'💪 Aur {goal-steps:,} steps baki!'}\n\n"
                f"💡 {'Great work!' if steps>=10000 else 'Evening walk se complete karo!'}"
            ),
            'data': data, 'type': 'steps_today'
        }

    def get_steps_weekly(self) -> dict:
        d = get_weekly_summary(self.sid)
        if not d: return self._no_data('Weekly Steps')
        days = d.get('steps_by_day', {}); avg = d.get('avg_steps',0); best = d.get('best_day','N/A')
        data = {'days': days, 'average': avg, 'best_day': best, 'total': d.get('total_steps',0)}
        set_report_context({'type':'steps_weekly','data':data,'raw':d})
        rows = '\n'.join([f"  {'✅' if v>=10000 else '📉'} {k}: {v:,}" for k,v in days.items()])
        return {
            'response': f"📊 **Weekly Steps — {d.get('week','This Week')}**\n\n{rows}\n\n📈 Avg: {avg:,}/day  |  Best: {best}\n🔢 Total: {data['total']:,}",
            'data': data, 'type': 'steps_weekly'
        }

    # ── SLEEP ──────────────────────────────────────────────────
    def get_sleep_duration(self) -> dict:
        d = get_today(self.sid)
        if not d or d.get('sleep_hours') is None: return self._no_data('Sleep Duration')
        hrs = d['sleep_hours']; qual = d.get('sleep_quality','N/A')
        data = {'hours': hrs, 'quality': qual, 'bedtime': d.get('bedtime','—'), 'wake': d.get('wake_time','—')}
        set_report_context({'type':'sleep_duration','data':data,'raw':d})
        return {
            'response': (
                f"😴 **Sleep: {hrs} hrs**\n\n"
                f"⭐ Quality: {qual}\n"
                f"🛏️ Bedtime: {data['bedtime']} → Wake: {data['wake']}\n\n"
                f"{'✅ Great sleep!' if hrs>=7 else '⚠️ Neend kam — kal 30 min pehle soyo!'}\n"
                f"💡 {'8 hrs = optimal recovery' if hrs<8 else 'Perfect!'}"
            ),
            'data': data, 'type': 'sleep_duration'
        }

    def get_sleep_score(self) -> dict:
        d = get_today(self.sid)
        if not d or d.get('sleep_hours') is None: return self._no_data('Sleep Score')
        hrs = d['sleep_hours']; score = min(round((hrs/9)*100),100)
        grade = 'A+' if score>=90 else 'A' if score>=85 else 'B+' if score>=78 else 'B' if score>=70 else 'C'
        data = {'score': score, 'grade': grade, 'hours': hrs}
        set_report_context({'type':'sleep_score','data':data,'raw':d})
        return {'response': f"⭐ **Sleep Score: {score}/100 ({grade})**\n\nBased on {hrs} hrs sleep\n{'✅ Excellent!' if score>=85 else '📈 Improvement possible'}\n\n💡 7-9 hrs = score 85+", 'data': data, 'type': 'sleep_score'}

    def get_deep_sleep(self) -> dict:
        d = get_today(self.sid)
        deep = d.get('deep_sleep_hours') if d else None
        if deep is None:
            total = d.get('sleep_hours') if d else None
            if not total: return self._no_data('Deep Sleep')
            deep = round(total*0.22,1)
        pct = round((deep/max(d.get('sleep_hours',deep),0.1))*100)
        data = {'hours': deep, 'percentage': pct}
        set_report_context({'type':'deep_sleep','data':data,'raw':d})
        return {'response': f"🌙 **Deep Sleep: {deep} hrs ({pct}%)**\n\n🎯 Recommended: 1.5-2 hrs (20-25%)\n{'✅ Good!' if deep>=1.5 else '⚠️ Deep sleep kam hai'}\n\n💡 Screen avoid karo sone se 1 hr pehle!", 'data': data, 'type': 'deep_sleep'}

    def get_rem_sleep(self) -> dict:
        d = get_today(self.sid)
        rem = d.get('rem_sleep_hours') if d else None
        if rem is None:
            total = d.get('sleep_hours') if d else None
            if not total: return self._no_data('REM Sleep')
            rem = round(total*0.20,1)
        data = {'hours': rem}
        set_report_context({'type':'rem_sleep','data':data,'raw':d})
        return {'response': f"🌙 **REM Sleep: {rem} hrs**\n\n🎯 Recommended: 1.5-2 hrs\n{'✅ Good REM!' if rem>=1.5 else '⚠️ REM low hai'}\n\n💡 REM = memory aur creativity ke liye zaroori!", 'data': data, 'type': 'rem_sleep'}

    # ── WATER ──────────────────────────────────────────────────
    def get_water_intake(self) -> dict:
        d = get_today(self.sid)
        if not d or d.get('water_liters') is None: return self._no_data('Water Intake')
        ltrs = d['water_liters']; goal = self._goal('water_liters',3.0); pct = round((ltrs/goal)*100)
        data = {'liters': ltrs, 'goal': goal, 'percentage': pct, 'glasses': round(ltrs*4)}
        set_report_context({'type':'water_intake','data':data,'raw':d})
        return {
            'response': (
                f"💧 **Water: {ltrs} L ({pct}% of {goal} L)**\n\n"
                f"🥛 Glasses: ~{data['glasses']}\n"
                f"{'✅ Hydrated! 🎉' if pct>=100 else f'⚠️ Aur {round(goal-ltrs,1)} L baki ({int((goal-ltrs)*4)} glasses)'}\n\n"
                f"💡 Har ghante ek glass paani!"
            ),
            'data': data, 'type': 'water_intake'
        }

    def get_water_goal(self) -> dict:
        goal = self._goal('water_liters',3.0)
        data = {'goal': goal}
        set_report_context({'type':'water_goal','data':data})
        return {'response': f"🎯 **Water Goal: {goal} L/day**\n\n💡 Change karne ke liye: 'Set water goal 3.5 liters'", 'data': data, 'type': 'water_goal'}

    # ── CALORIES ───────────────────────────────────────────────
    def get_calories_today(self) -> dict:
        d = get_today(self.sid)
        burned = d.get('calories_burned') if d else None
        consumed = d.get('calories_consumed') if d else None
        if burned is None and consumed is None: return self._no_data('Calories')
        net = (consumed-burned) if (consumed and burned) else None
        data = {'burned': burned, 'consumed': consumed, 'net': net}
        set_report_context({'type':'calories_today','data':data,'raw':d})
        parts = []
        if burned: parts.append(f"  🏃 Burned:   {burned} kcal")
        if consumed: parts.append(f"  🍽️ Consumed: {consumed} kcal")
        if net is not None: parts.append(f"  📊 Net:      {'➕' if net>0 else '➖'} {abs(net)} kcal ({'surplus' if net>0 else 'deficit'})")
        return {'response': "🔥 **Calories Today**\n\n" + '\n'.join(parts) + "\n\n💡 500 cal deficit = 0.5 kg/week loss!", 'data': data, 'type': 'calories_today'}

    def get_calories_weekly(self) -> dict:
        d = get_weekly_summary(self.sid)
        if not d or not d.get('total_calories'): return self._no_data('Weekly Calories')
        data = {'total': d['total_calories'], 'average': round(d['total_calories']/7)}
        set_report_context({'type':'calories_weekly','data':data,'raw':d})
        return {'response': f"🔥 **Weekly Calories**\n\n📅 {d.get('week','This Week')}\n🔥 Total: {data['total']:,} kcal\n📊 Daily Avg: {data['average']} kcal\n\n💡 7,700 kcal = 1 kg fat", 'data': data, 'type': 'calories_weekly'}

    # ── HEART RATE ─────────────────────────────────────────────
    def get_heart_rate_current(self) -> dict:
        d = get_today(self.sid)
        bpm = (d.get('heart_rate_resting') or d.get('heart_rate_avg')) if d else None
        if not bpm: return self._no_data('Heart Rate')
        status = 'Normal' if 60<=bpm<=100 else ('Low' if bpm<60 else 'High')
        data = {'bpm': bpm, 'status': status}
        set_report_context({'type':'heart_rate_current','data':data,'raw':d})
        return {'response': f"❤️ **Heart Rate: {bpm} BPM ({status})**\n\n{'✅ Normal resting HR' if 60<=bpm<=100 else '⚠️ Unusual — consult doctor!'}\n\n💡 Normal: 60-100 BPM. Athletes: 40-60 BPM", 'data': data, 'type': 'heart_rate_current'}

    def get_heart_rate_average(self) -> dict:
        last7 = get_last_n_days(self.sid, 7)
        vals = [e['heart_rate_avg'] for e in last7 if e.get('heart_rate_avg')]
        if not vals: return self._no_data('Average Heart Rate')
        avg = round(sum(vals)/len(vals))
        data = {'average': avg, 'days': len(vals)}
        set_report_context({'type':'heart_rate_average','data':data})
        return {'response': f"📊 **7-Day Avg HR: {avg} BPM**\n\n📅 Data from {len(vals)} days\n💡 Lower resting HR = better cardiovascular fitness!", 'data': data, 'type': 'heart_rate_average'}

    def get_heart_rate_zone(self) -> dict:
        d = get_today(self.sid)
        avg = d.get('heart_rate_avg') if d else None
        if not avg: return self._no_data('Heart Rate Zone')
        pct_max = (avg/190)*100
        zone = 'Rest' if pct_max<50 else 'Fat Burn' if pct_max<70 else 'Cardio' if pct_max<85 else 'Peak'
        data = {'zone': zone, 'avg_bpm': avg, 'pct_max': round(pct_max)}
        set_report_context({'type':'heart_rate_zone','data':data,'raw':d})
        return {'response': f"🔥 **HR Zone: {zone} ({avg} BPM)**\n\n💡 Fat Burn (60-70% max) = best for fat loss!\nCardio (70-85%) = cardiovascular fitness", 'data': data, 'type': 'heart_rate_zone'}

    # ── WEIGHT ─────────────────────────────────────────────────
    def get_weight(self) -> dict:
        d = get_today(self.sid)
        if not d or not d.get('weight_kg'):
            recent = get_last_n_days(self.sid, 7)
            for r in reversed(recent):
                if r.get('weight_kg'): d=r; break
        if not d or not d.get('weight_kg'): return self._no_data('Weight & BMI')
        w = d['weight_kg']; bmi = d.get('bmi'); cat = d.get('bmi_category','N/A')
        goal = self._goal('weight_kg', w); rem = round(w-goal,1)
        data = {'weight': w, 'bmi': bmi, 'category': cat, 'goal': goal, 'to_lose': max(rem,0)}
        set_report_context({'type':'weight_current','data':data,'raw':d})
        return {
            'response': (
                f"⚖️ **Weight: {w} kg**\n\n"
                f"📊 BMI: {bmi} ({cat})\n"
                f"🎯 Goal: {goal} kg\n"
                f"{'🎉 Goal Achieved! 🏆' if rem<=0 else f'📉 Baki: {abs(rem)} kg (~{int(abs(rem)*2)} weeks)'}\n\n"
                f"💡 0.5-1 kg/week = safe loss rate"
            ),
            'data': data, 'type': 'weight_current'
        }

    # ── STRESS / RECOVERY ──────────────────────────────────────
    def get_stress_level(self) -> dict:
        d = get_today(self.sid)
        score = d.get('stress_score') if d else None
        if score is None: return self._no_data('Stress Level')
        level = 'Low' if score<30 else 'Moderate' if score<55 else 'High' if score<75 else 'Very High'
        emoji = {'Low':'😊','Moderate':'😐','High':'😰','Very High':'🆘'}.get(level,'😐')
        data = {'level': level, 'score': score}
        set_report_context({'type':'stress_level','data':data,'raw':d})
        return {'response': f"🧠 **Stress: {emoji} {level} ({score}/100)**\n\n{'✅ Well managed!' if score<40 else '⚠️ High stress — take action!'}\n\n💡 4-7-8 breathing try karo!", 'data': data, 'type': 'stress_level'}

    def get_recovery_score(self) -> dict:
        d = get_today(self.sid)
        score = d.get('recovery_score') if d else None
        if score is None: return self._no_data('Recovery Score')
        grade = 'A' if score>=85 else 'B' if score>=70 else 'C' if score>=55 else 'D'
        data = {'score': score, 'grade': grade}
        set_report_context({'type':'recovery_score','data':data,'raw':d})
        rec = '✅ Full workout karo aaj!' if score>=80 else '💛 Moderate workout' if score>=60 else '⚠️ Rest ya light stretching'
        return {'response': f"🔋 **Recovery: {score}/100 ({grade})**\n\n{rec}\n\n💡 Sleep + protein + hydration = better recovery", 'data': data, 'type': 'recovery_score'}

    # ── DISTANCE ───────────────────────────────────────────────
    def get_distance_today(self) -> dict:
        d = get_today(self.sid)
        km = d.get('distance_km') if d else None
        if not km and d and d.get('steps'): km = round(d['steps']*0.00076,2)
        if not km: return self._no_data('Distance')
        data = {'km': km, 'miles': round(km*0.621,2)}
        set_report_context({'type':'distance_today','data':data,'raw':d})
        return {'response': f"📍 **Distance Today: {km} km ({data['miles']} miles)**\n\n💡 5 km/day = very active lifestyle!", 'data': data, 'type': 'distance_today'}

    # ── GOAL PROGRESS ──────────────────────────────────────────
    def get_goal_progress(self) -> dict:
        d = get_today(self.sid)
        goals = get_goals(self.sid)
        if not d: return self._no_data('Goal Progress')
        metrics = {
            'Steps':    (d.get('steps'),          goals.get('steps',10000)),
            'Water':    (d.get('water_liters'),    goals.get('water_liters',3.0)),
            'Sleep':    (d.get('sleep_hours'),     goals.get('sleep_hours',8.0)),
            'Calories': (d.get('calories_burned'), goals.get('calories_burned',500)),
        }
        progress = {n: min(round((v/g)*100),100) for n,(v,g) in metrics.items() if v is not None}
        if not progress: return self._no_data('Goal Progress')
        overall = round(sum(progress.values())/len(progress))
        progress['Overall'] = overall
        set_report_context({'type':'goal_progress','data':progress,'raw':d})
        bars = '\n'.join([f"  {'✅' if v>=100 else '📈'} {k}: {v}%" for k,v in progress.items()])
        return {'response': f"🎯 **Goal Progress Today**\n\n{bars}\n\n{'🎉 Amazing performance!' if overall>=85 else '💪 Keep going!'}", 'data': progress, 'type': 'goal_progress'}

    # ── SUMMARIES ──────────────────────────────────────────────
    def get_daily_summary(self) -> dict:
        d = get_today(self.sid)
        if not d or all(d.get(k) is None for k in ['steps','sleep_hours','water_liters','calories_burned']):
            return self._no_data('Daily Summary')
        def f(v,u=''): return f"{v}{u}" if v is not None else '—'
        data = {k: d.get(k) for k in ['date','steps','sleep_hours','calories_burned','calories_consumed','water_liters','heart_rate_resting','stress_score','recovery_score','weight_kg','distance_km','overall_score']}
        data['heart_rate'] = d.get('heart_rate_resting') or d.get('heart_rate_avg')
        if data['steps'] and not data['distance_km']: data['distance_km'] = round(data['steps']*0.00076,2)
        set_report_context({'type':'daily_summary','data':data,'raw':d})
        return {
            'response': (
                f"📋 **Daily Summary — {data['date']}**\n\n"
                f"🚶 Steps:      {f(data['steps'],' steps')}\n"
                f"😴 Sleep:      {f(data['sleep_hours'],' hrs')}\n"
                f"🔥 Cal Burned: {f(data['calories_burned'],' kcal')}\n"
                f"🍽️ Cal Intake: {f(data['calories_consumed'],' kcal')}\n"
                f"💧 Water:      {f(data['water_liters'],' L')}\n"
                f"❤️ Heart:      {f(data['heart_rate'],' BPM')}\n"
                f"🧠 Stress:     {f(data['stress_score'],'/100')}\n"
                f"🔋 Recovery:   {f(data['recovery_score'],'/100')}\n"
                f"⚖️ Weight:     {f(data['weight_kg'],' kg')}\n"
                f"📍 Distance:   {f(data['distance_km'],' km')}\n\n"
                f"🏅 **Overall Score: {data['overall_score']}/100**\n\n"
                f"💬 Is summary ke baare mein kuch poochho!"
            ),
            'data': data, 'type': 'daily_summary', 'qa_enabled': True, 'show_qa_prompt': True
        }

    def get_weekly_summary(self) -> dict:
        d = get_weekly_summary(self.sid)
        if not d: return self._no_data('Weekly Summary')
        data = {k: d.get(k) for k in ['week','avg_steps','total_steps','total_calories','avg_sleep','avg_water','avg_recovery','avg_stress','consistency','days_logged','best_day']}
        set_report_context({'type':'weekly_summary','data':data,'raw':d})
        return {
            'response': (
                f"📊 **Weekly Summary — {data['week']}**\n\n"
                f"🚶 Avg Steps:    {(data['avg_steps'] or 0):,}/day\n"
                f"🔢 Total Steps:  {(data['total_steps'] or 0):,}\n"
                f"🔥 Total Cal:    {(data['total_calories'] or 0):,} kcal\n"
                f"😴 Avg Sleep:    {data['avg_sleep']} hrs\n"
                f"💧 Avg Water:    {data['avg_water']} L\n"
                f"🔋 Avg Recovery: {data['avg_recovery']}/100\n"
                f"📈 Consistency:  {data['consistency']}%  ({data['days_logged']}/7 days)\n"
                f"🏆 Best Day:     {data['best_day']}\n\n"
                f"{'✅ Excellent week! 🎉' if (data['consistency'] or 0)>=80 else '💪 Next week aur better karo!'}\n\n"
                f"💬 Kuch specific poochhna hai?"
            ),
            'data': data, 'type': 'weekly_summary', 'qa_enabled': True, 'show_qa_prompt': True
        }

    def get_monthly_summary(self) -> dict:
        d = get_monthly_summary(self.sid)
        if not d: return self._no_data('Monthly Summary')
        wc = d.get('weight_change'); wc_str = (f"{'+' if wc and wc>0 else ''}{wc} kg" if wc is not None else '—')
        data = {k: d.get(k) for k in ['month','total_steps','avg_daily_steps','avg_sleep','avg_water','total_calories','avg_recovery','days_logged','consistency','weight_change']}
        set_report_context({'type':'monthly_summary','data':data,'raw':d})
        return {
            'response': (
                f"📅 **Monthly Summary — {data['month']}**\n\n"
                f"🚶 Total Steps:    {(data['total_steps'] or 0):,}\n"
                f"📈 Daily Avg:      {(data['avg_daily_steps'] or 0):,}\n"
                f"😴 Avg Sleep:      {data['avg_sleep']} hrs\n"
                f"💧 Avg Water:      {data['avg_water']} L\n"
                f"🔥 Cal Burned:     {(data['total_calories'] or 0):,} kcal\n"
                f"🔋 Avg Recovery:   {data['avg_recovery']}/100\n"
                f"⚖️ Weight Change:  {wc_str}\n"
                f"📊 Consistency:    {data['consistency']}%  ({data['days_logged']} days)\n\n"
                f"💬 Is mahine ke baare mein kuch poochho!"
            ),
            'data': data, 'type': 'monthly_summary', 'qa_enabled': True, 'show_qa_prompt': True
        }

    # ── REMINDERS ──────────────────────────────────────────────
    def set_reminder(self): return {'response': "⏰ **Reminders Set!**\n\n🔔 7 AM Workout\n🔔 3 PM Water\n🔔 10 PM Sleep", 'type': 'set_reminder'}
    def smart_reminder(self):
        d = get_today(self.sid)
        return {'response': f"🧠 **Smart Reminders (Based on Your Data)**\n\n💧 Water: {d.get('water_liters','?')} L piya — 2 PM reminder!\n😴 Sleep: aaj 10 PM reminder\n🏃 Every hour 5 min walk!", 'type': 'smart_reminder'}
    def delete_reminder(self): return {'response': "🗑️ Reminder deleted! Remaining: 2 active.", 'type': 'delete_reminder'}

    # ── POST-REPORT Q&A (ML-powered, DB-personalized) ──────────
    def answer_report_question(self, question: str, report_context: dict = None) -> dict:
        ctx   = report_context or get_report_context() or {}
        rtype = ctx.get('type', 'unknown')
        data  = ctx.get('data', {})
        raw   = ctx.get('raw', {})
        q     = question.lower()

        # ── Step 1: Get user real data from DB ──────────────
        user_data = {}
        goals     = {}
        try:
            user_data = get_today(self.sid) or {}
            goals     = get_goals(self.sid) or {}
        except Exception:
            pass

        # Merge report data with live DB data
        merged = {**data, **{k: v for k, v in (raw or {}).items() if v is not None}}
        if user_data:
            merged = {**merged, **{k: v for k, v in user_data.items() if v is not None}}

        engine = _get_qa()

        if engine and engine.ready and merged:
            response = engine.answer(
                question       = question,
                user_data      = merged,
                report_context = ctx,
                goals          = goals,
            )

            if any(w in q for w in ['compare','last week','pichle','difference','trend']):
                try:
                    metric_map = {
                        'steps_today':'steps', 'sleep_duration':'sleep_hours',
                        'water_intake':'water_liters', 'calories_today':'calories_burned',
                        'recovery_score':'recovery_score', 'stress_level':'stress_score',
                    }
                    ml_result = engine.detect_metric_intent(question)
                    metric    = metric_map.get(ml_result.get('intent')) or metric_map.get(rtype)
                    if metric:
                        comp = compare_with_prev(self.sid, metric, 7)
                        if comp.get('today') and comp.get('previous'):
                            trend     = comp['trend']
                            icon      = '📈' if trend == 'up' else ('📉' if trend == 'down' else '➡️')
                            diff_sign = '+' if trend == 'up' else ''
                            pct_sign  = '+' if (comp.get('pct_change', 0) or 0) > 0 else ''
                            response += (
                                "\n\n" + icon + " **vs 7 din pehle:**\n"
                                + f"Pehle: {comp['previous']} → Aaj: {comp['today']}\n"
                                + f"Change: {diff_sign}{comp.get('diff',0)} "
                                + f"({pct_sign}{comp.get('pct_change',0)}%)"
                            )
                except Exception:
                    pass

            return {
                'response':    response,
                'type':        'qa_answer',
                'confidence':  engine.detect_metric_intent(question).get('confidence', 0),
            }

        # ── Fallback: rule-based logic ─────────────
        if any(w in q for w in ['improve','better','kaise badhaye','tips','behtar']): return self._improvement_advice(rtype, data, raw)
        if any(w in q for w in ['compare','last week','pichle','difference','trend']): return self._comparison_answer(rtype, data, raw)
        if any(w in q for w in ['goal','target','kab','achieve','complete']): return self._goal_answer(rtype, data, raw)
        if any(w in q for w in ['why','kyu','reason','explain','samjhao']): return self._explain_metric(rtype, data)
        if any(w in q for w in ['effect','impact','health','risk','kya hoga']): return self._health_impact(rtype, data, raw)
        if any(w in q for w in ['predict','forecast','next','future']): return self._predict_trend(rtype, data, raw)
        if any(w in q for w in ['steps','walk']): return self.get_steps_today()
        if any(w in q for w in ['sleep','neend']): return self.get_sleep_duration()
        if any(w in q for w in ['water','pani']): return self.get_water_intake()
        if any(w in q for w in ['calorie','burn']): return self.get_calories_today()
        if any(w in q for w in ['heart','bpm']): return self.get_heart_rate_current()
        if any(w in q for w in ['stress']): return self.get_stress_level()
        if any(w in q for w in ['recovery']): return self.get_recovery_score()
        if any(w in q for w in ['weight','bmi']): return self.get_weight()
        return self._contextual_default(rtype, question)

    def _improvement_advice(self, rtype, data, raw):
        advice = {
            'steps_today':    "🚶 **Steps Tips:**\n\n• Stairs use karo\n• Lunch break 10 min walk\n• Phone calls pe walk\n• Evening 20 min fixed walk",
            'sleep_duration': "😴 **Sleep Tips:**\n\n• Fixed schedule daily\n• 1 hr pehle screen off\n• Room dark & cool (18-20°C)\n• Caffeine 6 PM ke baad avoid",
            'water_intake':   "💧 **Hydration Tips:**\n\n• Subah 2 glass uthte hi\n• Har meal se pehle 1 glass\n• Flavored water try karo\n• Bottle always paas rakho",
            'calories_today': "🔥 **Calorie Tips:**\n\n• 500 cal deficit = 0.5 kg/week\n• Protein badhao\n• Liquid calories avoid karo\n• Sunday meal prep karo",
            'stress_level':   "🧠 **Stress Tips:**\n\n• 4-7-8 breathing\n• Daily 10 min meditation\n• Exercise = best stress relief\n• Journal likhna start karo",
            'recovery_score': "🔋 **Recovery Tips:**\n\n• 7-9 hrs quality sleep\n• Post-workout protein 30g\n• Cold shower try karo\n• Rest days skip mat karo!",
        }
        extra = ''
        if rtype == 'steps_today' and data.get('steps') and data.get('goal'):
            gap = data['goal'] - data['steps']
            if gap > 0: extra = f"\n\n🎯 Aaj {gap:,} more steps — approx {round(gap/130)} mins walk!"
        return {'response': advice.get(rtype, "💪 **General Tips:**\n\n• 10,000 steps/day\n• 7-9 hrs sleep\n• 3 L water\n• 30 min exercise 5x/week") + extra, 'type': 'qa_answer'}

    def _comparison_answer(self, rtype, data, raw):
        metric_map = {'steps_today':'steps','sleep_duration':'sleep_hours','water_intake':'water_liters','calories_today':'calories_burned','recovery_score':'recovery_score','stress_level':'stress_score'}
        metric = metric_map.get(rtype)
        if metric:
            comp = compare_with_prev(self.sid, metric, 7)
            tv = comp.get('today'); pv = comp.get('previous')
            if tv is not None and pv is not None:
                trend = comp.get('trend','same'); pct = comp.get('pct_change',0)
                icon = '📈' if trend=='up' else ('📉' if trend=='down' else '➡️')
                return {'response': f"{icon} **{rtype.replace('_',' ').title()} Comparison**\n\n📅 Aaj: {tv}\n🕐 7 din pehle: {pv}\n📊 Change: {'+' if trend=='up' else ''}{comp.get('diff',0)} ({'+' if pct>0 else ''}{pct}%)\n\n{'✅ Improving!' if trend=='up' else '⚠️ Decline detected!'}", 'type': 'qa_answer'}
        return {'response': "📊 Zyada accurate comparison ke liye daily data save karte raho!", 'type': 'qa_answer'}

    def _goal_answer(self, rtype, data, raw):
        goals = get_goals(self.sid)
        if rtype == 'steps_today':
            steps = data.get('steps',0); goal = goals.get('steps',10000); rem = goal-steps
            return {'response': f"🎯 **Steps Goal**\n\n✅ Achieved: {steps:,}/{goal:,} ({round((steps/goal)*100)}%)\n{'🎉 Complete!' if rem<=0 else f'⏳ Baki: {rem:,} steps ({round(rem/130)} min walk)'}", 'type': 'qa_answer'}
        if rtype == 'water_intake':
            ltrs = data.get('liters',0); goal = goals.get('water_liters',3.0); rem = round(goal-ltrs,1)
            return {'response': f"💧 **Water Goal**\n\n✅ Piya: {ltrs} L/{goal} L\n{'🎉 Complete!' if rem<=0 else f'⏳ Baki: {rem} L ({int(rem*4)} glasses)'}", 'type': 'qa_answer'}
        if rtype == 'weight_current':
            w = data.get('weight',0); goal = goals.get('weight_kg',w); rem = round(w-goal,1); weeks = round(abs(rem)*2)
            target_date = (datetime.date.today()+datetime.timedelta(weeks=weeks)).strftime('%d %b %Y')
            return {'response': f"⚖️ **Weight Goal**\n\nCurrent: {w} kg → Goal: {goal} kg\n{'🎉 Achieved!' if rem<=0 else f'📉 Baki: {abs(rem)} kg → ~{weeks} weeks\n📅 Est date: {target_date}'}", 'type': 'qa_answer'}
        return {'response': "🎯 Goal set karne ke liye bolo:\n'Set steps goal 12000'\n'Set water goal 3.5'\n'Set weight goal 65'", 'type': 'qa_answer'}

    def _explain_metric(self, rtype, data):
        exp = {
            'deep_sleep': "🌙 **Deep Sleep kya hai?**\n\nStage N3 mein body:\n• Growth hormone release karta hai\n• Muscles repair hoti hain\n• Memory consolidate hoti hai\n• 1.5-2 hrs recommended",
            'rem_sleep': "🌙 **REM Sleep kya hai?**\n\nRapid Eye Movement:\n• Dreams is phase mein hote hain\n• Emotional processing\n• Memory formation & creativity\n• 1.5-2 hrs needed",
            'heart_rate_zone': "❤️ **HR Zones:**\n\nZone 1 (50-60%): Rest\nZone 2 (60-70%): Fat Burn ← Best!\nZone 3 (70-85%): Cardio\nZone 4 (85%+): Peak\n\n💡 Max HR = 220 - age",
            'recovery_score': "🔋 **Recovery Score:**\n\nFactors:\n• HRV (Heart Rate Variability)\n• Sleep quality\n• Previous workout intensity\n• Stress + Hydration\n\n💡 80+ = intense training ready",
            'stress_level': "🧠 **Stress Track kyu?**\n\nHigh stress causes:\n• Cortisol → belly fat storage\n• Slow recovery\n• Poor sleep quality\n• Weakened immunity",
            'daily_summary': "📋 **Overall Score Formula:**\n\n• Steps (25%): steps/goal\n• Sleep (25%): hrs/8\n• Water (20%): liters/3\n• Recovery (30%): score\n\n💡 80+ = excellent day!",
        }
        return {'response': exp.get(rtype, f"📚 **{rtype.replace('_',' ').title()}** ek important health metric hai. Regular tracking se patterns identify hote hain aur improvements possible hote hain!"), 'type': 'qa_answer'}

    def _health_impact(self, rtype, data, raw):
        impacts = {
            'steps_today': f"🦵 {'✅ Active day! Cardiovascular health improve ho rahi hai.' if (data.get('steps') or 0)>=7500 else '⚠️ Low activity. Sedentary lifestyle se diabetes, heart disease ka risk badhta hai!'}",
            'sleep_duration': f"😴 {'✅ Good sleep = sharp mind, stable mood, healthy metabolism!' if (data.get('hours') or 0)>=7 else '⚠️ Kam neend → poor focus, hunger hormones (ghrelin) badh jaata hai, cortisol high!'}",
            'water_intake': f"💧 {'✅ Hydrated! Kidney, skin, digestion sab smooth.' if (data.get('percentage') or 0)>=80 else '⚠️ Dehydration = headache, 30% focus decline, slow metabolism, kidney stress!'}",
            'stress_level': f"🧠 {'✅ Stress manageable. Cortisol normal range mein.' if data.get('level') in ['Low','Moderate'] else '🆘 High stress! Cortisol → belly fat, muscle loss, immune crash. Act karo abhi!'}",
            'recovery_score': f"🔋 {'✅ Good recovery! Body ready for training.' if (data.get('score') or 0)>=75 else '⚠️ Poor recovery = overtraining risk. Injury, prolonged fatigue possible!'}",
        }
        return {'response': impacts.get(rtype, "❤️ Regular tracking se cardiovascular health, energy, sleep quality, aur mental clarity improve hoti hai!"), 'type': 'qa_answer'}

    def _predict_trend(self, rtype, data, raw):
        last7 = get_last_n_days(self.sid, 7)
        if len(last7) < 3:
            return {'response': f"🔮 Prediction ke liye 3+ din ka data chahiye. Abhi {len(last7)} din. Daily save karo!", 'type': 'qa_answer'}
        if rtype in ['steps_today','weekly_summary']:
            vals = [e['steps'] for e in last7 if e.get('steps')]
            if vals:
                avg = round(sum(vals)/len(vals)); trend = vals[-1]-vals[0] if len(vals)>1 else 0
                next_est = round(avg+(trend*0.3))
                return {'response': f"🔮 **Steps Prediction**\n\nLast {len(vals)} days avg: {avg:,}\nTrend: {'📈 Up' if trend>0 else '📉 Down'}\nNext week estimate: {next_est:,}/day\n\n{'✅ On track!' if next_est>=10000 else '💪 Consistency badhao!'}", 'type': 'qa_answer'}
        if rtype == 'weight_current':
            weights = [e['weight_kg'] for e in last7 if e.get('weight_kg')]
            if len(weights) >= 2:
                change = round((weights[-1]-weights[0])/len(weights),2)
                monthly = round(change*30,1)
                return {'response': f"⚖️ **Weight Prediction**\n\nDaily rate: {change:+} kg\nMonthly: {monthly:+} kg\n{'✅ Losing weight!' if change<0 else '⚠️ Weight badh raha hai!'}", 'type': 'qa_answer'}
        return {'response': "🔮 Current trend pe improvement expected hai. Consistency maintain karo! 💪", 'type': 'qa_answer'}

    def _contextual_default(self, rtype, question):
        return {
            'response': (
                f"💡 **'{question}'** ke baare mein:\n\n"
                f"Yeh poochh sakte ho:\n"
                f"  🔹 'Improve kaise karein?'\n"
                f"  🔹 'Last week se compare karo'\n"
                f"  🔹 'Goal kab achieve hoga?'\n"
                f"  🔹 'Yeh kyu zaroori hai?'\n"
                f"  🔹 'Health par kya effect hai?'\n"
                f"  🔹 'Next week prediction do'"
            ),
            'type': 'qa_hint'
        }