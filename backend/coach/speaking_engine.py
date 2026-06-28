"""
speaking_engine.py — AI Speaking Coach Engine
Premium multi-mode speaking practice with deep analysis.
Uses local dataset + structured AI-like analysis. No external API needed.
"""
import re
import random
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# SPEAKING MODES
# ─────────────────────────────────────────────────────────────────
SPEAKING_MODES = {
    "daily_conversation": {
        "title": "Daily Conversation",
        "emoji": "☀️",
        "desc": "Practice everyday English naturally",
        "color": "#f59e0b",
        "system_persona": "friendly neighbor catching up",
        "difficulty": "beginner",
        "topics": [
            "What did you do today?",
            "How was your morning?",
            "What are you having for dinner?",
            "Did you watch anything interesting recently?",
            "How's the weather where you are?",
            "What's your weekend plan?",
        ],
        "follow_ups": [
            "That sounds interesting! Tell me more.",
            "Really? How did that make you feel?",
            "What happened next?",
            "Did anyone else join you?",
            "Would you do it again?",
        ],
        "focus": ["natural flow", "common phrases", "casual vocabulary"],
    },
    "casual_conversation": {
        "title": "Casual Conversation",
        "emoji": "😊",
        "desc": "Relax and chat like with a friend",
        "color": "#10b981",
        "system_persona": "close friend",
        "difficulty": "beginner",
        "topics": [
            "What's your favorite way to spend a lazy Sunday?",
            "If you could eat one meal forever, what would it be?",
            "What's the funniest thing that happened to you recently?",
            "Do you prefer mornings or nights? Why?",
            "What's your go-to comfort food?",
        ],
        "follow_ups": [
            "Ha! That's so relatable. Same for me when...",
            "No way! I didn't expect that. What did you do?",
            "I love that! Have you always been like that?",
            "That's so you! Tell me the full story.",
        ],
        "focus": ["informal language", "storytelling", "expressing opinions"],
    },
    "professional_conversation": {
        "title": "Professional Conversation",
        "emoji": "💼",
        "desc": "Master workplace English",
        "color": "#3b82f6",
        "system_persona": "experienced professional colleague",
        "difficulty": "intermediate",
        "topics": [
            "Walk me through your current role and responsibilities.",
            "How do you handle tight deadlines and competing priorities?",
            "Describe a successful project you led recently.",
            "How do you communicate complex ideas to non-technical stakeholders?",
            "What does your ideal work environment look like?",
        ],
        "follow_ups": [
            "Interesting approach. What metrics did you use to measure success?",
            "How did the team respond to that?",
            "What would you do differently if you could do it again?",
            "That's a strong example. How has that shaped your work style?",
        ],
        "focus": ["professional vocabulary", "clarity", "structured thinking"],
    },
    "interview_speaking": {
        "title": "Interview Speaking",
        "emoji": "🎯",
        "desc": "Ace your next job interview",
        "color": "#8b5cf6",
        "system_persona": "senior hiring manager",
        "difficulty": "intermediate",
        "topics": [
            "Tell me about yourself and your background.",
            "Why are you interested in this role?",
            "Describe a challenge you overcame at work.",
            "Where do you see yourself in 5 years?",
            "What's your greatest professional strength?",
            "Tell me about a time you failed and what you learned.",
        ],
        "follow_ups": [
            "Can you give me a specific example of that?",
            "What was the measurable outcome?",
            "How did that experience change your approach?",
            "What would your previous manager say about you?",
        ],
        "focus": ["STAR method", "confidence", "specific examples", "professional tone"],
    },
    "public_speaking": {
        "title": "Public Speaking",
        "emoji": "🎤",
        "desc": "Build stage presence and confidence",
        "color": "#ef4444",
        "system_persona": "public speaking coach",
        "difficulty": "advanced",
        "topics": [
            "Give a 2-minute speech on why education is important.",
            "Persuade me to try a hobby you love.",
            "Speak on the impact of social media on youth.",
            "Deliver an inspiring message on overcoming failure.",
            "Talk about a leader who changed the world.",
        ],
        "follow_ups": [
            "Strong opening. Now strengthen your core argument.",
            "Good point. Can you back that with a real example?",
            "Your conclusion needs more impact. How can you leave them inspired?",
            "That statistic is powerful. Did you explain its significance?",
        ],
        "focus": ["structure", "rhetoric", "impact", "audience engagement"],
    },
    "story_telling": {
        "title": "Story Telling",
        "emoji": "📖",
        "desc": "Narrate stories with vivid English",
        "color": "#f97316",
        "system_persona": "writing mentor",
        "difficulty": "intermediate",
        "topics": [
            "Tell me about the most memorable day of your life.",
            "Narrate a funny childhood memory.",
            "Describe a time when you helped someone.",
            "Tell a story about an unexpected adventure.",
            "Share a moment when you were truly proud of yourself.",
        ],
        "follow_ups": [
            "What a scene! Paint the setting for me — where exactly were you?",
            "The plot thickens! What did you feel in that moment?",
            "I didn't see that coming. How did others react?",
            "What's the lesson you took from that story?",
        ],
        "focus": ["narrative arc", "descriptive language", "emotional expression", "tense consistency"],
    },
    "debate_practice": {
        "title": "Debate Practice",
        "emoji": "⚖️",
        "desc": "Argue, persuade, and think critically",
        "color": "#dc2626",
        "system_persona": "debate opponent who challenges your points",
        "difficulty": "advanced",
        "topics": [
            "Social media does more harm than good.",
            "Remote work is better than office work.",
            "Smartphones should be banned in schools.",
            "AI will take more jobs than it creates.",
            "Online education is better than traditional classrooms.",
        ],
        "follow_ups": [
            "I respectfully disagree. Have you considered the other side?",
            "That's a fair point, but what about those who argue...",
            "You need stronger evidence. Can you cite a real example?",
            "Good argument! Now address the counterargument.",
        ],
        "focus": ["logical argumentation", "counterarguments", "persuasive language", "evidence use"],
    },
    "role_play": {
        "title": "Role Play",
        "emoji": "🎭",
        "desc": "Practice real-life English scenarios",
        "color": "#06b6d4",
        "system_persona": "role-play partner",
        "difficulty": "intermediate",
        "topics": [
            "You are complaining to a hotel manager about your room.",
            "You are calling a customer service rep about a billing error.",
            "You are negotiating a salary raise with your manager.",
            "You are asking your doctor about test results.",
            "You are explaining a project delay to your team lead.",
        ],
        "follow_ups": [
            "I understand your concern. Let me check what I can do.",
            "That's a valid point. Can you clarify what exactly happened?",
            "I'm listening. What outcome are you looking for?",
            "Let's work through this together. What's your proposal?",
        ],
        "focus": ["formal requests", "polite assertiveness", "problem-solving language"],
    },
    "group_discussion": {
        "title": "Group Discussion",
        "emoji": "👥",
        "desc": "Lead and participate in discussions",
        "color": "#84cc16",
        "system_persona": "group discussion moderator",
        "difficulty": "intermediate",
        "topics": [
            "The government should invest more in renewable energy.",
            "Mental health should be part of school curriculum.",
            "India should focus on manufacturing over IT services.",
            "Electric vehicles are the future of transportation.",
            "Should the voting age be lowered to 16?",
        ],
        "follow_ups": [
            "Great perspective! Does anyone want to add to that?",
            "Interesting view. How does the group feel about this?",
            "Good analysis. Can you provide a real-world example?",
            "You raised an important point. What's your recommendation?",
        ],
        "focus": ["turn-taking", "building on others' ideas", "diplomatic language", "leadership"],
    },
    "picture_description": {
        "title": "Picture Description",
        "emoji": "🖼️",
        "desc": "Describe scenes with rich vocabulary",
        "color": "#a855f7",
        "system_persona": "art and language instructor",
        "difficulty": "intermediate",
        "topics": [
            "Describe a busy street market you've seen or imagined.",
            "Describe your ideal home or room in detail.",
            "Describe a beautiful landscape — mountains, beach, or forest.",
            "Describe a family gathering scene.",
            "Describe a futuristic city as you imagine it.",
        ],
        "follow_ups": [
            "Vivid! Now tell me about the people in the scene.",
            "Good visual detail. What sounds might you hear there?",
            "What emotions does this scene evoke in you?",
            "Describe the light and atmosphere more specifically.",
        ],
        "focus": ["descriptive vocabulary", "spatial language", "sensory details", "adjective use"],
    },
    "ielts_speaking": {
        "title": "IELTS Speaking",
        "emoji": "🏆",
        "desc": "Prepare for IELTS Band 7+",
        "color": "#0891b2",
        "system_persona": "IELTS examiner",
        "difficulty": "advanced",
        "topics": [
            "Part 1: Tell me about your hometown.",
            "Part 1: Do you enjoy reading? What kind of books?",
            "Part 2: Describe a person who has influenced you greatly.",
            "Part 2: Describe a journey that was particularly memorable.",
            "Part 3: How has technology changed the way people communicate?",
            "Part 3: Do you think traditional values are still important today?",
        ],
        "follow_ups": [
            "Good. Could you elaborate on that point?",
            "You mentioned [topic]. Could you give an example?",
            "How might this differ in other countries?",
            "What are the long-term implications of this trend?",
        ],
        "focus": ["band 7+ vocabulary", "coherence", "complex grammar", "topic development"],
    },
    "random_topics": {
        "title": "Random Topics",
        "emoji": "🎲",
        "desc": "Surprise topics to test versatility",
        "color": "#d4af37",
        "system_persona": "curious conversation partner",
        "difficulty": "mixed",
        "topics": [
            "If you could have any superpower, what would it be and why?",
            "What invention from the last 50 years changed life the most?",
            "If you could live in any era of history, which would you choose?",
            "What's one thing you wish everyone knew?",
            "If animals could talk, which would be the rudest?",
            "What would you do with 24 hours of complete freedom?",
            "What skill would you most like to master?",
        ],
        "follow_ups": [
            "Fascinating take! What made you think of that angle?",
            "Ha, I like that! Have you always felt this way?",
            "Interesting! What would be the downside of that?",
            "Most people say something else. You're original!",
        ],
        "focus": ["spontaneity", "creativity", "natural expression", "fluency"],
    },
}

# ─────────────────────────────────────────────────────────────────
# FILLER WORDS & PATTERNS
# ─────────────────────────────────────────────────────────────────
FILLER_WORDS = [
    r'\buh\b', r'\bumm?\b', r'\buhh\b', r'\bhmm\b',
    r'\blike\b', r'\byou know\b', r'\bactually\b',
    r'\bbasically\b', r'\bright\b', r'\bokay so\b',
    r'\bkinda\b', r'\bsorta\b', r'\bi mean\b',
    r'\bwhatever\b', r'\banyway\b', r'\bso like\b',
]

# Common grammar mistakes (Indian English patterns)
GRAMMAR_PATTERNS = [
    {
        "wrong_pattern": r'\bI am having\b',
        "correct": "I have",
        "rule": "Stative verbs don't use continuous tense",
        "example": "I have a question. (Not: I am having a question)",
        "category": "stative_verbs"
    },
    {
        "wrong_pattern": r'\bdo the needful\b',
        "correct": "take care of this / handle this",
        "rule": "'Do the needful' is an Indian English expression not used in standard English",
        "example": "Please take care of this. (Not: Please do the needful)",
        "category": "indianism"
    },
    {
        "wrong_pattern": r'\bprepone\b',
        "correct": "reschedule to an earlier time / move up",
        "rule": "'Prepone' is not a standard English word",
        "example": "Can we move the meeting up? (Not: Can we prepone it?)",
        "category": "indianism"
    },
    {
        "wrong_pattern": r'\bdiscuss about\b',
        "correct": "discuss",
        "rule": "'Discuss' is transitive — no 'about' needed",
        "example": "We discussed the plan. (Not: We discussed about the plan)",
        "category": "preposition"
    },
    {
        "wrong_pattern": r'\brevert back\b',
        "correct": "revert / respond / reply",
        "rule": "'Revert' already means to go back — 'back' is redundant",
        "example": "Please revert by Friday. (Not: Please revert back)",
        "category": "redundancy"
    },
    {
        "wrong_pattern": r'\bI was went\b',
        "correct": "I went",
        "rule": "Past tense of 'go' is 'went' — no auxiliary needed",
        "example": "I went to the market. (Not: I was went)",
        "category": "tense"
    },
    {
        "wrong_pattern": r'\bsince (\d+ years?|long|many)\b',
        "correct": "for [duration]",
        "rule": "Use 'for' with durations, 'since' with specific points in time",
        "example": "I have been here for two years. (Not: since two years)",
        "category": "preposition"
    },
    {
        "wrong_pattern": r'\bmy self\b',
        "correct": "myself",
        "rule": "'Myself' is one word",
        "example": "I will do it myself. (Not: my self)",
        "category": "spelling"
    },
    {
        "wrong_pattern": r'\bwould you mind to\b',
        "correct": "would you mind + gerund (-ing)",
        "rule": "'Mind' is followed by a gerund, not an infinitive",
        "example": "Would you mind helping me? (Not: Would you mind to help?)",
        "category": "gerund"
    },
    {
        "wrong_pattern": r'\b(she|he) don\'t\b',
        "correct": "she doesn't / he doesn't",
        "rule": "Third-person singular requires 'doesn't'",
        "example": "She doesn't know. (Not: She don't know)",
        "category": "subject_verb_agreement"
    },
]

# Vocabulary upgrade suggestions
VOCAB_UPGRADES = {
    "good": ["excellent", "outstanding", "remarkable", "commendable"],
    "bad": ["challenging", "difficult", "problematic", "concerning"],
    "very": ["extremely", "particularly", "exceptionally", "considerably"],
    "big": ["substantial", "significant", "considerable", "extensive"],
    "small": ["minimal", "marginal", "modest", "limited"],
    "said": ["mentioned", "noted", "explained", "emphasized", "highlighted"],
    "think": ["believe", "consider", "feel", "perceive", "understand"],
    "get": ["obtain", "acquire", "receive", "achieve", "gain"],
    "make": ["create", "develop", "establish", "produce", "generate"],
    "show": ["demonstrate", "illustrate", "reveal", "indicate", "present"],
    "help": ["assist", "support", "facilitate", "enable", "guide"],
    "use": ["utilize", "employ", "leverage", "apply", "implement"],
    "want": ["desire", "aspire to", "aim for", "seek", "intend"],
    "need": ["require", "necessitate", "demand", "call for"],
    "start": ["initiate", "commence", "launch", "begin", "undertake"],
    "end": ["conclude", "finalize", "complete", "accomplish"],
    "important": ["crucial", "vital", "essential", "significant", "critical"],
    "happy": ["thrilled", "delighted", "elated", "pleased", "gratified"],
    "sad": ["disheartened", "disappointed", "melancholy", "somber"],
    "interesting": ["fascinating", "compelling", "intriguing", "engaging"],
    "problem": ["challenge", "obstacle", "hurdle", "issue", "concern"],
}

# Pronunciation difficult words by category
PRONUNCIATION_TRICKY = {
    "commonly_mispronounced": [
        {"word": "comfortable", "wrong": "com-for-ta-ble", "right": "CUMF-ter-bul", "tip": "Drop the 'or' sound"},
        {"word": "specifically", "wrong": "spe-si-fi-clee", "right": "speh-SIF-ik-lee", "tip": "Stress the second syllable"},
        {"word": "pronunciation", "wrong": "pro-NOUN-ciation", "right": "pruh-nun-see-AY-shun", "tip": "No 'noun' sound — it's 'nun'"},
        {"word": "entrepreneur", "wrong": "en-treh-preh-NOOR", "right": "on-truh-pruh-NUR", "tip": "Silent 't' at the end"},
        {"word": "hierarchy", "wrong": "high-ARCH-ee", "right": "HI-er-ar-kee", "tip": "Three syllables, not two"},
        {"word": "February", "wrong": "Feb-yoo-air-ee", "right": "FEB-roo-air-ee", "tip": "Don't drop the first 'r'"},
        {"word": "statistics", "wrong": "sta-TIS-tics", "right": "stuh-TIS-tiks", "tip": "The plural has a /s/ sound at end"},
        {"word": "miscellaneous", "wrong": "mis-cel-LANE-ee-us", "right": "mis-uh-LAY-nee-us", "tip": "The 'c' is silent in the middle"},
        {"word": "colleague", "wrong": "col-EEG", "right": "KOL-eeg", "tip": "Stress the first syllable"},
        {"word": "apparently", "wrong": "ap-par-ENT-ly", "right": "uh-PAIR-ent-lee", "tip": "Stress is on PAIR, not ENT"},
    ]
}

# Confidence coaching patterns
CONFIDENCE_ISSUES = {
    "very_short": {
        "threshold": 30,  # words
        "feedback": "Your response was quite brief. Confident speakers elaborate on their points. Try to expand each idea with an example or explanation.",
        "suggestion": "Add the phrase 'For example...' or 'What I mean is...' to elaborate naturally."
    },
    "very_long_sentences": {
        "pattern": r'[^.!?]+[^.!?]{200}',
        "feedback": "You tend to speak in very long sentences. Pausing more often sounds more confident and is easier to follow.",
        "suggestion": "Practice using shorter sentences: say one idea, pause, then continue."
    },
    "repetitive_words": {
        "threshold": 3,  # same word used 3+ times
        "feedback": "Repeating the same words frequently is a sign of vocabulary limitation. Vary your expressions.",
        "suggestion": "Use a synonym or phrase the idea differently each time."
    },
    "incomplete_thoughts": {
        "pattern": r'\b(actually|basically|I mean|like)\b.*\b(actually|basically|I mean|like)\b',
        "feedback": "Overusing fillers suggests hesitation. Replace fillers with a brief pause — silence is more powerful.",
        "suggestion": "Practice saying your thought completely before speaking. Think → Pause → Speak."
    }
}

# ─────────────────────────────────────────────────────────────────
# CORE ANALYSIS ENGINE
# ─────────────────────────────────────────────────────────────────

def detect_fillers(text: str) -> dict:
    """Detect filler words and return analysis."""
    text_lower = text.lower()
    found_fillers = []
    filler_count = 0
    
    for pattern in FILLER_WORDS:
        matches = re.findall(pattern, text_lower)
        if matches:
            word = pattern.replace(r'\b', '').strip()
            found_fillers.append({"word": word, "count": len(matches)})
            filler_count += len(matches)
    
    word_count = len(text.split())
    filler_ratio = (filler_count / max(word_count, 1)) * 100
    
    return {
        "fillers_found": found_fillers,
        "total_count": filler_count,
        "ratio": round(filler_ratio, 1),
        "level": "Low" if filler_ratio < 5 else ("Medium" if filler_ratio < 12 else "High")
    }


def detect_grammar_issues(text: str) -> list:
    """Detect grammar mistakes and return structured corrections."""
    issues = []
    for pattern in GRAMMAR_PATTERNS:
        if re.search(pattern["wrong_pattern"], text, re.IGNORECASE):
            match = re.search(pattern["wrong_pattern"], text, re.IGNORECASE)
            wrong_text = match.group(0) if match else pattern["wrong_pattern"]
            issues.append({
                "original": wrong_text,
                "corrected": pattern["correct"],
                "rule": pattern["rule"],
                "example": pattern["example"],
                "category": pattern["category"]
            })
    return issues[:3]  # Max 3 corrections per turn


def suggest_vocabulary(text: str) -> list:
    """Suggest better vocabulary for basic words used."""
    suggestions = []
    words = re.findall(r'\b\w+\b', text.lower())
    used_suggestions = set()
    
    for word in words:
        if word in VOCAB_UPGRADES and word not in used_suggestions:
            alternatives = VOCAB_UPGRADES[word]
            suggestions.append({
                "basic_word": word,
                "alternatives": alternatives[:3],
                "best_alternative": alternatives[0]
            })
            used_suggestions.add(word)
            if len(suggestions) >= 3:
                break
    
    return suggestions


def detect_pronunciation_challenges(text: str) -> list:
    """Identify difficult words in the text."""
    challenges = []
    text_lower = text.lower()
    
    for item in PRONUNCIATION_TRICKY["commonly_mispronounced"]:
        if item["word"].lower() in text_lower:
            challenges.append(item)
    
    return challenges[:2]


def calculate_scores(text: str, mode: str = "daily_conversation") -> dict:
    """Calculate speaking scores across multiple dimensions."""
    words = text.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Word count score (ideal: 80-200 words)
    if word_count < 20:
        length_score = 3
    elif word_count < 50:
        length_score = 5
    elif word_count < 80:
        length_score = 7
    elif word_count <= 200:
        length_score = 9
    else:
        length_score = 8
    
    # Grammar score (based on detected issues)
    grammar_issues = detect_grammar_issues(text)
    grammar_score = max(5, 10 - len(grammar_issues) * 2)
    
    # Filler analysis
    filler_data = detect_fillers(text)
    filler_score = 10 if filler_data["level"] == "Low" else (7 if filler_data["level"] == "Medium" else 4)
    
    # Vocabulary score (check for basic words)
    vocab_suggestions = suggest_vocabulary(text)
    vocab_score = max(5, 10 - len(vocab_suggestions))
    
    # Fluency score (sentence variety)
    avg_sentence_length = word_count / max(len(sentences), 1)
    if 8 <= avg_sentence_length <= 20:
        fluency_score = 8
    elif avg_sentence_length < 5:
        fluency_score = 5
    else:
        fluency_score = 7
    
    # Confidence score (combined)
    confidence_score = (filler_score + min(9, length_score) + 7) // 3
    
    # Pronunciation (estimated)
    pronunciation_challenges = detect_pronunciation_challenges(text)
    pronunciation_score = max(6, 10 - len(pronunciation_challenges))
    
    # Mode-based adjustments
    difficulty = SPEAKING_MODES.get(mode, {}).get("difficulty", "intermediate")
    base_boost = {"beginner": 1, "intermediate": 0, "advanced": -1, "mixed": 0}.get(difficulty, 0)
    
    def adj(score):
        return min(10, max(1, score + base_boost))
    
    overall = round((grammar_score + fluency_score + vocab_score + confidence_score + pronunciation_score) / 5, 1)
    
    return {
        "overall": adj(overall),
        "grammar": adj(grammar_score),
        "fluency": adj(fluency_score),
        "vocabulary": adj(vocab_score),
        "pronunciation": adj(pronunciation_score),
        "confidence": adj(confidence_score),
        "word_count": word_count,
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sentence_length, 1),
    }


def generate_versions(text: str, mode: str) -> dict:
    """Generate better, native, and professional versions of the response."""
    # Extract the core meaning and return template versions
    word_count = len(text.split())
    
    better = _make_better_version(text)
    native = _make_native_version(text)
    professional = _make_professional_version(text)
    
    return {
        "better": better,
        "native": native,
        "professional": professional
    }


def _make_better_version(text: str) -> str:
    """Create a slightly improved version."""
    # Fix common issues and add connectors
    improved = text
    improved = re.sub(r'\bI am having\b', 'I have', improved, flags=re.IGNORECASE)
    improved = re.sub(r'\bdiscuss about\b', 'discuss', improved, flags=re.IGNORECASE)
    improved = re.sub(r'\brevert back\b', 'revert', improved, flags=re.IGNORECASE)
    improved = re.sub(r'\bprepone\b', 'reschedule to an earlier time', improved, flags=re.IGNORECASE)
    
    # Add transition if missing
    if not any(t in improved.lower() for t in ["firstly", "moreover", "however", "additionally", "furthermore"]):
        improved = improved.strip()
        if improved and not improved.endswith('.'):
            improved += '.'
    
    return improved.strip()


def _make_native_version(text: str) -> str:
    """Create a native-speaker style version (shorter, more natural)."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > 3:
        # Take key sentences and make them flow naturally
        core = '. '.join(sentences[:3])
    else:
        core = text
    
    # Native speakers use contractions
    native = core
    native = re.sub(r'\bI am\b', "I'm", native)
    native = re.sub(r'\bI have\b', "I've", native)
    native = re.sub(r'\bI will\b', "I'll", native)
    native = re.sub(r'\bdo not\b', "don't", native, flags=re.IGNORECASE)
    native = re.sub(r'\bdoes not\b', "doesn't", native, flags=re.IGNORECASE)
    native = re.sub(r'\bit is\b', "it's", native, flags=re.IGNORECASE)
    
    return native.strip() if native.strip() else text


def _make_professional_version(text: str) -> str:
    """Create a formal, professional version."""
    prof = text
    # Upgrade basic words
    replacements = {
        r'\bgood\b': 'excellent',
        r'\bvery\b': 'particularly',
        r'\bget\b': 'obtain',
        r'\buse\b': 'utilize',
        r'\bhelp\b': 'assist',
        r'\bshow\b': 'demonstrate',
        r'\bstart\b': 'initiate',
    }
    for pattern, replacement in replacements.items():
        prof = re.sub(pattern, replacement, prof, flags=re.IGNORECASE, count=1)
    
    return prof.strip()


def get_ai_response(mode: str, user_message: str, conversation_history: list, turn_number: int) -> str:
    """Generate a conversational AI response as a speaking partner."""
    mode_config = SPEAKING_MODES.get(mode, SPEAKING_MODES["daily_conversation"])
    
    # Select appropriate follow-up
    follow_ups = mode_config.get("follow_ups", ["Interesting! Tell me more."])
    
    # Analyze the user's response
    word_count = len(user_message.split())
    filler_data = detect_fillers(user_message)
    
    # Build a contextual response
    if turn_number == 0:
        # First turn — introduce the topic
        topic = random.choice(mode_config["topics"])
        if mode == "ielts_speaking":
            response = f"Good. I'd like to begin. {topic} Please give a full answer."
        elif mode == "debate_practice":
            response = f"Let's begin our debate. The motion is: '{topic}'. Please give your opening argument."
        elif mode == "interview_speaking":
            response = f"Thank you for joining us today. Let's start. {topic}"
        elif mode == "role_play":
            response = f"Let's begin the scenario. {topic} — Go ahead when you're ready."
        else:
            response = f"{topic}"
        return response
    
    # Follow-up based on what the user said
    if word_count < 20:
        # Too short — encourage more
        follow_up = random.choice([
            "That's a start! Can you tell me a bit more? I'd love to hear the details.",
            "Interesting! What else can you add to that? Give me a full picture.",
            "Good beginning! Expand on that thought a little more.",
        ])
    elif word_count > 250:
        # Too long — redirect
        follow_up = random.choice([
            "You've made several good points! Let me ask you a specific one: " + random.choice(follow_ups),
            "Great depth! To focus our conversation: " + random.choice(follow_ups),
        ])
    else:
        follow_up = random.choice(follow_ups)
    
    # Mode-specific response style
    if mode == "debate_practice":
        counter = random.choice([
            "You make a point, but critics would argue the opposite. How do you respond to that?",
            "That's one view. However, studies show the contrary in many cases. Can you defend your stance further?",
            "Interesting! But isn't it also true that... " + random.choice(follow_ups),
        ])
        return counter
    
    if mode == "ielts_speaking":
        examiner_responses = [
            follow_up,
            f"Thank you. {follow_up}",
            f"I see. {follow_up}",
            f"Right. Now, {follow_up}",
        ]
        return random.choice(examiner_responses)
    
    return follow_up


def generate_full_analysis(mode: str, user_message: str, turn_number: int, session_issues: dict) -> dict:
    """Generate complete feedback for a user's speaking turn."""
    scores = calculate_scores(user_message, mode)
    grammar_issues = detect_grammar_issues(user_message)
    vocab_suggestions = suggest_vocabulary(user_message)
    filler_data = detect_fillers(user_message)
    pronunciation = detect_pronunciation_challenges(user_message)
    versions = generate_versions(user_message, mode)
    
    # Short feedback based on scores
    overall = scores["overall"]
    if overall >= 9:
        short_feedback = "Excellent response! Natural, confident, and well-structured."
    elif overall >= 7:
        short_feedback = "Good speaking! A few small improvements will make it sound even more natural."
    elif overall >= 5:
        short_feedback = "Nice effort! Focus on vocabulary variety and reducing fillers."
    else:
        short_feedback = "Keep practicing! Try to speak in complete sentences and expand your answers."
    
    # Track session-level recurring issues
    if grammar_issues:
        for issue in grammar_issues:
            cat = issue["category"]
            session_issues["grammar"][cat] = session_issues["grammar"].get(cat, 0) + 1
    
    if filler_data["total_count"] > 2:
        session_issues["fillers"] = session_issues.get("fillers", 0) + filler_data["total_count"]
    
    if scores["word_count"] < 40:
        session_issues["short_answers"] = session_issues.get("short_answers", 0) + 1
    
    return {
        "scores": scores,
        "short_feedback": short_feedback,
        "grammar_issues": grammar_issues,
        "vocab_suggestions": vocab_suggestions,
        "filler_data": filler_data,
        "pronunciation_challenges": pronunciation,
        "versions": versions,
        "session_issues": session_issues,
    }


def generate_session_report(mode: str, all_scores: list, session_issues: dict, turn_count: int) -> dict:
    """Generate end-of-session progress report."""
    if not all_scores:
        return {}
    
    avg = lambda key: round(sum(s[key] for s in all_scores) / len(all_scores), 1)
    
    overall_avg = avg("overall")
    
    # Determine trend (improving, stable, declining)
    if len(all_scores) >= 3:
        first_half = sum(s["overall"] for s in all_scores[:len(all_scores)//2]) / (len(all_scores)//2)
        second_half = sum(s["overall"] for s in all_scores[len(all_scores)//2:]) / (len(all_scores) - len(all_scores)//2)
        trend = "📈 Improving" if second_half > first_half + 0.5 else ("📉 Needs Work" if second_half < first_half - 0.5 else "📊 Consistent")
    else:
        trend = "📊 Baseline"
    
    # Strengths and weaknesses
    score_keys = ["grammar", "fluency", "vocabulary", "pronunciation", "confidence"]
    averages = {k: avg(k) for k in score_keys}
    sorted_scores = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    
    strengths = [k.title() for k, v in sorted_scores[:2] if v >= 7]
    weaknesses = [k.title() for k, v in sorted_scores if v < 6]
    
    # Suggestions
    suggestions = []
    if averages.get("vocabulary", 10) < 7:
        suggestions.append("Expand your vocabulary: learn 5 new words daily and use them in sentences.")
    if averages.get("fluency", 10) < 7:
        suggestions.append("Practice speaking at a natural pace — not too fast, not too slow.")
    if averages.get("confidence", 10) < 7:
        suggestions.append("Record yourself speaking and play it back — you'll spot hesitations.")
    if session_issues.get("fillers", 0) > 5:
        suggestions.append("Replace filler words with a confident 1-second pause.")
    if session_issues.get("short_answers", 0) >= 2:
        suggestions.append("Challenge yourself to speak for at least 30 seconds on each topic.")
    
    if not suggestions:
        suggestions.append("Keep up the great work! Try advanced modes like Debate Practice or IELTS.")
    
    mode_config = SPEAKING_MODES.get(mode, {})
    
    return {
        "mode": mode,
        "mode_title": mode_config.get("title", mode),
        "turns_completed": turn_count,
        "overall_score": overall_avg,
        "trend": trend,
        "score_breakdown": averages,
        "strengths": strengths if strengths else ["Participation"],
        "weaknesses": weaknesses if weaknesses else [],
        "suggestions": suggestions[:3],
        "xp_earned": min(100, turn_count * 15 + int(overall_avg * 5)),
        "grade": (
            "S" if overall_avg >= 9 else
            "A" if overall_avg >= 8 else
            "B" if overall_avg >= 7 else
            "C" if overall_avg >= 5 else "D"
        )
    }