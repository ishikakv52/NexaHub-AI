"""
interview_engine.py — Premium AI Interview Simulator Engine
Handles: question generation, adaptive difficulty, answer evaluation, final report.
No external API required — uses dataset + smart heuristics.
"""

import re
import random
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
#  QUESTION BANKS
# ──────────────────────────────────────────────────────────────────────────────

HR_QUESTIONS = {
    "opening": [
        "Tell me about yourself.",
        "Walk me through your background and what brings you here today.",
        "Start by giving me a brief overview of your professional journey.",
    ],
    "strengths_weaknesses": [
        "What would you say are your top three strengths?",
        "Describe a weakness you've been actively working to improve.",
        "How would your previous manager describe you in three words?",
        "What do your colleagues typically come to you for help with?",
    ],
    "motivation": [
        "Why are you interested in this role?",
        "What motivated you to apply to our company specifically?",
        "Where do you see your career heading in the next five years?",
        "What does career growth mean to you?",
    ],
    "culture_fit": [
        "Describe your ideal work environment.",
        "How do you prefer to receive feedback?",
        "What kind of manager brings out your best work?",
        "How do you balance work and personal life?",
    ],
    "closing": [
        "What are your salary expectations?",
        "Do you have any questions for us?",
        "When would you be available to join?",
        "Is there anything else you'd like us to know about you?",
    ],
}

BEHAVIORAL_QUESTIONS = {
    "leadership": [
        "Tell me about a time when you took charge of a situation without being asked.",
        "Describe a situation where you led a team through a difficult challenge.",
        "Give me an example of when you had to influence someone without formal authority.",
    ],
    "conflict": [
        "Tell me about a time you had a disagreement with a colleague. How did you handle it?",
        "Describe a situation where you had to push back on your manager's decision.",
        "Give me an example of a difficult stakeholder you had to manage.",
    ],
    "problem_solving": [
        "Tell me about the most complex problem you've ever solved at work.",
        "Describe a situation where you had to make a decision with incomplete information.",
        "Give me an example of a time you identified a process inefficiency and fixed it.",
    ],
    "failure": [
        "Tell me about a significant mistake you made and what you learned from it.",
        "Describe a project that didn't go as planned and how you recovered.",
        "Give me an example of when you missed a deadline. What happened?",
    ],
    "achievement": [
        "What's the accomplishment you're most proud of in your career?",
        "Tell me about a time you exceeded your goals or targets.",
        "Describe a project that had a measurable positive impact on your organization.",
    ],
    "teamwork": [
        "Tell me about a time you collaborated with a difficult team member.",
        "Describe a project where teamwork was essential to the outcome.",
        "Give me an example of when you put the team's needs ahead of your own.",
    ],
}

TECHNICAL_QUESTIONS = {
    "general": [
        "Walk me through your technical background and your strongest areas.",
        "What technologies are you most comfortable with and why?",
        "Describe the most technically challenging project you've worked on.",
        "How do you stay updated with the latest developments in your field?",
        "Explain a complex technical concept you've mastered recently.",
    ],
    "problem_solving": [
        "How do you approach debugging a complex issue?",
        "Walk me through how you would design a system from scratch.",
        "Describe your process when you're given a task you've never done before.",
        "How do you prioritize tasks when everything seems urgent?",
    ],
    "code_quality": [
        "How do you ensure the quality of your code?",
        "What's your approach to code reviews?",
        "How do you handle technical debt?",
        "Describe your testing philosophy.",
    ],
    "collaboration": [
        "How do you document your work for future developers?",
        "Describe how you communicate technical concepts to non-technical stakeholders.",
        "How do you handle technical disagreements with peers?",
    ],
}

MIXED_QUESTION_POOL = (
    [q for qs in HR_QUESTIONS.values() for q in qs] +
    [q for qs in BEHAVIORAL_QUESTIONS.values() for q in qs] +
    [q for qs in TECHNICAL_QUESTIONS.values() for q in qs]
)

FOLLOWUP_TRIGGERS = {
    "python": "You mentioned Python — can you describe a specific project where you used it and the challenges you faced?",
    "javascript": "You mentioned JavaScript — what frameworks have you worked with and what do you prefer?",
    "java": "Since you mentioned Java, how do you handle memory management in your Java applications?",
    "machine learning": "You brought up machine learning — can you walk me through a model you built and how you evaluated it?",
    "deep learning": "You mentioned deep learning — what frameworks have you used and what challenges did you face?",
    "react": "You mentioned React — can you explain how you manage state in a large React application?",
    "sql": "You referenced SQL — can you walk me through a complex query you've written?",
    "team": "You mentioned teamwork — can you give me a specific example of how you resolved a disagreement within a team?",
    "leadership": "You mentioned leadership — can you tell me about a time you led without having the title or authority?",
    "project": "You mentioned a project — can you walk me through your specific role, the challenges, and the outcome?",
    "manager": "You mentioned your manager — how would you describe your working relationship and how did you handle any differences?",
    "deadline": "You mentioned deadlines — tell me about the tightest deadline you've ever worked under and how you managed it.",
    "customer": "You mentioned customers — describe the most challenging customer interaction you've had and how you resolved it.",
    "mistake": "You mentioned making a mistake — what specifically did you learn, and how did it change your approach going forward?",
    "startup": "You worked at a startup — how did you manage competing priorities and constant change?",
    "remote": "You mentioned remote work — how do you maintain productivity and collaboration when working remotely?",
    "agile": "You mentioned Agile — can you walk me through how your team implemented it and what worked or didn't?",
    "data": "You mentioned data — how do you ensure data quality and integrity in your work?",
    "api": "You mentioned APIs — can you walk me through how you designed or consumed a REST API?",
    "performance": "You mentioned performance — can you describe a specific optimization you made and how you measured the improvement?",
    "cloud": "You mentioned cloud — which cloud platform do you prefer and what services have you used most extensively?",
}

WEAK_ANSWER_PROMPTS = [
    "I appreciate that — could you be more specific? Give me a concrete example from your experience.",
    "That's a good start. Can you quantify the impact? What were the actual results?",
    "Interesting. Can you walk me through the exact steps you took in that situation?",
    "I'd like to dig deeper into that. What was the biggest challenge you faced, and how did you specifically overcome it?",
    "Could you use the STAR method here? Tell me the Situation, Task, Action, and Result.",
]

STRONG_ANSWER_ACKNOWLEDGMENTS = [
    "That's a strong answer. Let me push you a bit further — ",
    "Excellent. Building on that, ",
    "I like how you structured that response. Now, ",
    "Good. That shows solid experience. Let me ask you something more challenging — ",
]

# ──────────────────────────────────────────────────────────────────────────────
#  WORD LISTS FOR SCORING
# ──────────────────────────────────────────────────────────────────────────────

POWER_WORDS = {
    "accomplished", "achieved", "delivered", "implemented", "spearheaded",
    "developed", "built", "designed", "optimized", "launched", "managed",
    "led", "collaborated", "contributed", "innovated", "streamlined",
    "increased", "reduced", "improved", "transformed", "mentored",
    "coordinated", "executed", "established", "initiated", "resolved"
}

FILLER_WORDS = {
    "basically", "literally", "actually", "umm", "uhh", "like", "you know",
    "i mean", "sort of", "kind of", "stuff", "things", "etc",
    "i think maybe", "i'm not sure", "probably", "i guess"
}

WEAK_PHRASES = {
    "i don't know", "i have no idea", "never done this", "not sure about",
    "can't think of", "nothing comes to mind", "i haven't really"
}

STAR_INDICATORS = {
    "situation": ["when i was", "in my previous", "at my last", "there was a time", "i was working"],
    "task": ["my responsibility was", "i was tasked", "i needed to", "my role was", "i had to"],
    "action": ["i decided to", "i implemented", "i worked with", "i took the initiative", "i reached out", "i built", "i created"],
    "result": ["as a result", "this led to", "we achieved", "the outcome was", "we improved", "it resulted in", "we reduced", "we increased"]
}

PROFESSIONAL_PHRASES = {
    "take initiative", "result-oriented", "continuous learning", "stakeholder",
    "cross-functional", "deliverable", "bandwidth", "proactive", "synergy",
    "scalable", "agile", "iterative", "data-driven", "impact", "ownership"
}

GRAMMAR_PATTERNS = [
    (r"\bi done\b", "I did"),
    (r"\bI have went\b", "I have gone"),
    (r"\bwe was\b", "we were"),
    (r"\bthey was\b", "they were"),
    (r"\bhe have\b", "he has"),
    (r"\bshe have\b", "she has"),
    (r"\bdo the needful\b", "please take necessary action"),
    (r"\brevert back\b", "revert / reply back"),
    (r"\bprepone\b", "reschedule to an earlier time"),
    (r"\bkindy\b", "kindly"),
    (r"\bam knowing\b", "know"),
    (r"\bam understanding\b", "understand"),
    (r"\bam liking\b", "like"),
    (r"\bI am having\b", "I have"),
    (r"\bwould be doing\b", "will do"),
    (r"\bI am working since\b", "I have been working since"),
    (r"\bsince \d+ years\b", "for X years"),
    (r"\bpast experience\b", "experience (all experience is past)"),
]

# ──────────────────────────────────────────────────────────────────────────────
#  CORE ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def generate_first_question(interview_type: str, job_role: str, experience_level: str,
                             company: str, resume_text: str, jd_text: str) -> dict:
    """Generate the very first question and initialize interview state."""
    q = "Tell me about yourself."
    context = ""
    if company:
        context = f" I see you're interested in the {job_role} role at {company}."
    elif job_role:
        context = f" I understand you're applying for a {job_role} position."

    opener = random.choice([
        f"Thank you for joining us today.{context} Let's begin.",
        f"Welcome.{context} I'm glad you could make it. Let's get started.",
        f"Good to have you here.{context} Let's dive right in.",
    ])

    return {
        "interviewer_message": opener,
        "question": q,
        "question_number": 1,
        "question_type": "opening",
        "difficulty": "easy",
    }


def generate_next_question(interview_type: str, job_role: str, experience_level: str,
                            company: str, history: list, last_eval: dict,
                            asked_questions: list, resume_text: str, jd_text: str) -> Optional[dict]:
    """
    Generate the next question adaptively based on:
    - interview type, history, previous answer quality, asked questions
    Returns None if interview should end (10-15 questions reached).
    """
    q_count = len(asked_questions)

    # End interview after 10-15 questions
    if q_count >= 12:
        return None
    if q_count >= 10 and last_eval and last_eval.get("score", 5) >= 7:
        # Good performer — can end earlier gracefully
        if random.random() < 0.4:
            return None

    score = last_eval.get("score", 5) if last_eval else 5
    last_answer = ""
    for msg in reversed(history):
        if msg["role"] == "user":
            last_answer = msg["content"]
            break

    # Try follow-up question based on keywords in last answer
    if last_answer and q_count <= 10:
        la_lower = last_answer.lower()
        for keyword, followup_q in FOLLOWUP_TRIGGERS.items():
            if keyword in la_lower and followup_q not in asked_questions:
                prefix = ""
                if score >= 7:
                    prefix = random.choice(STRONG_ANSWER_ACKNOWLEDGMENTS)
                elif score <= 4:
                    prefix = random.choice(WEAK_ANSWER_PROMPTS) + " "
                return {
                    "interviewer_message": prefix,
                    "question": followup_q,
                    "question_number": q_count + 1,
                    "question_type": "followup",
                    "difficulty": "adaptive",
                }

    # Select from pool based on interview type
    pool = _get_question_pool(interview_type, q_count, score)
    available = [q for q in pool if q not in asked_questions]

    if not available:
        # Fallback to mixed pool
        available = [q for q in MIXED_QUESTION_POOL if q not in asked_questions]

    if not available:
        return None

    chosen = random.choice(available)

    # Build interviewer message
    prefix = ""
    if score <= 4 and last_answer:
        prefix = random.choice(WEAK_ANSWER_PROMPTS) + " Moving on — "
    elif score >= 8 and last_answer:
        prefix = random.choice(STRONG_ANSWER_ACKNOWLEDGMENTS)

    return {
        "interviewer_message": prefix,
        "question": chosen,
        "question_number": q_count + 1,
        "question_type": _classify_question(chosen),
        "difficulty": _get_difficulty(score, q_count),
    }


def _get_question_pool(interview_type: str, q_count: int, score: int) -> list:
    """Select appropriate question pool based on type and progress."""
    if interview_type == "hr":
        pools = list(HR_QUESTIONS.values())
    elif interview_type == "behavioral":
        pools = list(BEHAVIORAL_QUESTIONS.values())
    elif interview_type == "technical":
        pools = list(TECHNICAL_QUESTIONS.values())
    else:  # mixed
        if q_count < 3:
            pools = list(HR_QUESTIONS.values())
        elif q_count < 7:
            pools = list(BEHAVIORAL_QUESTIONS.values())
        else:
            pools = list(TECHNICAL_QUESTIONS.values())

    all_qs = [q for pool in pools for q in pool]
    return all_qs


def _classify_question(q: str) -> str:
    q_lower = q.lower()
    if any(w in q_lower for w in ["tell me about", "walk me through", "describe yourself"]):
        return "opening"
    if any(w in q_lower for w in ["time when", "example of", "situation where", "describe a"]):
        return "behavioral"
    if any(w in q_lower for w in ["technical", "code", "system", "design", "debug", "api"]):
        return "technical"
    if any(w in q_lower for w in ["strength", "weakness", "salary", "years"]):
        return "hr"
    return "general"


def _get_difficulty(score: int, q_count: int) -> str:
    if q_count < 3:
        return "easy"
    if score >= 8:
        return "hard"
    if score <= 4:
        return "easy"
    return "medium"


# ──────────────────────────────────────────────────────────────────────────────
#  ANSWER EVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_answer(question: str, answer: str, question_type: str,
                    interview_type: str, experience_level: str,
                    history: list) -> dict:
    """
    Comprehensive answer evaluation returning structured feedback.
    """
    answer_lower = answer.lower()
    words = answer.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]

    # ── Length Score ──
    if word_count < 20:
        length_score = 3
        length_fb = "Answer is too brief. Aim for at least 60-100 words."
    elif word_count < 50:
        length_score = 5
        length_fb = "Good start but expand more. Add specific examples and outcomes."
    elif word_count < 100:
        length_score = 7
        length_fb = "Good length. Adding measurable results would make it stronger."
    elif word_count <= 250:
        length_score = 9
        length_fb = "Excellent length — detailed yet focused."
    else:
        length_score = 7
        length_fb = "Slightly long. Practice being more concise while keeping key points."

    # ── Grammar Score ──
    grammar_issues = []
    for pattern, correction in GRAMMAR_PATTERNS:
        if re.search(pattern, answer, re.IGNORECASE):
            grammar_issues.append({"error": pattern.replace(r"\b", "").replace("\\", ""), "fix": correction})
    grammar_score = max(4, 10 - len(grammar_issues) * 2)

    # ── Vocabulary Score ──
    power_used = [w for w in POWER_WORDS if w in answer_lower]
    filler_found = [f for f in FILLER_WORDS if f in answer_lower]
    vocab_score = min(10, 5 + len(power_used) * 1 - len(filler_found) * 1)
    vocab_score = max(3, vocab_score)

    # ── STAR Method Score (for behavioral) ──
    star_score = 5
    star_hits = {}
    if question_type in ("behavioral", "general"):
        for component, indicators in STAR_INDICATORS.items():
            if any(ind in answer_lower for ind in indicators):
                star_hits[component] = True
        star_score = 3 + len(star_hits) * 1.5
        star_score = min(10, star_score)

    # ── Confidence Score ──
    weak_count = sum(1 for wp in WEAK_PHRASES if wp in answer_lower)
    confidence_score = max(3, 9 - weak_count * 2)

    # ── Professional Tone ──
    prof_phrases_used = [p for p in PROFESSIONAL_PHRASES if p in answer_lower]
    prof_score = min(10, 5 + len(prof_phrases_used) * 1)
    prof_score = max(4, prof_score)

    # ── Overall Score ──
    if question_type == "behavioral":
        overall = (grammar_score * 0.2 + vocab_score * 0.15 + star_score * 0.3
                   + confidence_score * 0.2 + length_score * 0.15)
    elif question_type == "technical":
        overall = (grammar_score * 0.15 + vocab_score * 0.15 + length_score * 0.2
                   + confidence_score * 0.15 + prof_score * 0.15 + star_score * 0.2)
    else:
        overall = (grammar_score * 0.2 + vocab_score * 0.2 + length_score * 0.2
                   + confidence_score * 0.2 + prof_score * 0.2)
    overall = round(min(10, max(1, overall)), 1)

    # ── Strengths ──
    strengths = []
    if word_count >= 80:
        strengths.append("Well-structured and detailed response")
    if power_used:
        strengths.append(f"Strong action words used: {', '.join(power_used[:3])}")
    if star_hits.get("result"):
        strengths.append("Mentioned results/outcomes — very impactful")
    if star_hits.get("action"):
        strengths.append("Clearly described the actions you took")
    if not filler_found:
        strengths.append("No filler words — sounds professional and confident")
    if prof_phrases_used:
        strengths.append(f"Professional vocabulary: {', '.join(prof_phrases_used[:2])}")
    if not strengths:
        strengths.append("You attempted to answer the question directly")

    # ── Weaknesses ──
    weaknesses = []
    if word_count < 50:
        weaknesses.append("Answer is too short — interviewers expect depth and examples")
    if grammar_issues:
        weaknesses.append(f"Grammar issues detected ({len(grammar_issues)} found)")
    if filler_found:
        weaknesses.append(f"Filler words used: '{', '.join(filler_found[:2])}' — avoid these")
    if not star_hits.get("result") and question_type == "behavioral":
        weaknesses.append("Missing results/impact — always quantify your achievements")
    if not star_hits.get("situation") and question_type == "behavioral":
        weaknesses.append("No specific situation mentioned — use the STAR method")
    if weak_count > 0:
        weaknesses.append("Uncertain language detected — sounds less confident")
    if not weaknesses:
        weaknesses.append("Minor: Could add more specific numbers/metrics for stronger impact")

    # ── Missing Points ──
    missing = []
    if question_type == "behavioral":
        missing_star = [k for k in ["situation", "task", "action", "result"] if k not in star_hits]
        if missing_star:
            missing.append(f"STAR components missing: {', '.join(missing_star).upper()}")
    if not any(char.isdigit() for char in answer):
        missing.append("No quantifiable metrics (e.g., '30% improvement', 'team of 5', '$2M project')")
    if word_count < 80 and question_type != "hr":
        missing.append("More context about your specific role and impact")
    if not any(w in answer_lower for w in ["i learned", "takeaway", "outcome", "result", "impact", "achieved"]):
        missing.append("What you learned or the final outcome")

    # ── Better Answer Structure ──
    better = _generate_better_answer_hint(question, question_type, star_hits, power_used)

    # ── Communication Feedback ──
    avg_sentence_len = word_count / max(1, len(sentences))
    if avg_sentence_len > 35:
        comm_fb = "Sentences are too long. Break them into shorter, clearer statements."
    elif avg_sentence_len < 8:
        comm_fb = "Sentences feel choppy. Connect your ideas for better flow."
    else:
        comm_fb = "Good sentence variety. Clear and easy to follow."

    # ── Grammar Feedback ──
    if grammar_issues:
        grammar_fb = "Issues found: " + "; ".join(
            [f'"{g["error"]}" → use "{g["fix"]}"' for g in grammar_issues[:3]]
        )
    else:
        grammar_fb = "No major grammar issues detected. Well done!"

    # ── Confidence Feedback ──
    if confidence_score >= 8:
        conf_fb = "Answer sounds confident and assertive. Great!"
    elif confidence_score >= 6:
        conf_fb = "Generally confident but avoid phrases like 'I think maybe' or 'I'm not sure.'"
    else:
        conf_fb = "Replace uncertain phrases with definitive statements. Own your experience!"

    return {
        "score": overall,
        "scores": {
            "grammar": grammar_score,
            "vocabulary": vocab_score,
            "confidence": confidence_score,
            "professionalism": prof_score,
            "structure": round(star_score, 1),
            "length": length_score,
        },
        "strengths": strengths[:3],
        "weaknesses": weaknesses[:3],
        "missing_points": missing[:3],
        "better_answer": better,
        "communication_feedback": comm_fb,
        "grammar_feedback": grammar_fb,
        "confidence_feedback": conf_fb,
        "word_count": word_count,
        "star_components_used": list(star_hits.keys()),
        "power_words_used": power_used[:5],
        "filler_words_found": filler_found[:3],
    }


def _generate_better_answer_hint(question: str, question_type: str, star_hits: dict, power_used: list) -> str:
    q_lower = question.lower()

    if "tell me about yourself" in q_lower:
        return (
            "Strong formula: 'I am a [role] with [X] years of experience in [domain]. "
            "At [Company], I [key achievement]. I specialize in [skill]. "
            "I'm excited about this role because [specific reason aligned with company].'"
        )

    if "strength" in q_lower:
        return (
            "Pick ONE strength + give a specific example. "
            "E.g.: 'My greatest strength is problem-solving. For instance, when [situation], "
            "I [action], which resulted in [measurable result].'"
        )

    if "weakness" in q_lower:
        return (
            "Choose a real weakness that's not critical for this role, then show growth. "
            "E.g.: 'I used to struggle with public speaking. I addressed this by [action]. "
            "Today I [evidence of improvement].'"
        )

    if question_type == "behavioral":
        missing_components = [k for k in ["situation", "task", "action", "result"] if k not in star_hits]
        if missing_components:
            return (
                f"Use the STAR method. Your answer is missing: {', '.join(missing_components).upper()}. "
                f"Structure: Situation → Task → Action → Result. "
                f"Always end with a measurable outcome: 'This resulted in a 25% improvement...' or 'The team delivered 2 weeks ahead of schedule.'"
            )
        return (
            "Good STAR structure! Strengthen it by quantifying your results: "
            "'increased revenue by X%', 'reduced time by Y hours', 'managed a team of Z people.'"
        )

    if "salary" in q_lower:
        return (
            "Research the market rate. Answer confidently with a range: "
            "'Based on my research and experience, I'm looking at [X-Y LPA]. "
            "I'm open to discussing based on the overall compensation package.'"
        )

    if "5 years" in q_lower or "future" in q_lower:
        return (
            "Show ambition + alignment with the company. "
            "E.g.: 'In five years, I see myself growing into a [senior role], "
            "contributing to [company goal]. I want to develop expertise in [area] "
            "and take on more leadership responsibility.'"
        )

    return (
        "Strengthen your answer with: (1) A specific example, "
        "(2) Quantifiable results, (3) What you personally did (use 'I' not 'we'), "
        "(4) End with the impact or lesson."
    )


# ──────────────────────────────────────────────────────────────────────────────
#  FINAL REPORT
# ──────────────────────────────────────────────────────────────────────────────

def generate_final_report(interview_type: str, job_role: str, company: str,
                           experience_level: str, evaluations: list,
                           questions: list) -> dict:
    """Generate a comprehensive final interview report."""

    if not evaluations:
        return {"error": "No evaluations to report on."}

    # ── Aggregate Scores ──
    avg_overall = sum(e["score"] for e in evaluations) / len(evaluations)

    score_dims = ["grammar", "vocabulary", "confidence", "professionalism", "structure"]
    dim_avgs = {}
    for dim in score_dims:
        vals = [e["scores"].get(dim, 5) for e in evaluations]
        dim_avgs[dim] = round(sum(vals) / len(vals), 1)

    # ── Communication Analysis ──
    total_words = sum(e.get("word_count", 0) for e in evaluations)
    avg_words = total_words // len(evaluations)

    all_power_words = []
    all_fillers = []
    for e in evaluations:
        all_power_words.extend(e.get("power_words_used", []))
        all_fillers.extend(e.get("filler_words_found", []))

    # ── Strengths Aggregation ──
    strength_counts = {}
    for e in evaluations:
        for s in e.get("strengths", []):
            strength_counts[s] = strength_counts.get(s, 0) + 1
    top_strengths = sorted(strength_counts, key=strength_counts.get, reverse=True)[:4]

    # ── Weaknesses Aggregation ──
    weakness_counts = {}
    for e in evaluations:
        for w in e.get("weaknesses", []):
            weakness_counts[w] = weakness_counts.get(w, 0) + 1
    top_weaknesses = sorted(weakness_counts, key=weakness_counts.get, reverse=True)[:4]

    # ── Skill Area Scores ──
    hr_score = round((dim_avgs["professionalism"] + dim_avgs["confidence"]) / 2, 1)
    tech_score = round((dim_avgs["structure"] + dim_avgs["vocabulary"]) / 2, 1)
    comm_score = round((dim_avgs["grammar"] + dim_avgs["vocabulary"]) / 2, 1)
    problem_solving_score = dim_avgs["structure"]

    # ── Areas to Improve ──
    improve = []
    if dim_avgs["grammar"] < 7:
        improve.append("Grammar accuracy — practice writing and get feedback regularly")
    if dim_avgs["confidence"] < 6:
        improve.append("Confidence in delivery — record yourself and practice out loud")
    if avg_words < 60:
        improve.append("Answer depth — expand your answers with specific STAR examples")
    if all_fillers:
        filler_unique = list(set(all_fillers))[:3]
        improve.append(f"Eliminate filler words: {', '.join(filler_unique)}")
    if dim_avgs["vocabulary"] < 6:
        improve.append("Professional vocabulary — learn and use industry-specific terms")
    if not improve:
        improve.append("Continue refining your storytelling with quantified results")

    # ── Top Mistakes ──
    mistakes = []
    for e in evaluations:
        if e.get("grammar_feedback") and "Issues found" in e.get("grammar_feedback", ""):
            mistakes.append(e["grammar_feedback"][:80])
        for filler in e.get("filler_words_found", []):
            mistakes.append(f"Used '{filler}' — avoid filler words")
        if e.get("word_count", 100) < 40:
            mistakes.append("Too brief — answers lacked sufficient detail")

    mistakes = list(dict.fromkeys(mistakes))[:5]  # deduplicate
    if not mistakes:
        mistakes = ["Keep adding quantified metrics to your answers for stronger impact"]

    # ── Recommended Topics ──
    recommended = _get_recommended_topics(interview_type, dim_avgs, top_weaknesses)

    # ── Hiring Recommendation ──
    avg_score = round(avg_overall, 1)
    if avg_score >= 7.5:
        hiring_rec = "Ready"
        hiring_msg = "Strong candidate — demonstrates clear communication, relevant experience, and professional confidence."
        hiring_color = "green"
    elif avg_score >= 5.5:
        hiring_rec = "Needs Improvement"
        hiring_msg = "Shows potential but needs to strengthen answer structure, add specific examples, and improve confidence."
        hiring_color = "yellow"
    else:
        hiring_rec = "Not Ready"
        hiring_msg = "Significant improvement needed in communication, grammar, and answer depth before moving forward."
        hiring_color = "red"

    return {
        "overall_score": avg_score,
        "total_questions": len(evaluations),
        "skill_scores": {
            "hr_skills": hr_score,
            "technical_skills": tech_score,
            "communication": comm_score,
            "grammar": dim_avgs["grammar"],
            "confidence": dim_avgs["confidence"],
            "problem_solving": problem_solving_score,
            "professionalism": dim_avgs["professionalism"],
        },
        "strengths": top_strengths,
        "weaknesses": top_weaknesses,
        "areas_to_improve": improve[:4],
        "top_mistakes": mistakes[:4],
        "recommended_topics": recommended,
        "hiring_recommendation": hiring_rec,
        "hiring_message": hiring_msg,
        "hiring_color": hiring_color,
        "stats": {
            "avg_words_per_answer": avg_words,
            "power_words_used": list(set(all_power_words))[:8],
            "filler_words_total": len(all_fillers),
        },
        "summary": _build_summary(avg_score, interview_type, job_role, company,
                                   len(evaluations), dim_avgs, hiring_rec),
    }


def _get_recommended_topics(interview_type: str, dim_avgs: dict, weaknesses: list) -> list:
    topics = []
    if dim_avgs.get("grammar", 10) < 7:
        topics.append("English Grammar Fundamentals — Articles, Tenses, Subject-Verb Agreement")
    if interview_type in ("behavioral", "mixed"):
        topics.append("STAR Method Mastery — Structuring behavioral answers effectively")
    if dim_avgs.get("confidence", 10) < 6:
        topics.append("Public Speaking & Confident Delivery — Record and review yourself")
    if interview_type in ("hr", "mixed"):
        topics.append("Company Research Framework — How to research and connect with company values")
    topics.append("Professional Vocabulary — Power words and industry-specific terms")
    topics.append("Salary Negotiation Techniques — Know your worth and negotiate effectively")
    if interview_type in ("technical", "mixed"):
        topics.append("System Design Basics — Practice explaining technical concepts simply")
    return topics[:5]


def _build_summary(score: float, itype: str, role: str, company: str,
                   q_count: int, dim_avgs: dict, recommendation: str) -> str:
    role_str = f"the {role} role" if role else "this role"
    company_str = f" at {company}" if company else ""

    if score >= 7.5:
        return (
            f"Overall, this was a strong performance across {q_count} questions for {role_str}{company_str}. "
            f"You demonstrated clear communication and relevant experience. "
            f"Your confidence ({dim_avgs['confidence']}/10) and professionalism ({dim_avgs['professionalism']}/10) "
            f"were particular highlights. To take it to the next level, focus on adding quantifiable "
            f"results to your answers and vary your sentence structure for better impact."
        )
    elif score >= 5.5:
        return (
            f"A decent showing across {q_count} questions for {role_str}{company_str}, "
            f"but there's room to grow. Your answers showed some good moments, but lacked "
            f"consistent structure and specific examples. Work on the STAR method for behavioral "
            f"questions and aim for answers in the 80-150 word range. "
            f"Grammar ({dim_avgs['grammar']}/10) and confidence ({dim_avgs['confidence']}/10) "
            f"are your key areas to develop."
        )
    else:
        return (
            f"The {q_count}-question session for {role_str}{company_str} revealed areas needing "
            f"significant attention. Focus first on answer structure — use STAR method consistently. "
            f"Practice speaking in complete, confident sentences. Address grammar basics, "
            f"eliminate filler words, and build professional vocabulary. "
            f"Daily practice of 2-3 mock questions will show measurable improvement within weeks."
        )