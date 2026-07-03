"""
email_generator.py  –  Offline AI Email Generation Engine
==========================================================

Zero external dependencies.  No API keys.  No internet required.
Pure Python + random template selection.

Architecture
------------
1.  PHRASE BANKS        – Greetings, openings, transitions, CTAs,
                          closing lines, sign-offs, signatures.
                          Every bank has 8-15+ options so repeated
                          generations feel different.

2.  TOPIC TEMPLATES     – 26 named topic families (Leave, Job,
                          Internship, Complaint, Meeting, Proposal,
                          Interview, Resignation, Invitation,
                          Cold Email, Follow-up, Thank You,
                          Congratulations, Festival Wishes, Birthday,
                          Reminder, Customer Support, Refund,
                          Order Delay, Project Update, Feedback,
                          Payment Reminder, Sales, Marketing,
                          Apology, Promotion Request) + generic.
                          Each family has 3-5 body options.

3.  detect_topic_key()  – Keyword matching against the user's
                          free-text Topic field. Falls back to
                          "generic" gracefully.

4.  generate_email()    – Main entry point. Assembles Subject,
                          Greeting, Opening, Body, Extra paragraphs,
                          Closing, Sign-off, Signature.
                          Quality and length controlled by:
                              premium_level  (Basic / Premium / Premium Plus)
                              length         (Small / Medium / Large)
                              tone           (9 tones)
"""

import random


# ======================================================================
# 1.  TOPIC  →  TEMPLATE KEY  (keyword matching)
# ======================================================================

TOPIC_KEYWORDS = {
    "leave": [
        "leave", "vacation", "sick leave", "casual leave",
        "day off", "holiday request", "medical leave",
        "maternity leave", "paternity leave", "annual leave",
    ],
    "job": [
        "job application", "apply for", "job opening",
        "vacancy", "position", "job role", "career opportunity",
        "open position", "hiring", "job post",
    ],
    "internship": [
        "internship", "intern", "training program",
        "summer internship", "industrial training",
        "work experience", "apprenticeship",
    ],
    "complaint": [
        "complaint", "issue", "problem", "dissatisfied",
        "not working", "defective", "poor service",
        "grievance", "dispute", "unsatisfactory",
    ],
    "meeting": [
        "meeting", "schedule a call", "discussion",
        "appointment", "video call", "conference",
        "sync", "catch up", "team call", "zoom",
    ],
    "proposal": [
        "business proposal", "proposal", "partnership",
        "collaboration", "joint venture", "business deal",
        "strategic alliance", "tie-up",
    ],
    "interview": [
        "interview", "shortlisted", "selection round",
        "technical round", "hr round", "interview schedule",
        "interview confirmation", "reschedule interview",
    ],
    "resignation": [
        "resignation", "resign", "last working day",
        "notice period", "stepping down", "quitting",
        "exit", "relieving letter",
    ],
    "invitation": [
        "invitation", "invite", "ceremony", "event",
        "function", "launch", "conference invite",
        "webinar invite", "party invite", "gathering",
    ],
    "cold_email": [
        "cold email", "introduction", "introduce myself",
        "outreach", "reaching out", "networking",
        "first contact", "initial outreach",
    ],
    "follow_up": [
        "follow up", "followup", "checking in",
        "status update", "any update", "following up",
        "reminder follow up", "chasing",
    ],
    "thank_you": [
        "thank you", "thanks", "appreciation",
        "grateful", "gratitude", "thankful",
        "expressing thanks", "many thanks",
    ],
    "congrats": [
        "congratulations", "congrats", "well done",
        "promotion announcement", "achievement",
        "success", "felicitations",
    ],
    "festival": [
        "festival", "diwali", "holi", "eid",
        "christmas", "new year", "pongal", "navratri",
        "onam", "baisakhi", "durga puja", "festive wishes",
    ],
    "birthday": [
        "birthday", "happy birthday", "bday",
        "birth anniversary", "birthday wishes",
    ],
    "reminder": [
        "reminder", "don't forget", "deadline reminder",
        "gentle reminder", "follow up reminder",
        "submission reminder", "due date reminder",
    ],
    "support": [
        "customer support", "support request",
        "help needed", "technical support",
        "raise a ticket", "service request",
        "assistance required",
    ],
    "refund": [
        "refund", "money back", "return order",
        "cancel order", "chargeback", "refund request",
        "return policy",
    ],
    "order_delay": [
        "order delay", "delayed delivery",
        "shipment delay", "late delivery",
        "package not received", "where is my order",
    ],
    "project": [
        "project update", "project status",
        "milestone", "sprint update", "progress report",
        "deliverable", "project summary",
    ],
    "feedback": [
        "feedback", "review request", "rate your experience",
        "share your thoughts", "testimonial",
        "user feedback", "product feedback",
    ],
    "payment": [
        "payment reminder", "invoice", "due payment",
        "outstanding payment", "pending amount",
        "overdue invoice", "billing",
    ],
    "sales": [
        "sales", "offer", "discount", "deal",
        "promotional", "special price", "exclusive offer",
        "limited time", "flash sale",
    ],
    "marketing": [
        "marketing", "campaign", "newsletter",
        "product launch", "announcement", "new feature",
        "product update", "press release",
    ],
    "apology": [
        "apology", "sorry", "apologize",
        "regret", "sincere apologies", "my mistake",
        "error on our part", "inconvenience",
    ],
    "promotion_req": [
        "promotion request", "salary hike",
        "appraisal", "increment", "performance review",
        "raise request", "career growth",
    ],
}


def detect_topic_key(topic_text: str) -> str:
    """
    Case-insensitive keyword scan of the user's free-text topic.
    Returns the matching template family key, or 'generic'.
    """
    text = (topic_text or "").lower().strip()
    for key, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return key
    return "generic"


# ======================================================================
# 2.  PHRASE BANKS
# ======================================================================

# -- Greetings (keyed by tone) -----------------------------------------
GREETINGS = {
    "Formal":       [
        "Dear Sir/Madam,",
        "Respected Sir/Madam,",
        "Dear {name},",
        "To Whom It May Concern,",
        "Respected {name},",
    ],
    "Professional": [
        "Dear {name},",
        "Hello {name},",
        "Dear Sir/Madam,",
        "Good day, {name},",
        "Hi {name},",
    ],
    "Friendly":     [
        "Hi {name},",
        "Hello {name},",
        "Hey {name},",
        "Hi there, {name},",
        "Howdy, {name}!",
    ],
    "Confident":    [
        "Dear {name},",
        "Hello {name},",
        "Hi {name},",
        "Good morning, {name},",
    ],
    "Polite":       [
        "Dear {name},",
        "Respected {name},",
        "Dear Sir/Madam,",
        "Hello {name},",
    ],
    "Persuasive":   [
        "Dear {name},",
        "Hello {name},",
        "Hi {name},",
        "Good day, {name},",
    ],
    "Respectful":   [
        "Respected {name},",
        "Dear {name},",
        "Honourable {name},",
        "Dear Sir/Madam,",
    ],
    "Apologetic":   [
        "Dear {name},",
        "Respected {name},",
        "Dear Sir/Madam,",
        "Hello {name},",
    ],
    "Simple":       [
        "Hi {name},",
        "Hello {name},",
        "Hey {name},",
        "Hi there,",
    ],
}

# -- Opening sentences (used only at Premium+ levels) ------------------
OPENINGS = [
    "I hope this email finds you in good health and high spirits.",
    "I hope you are doing well.",
    "I trust this message reaches you at a convenient time.",
    "I hope you're having a productive day.",
    "I trust you are well.",
    "I hope this note finds you well.",
    "I am reaching out to you today with an important matter.",
    "Thank you for taking the time to read this email.",
    "I appreciate you giving this your attention.",
    "I am writing to you with the utmost respect.",
]

# -- Transition sentences (used in Medium / Large length) --------------
# These are complete sentences, not fragments, so they pair cleanly
# with any CTA sentence that follows them.
TRANSITIONS = [
    "With this in mind, I wanted to follow up directly.",
    "I would also like to take this opportunity to reiterate my commitment.",
    "Furthermore, I believe open and timely communication is key to a smooth resolution.",
    "On a related note, I remain fully available to discuss this at any time.",
    "To elaborate a little further on my position, I am fully prepared to cooperate at every step.",
    "I would also like to add that I appreciate your time and attention on this matter.",
    "Building on this, I am confident that a positive outcome is well within reach.",
    "In connection with the above, I am happy to provide any additional context you may require.",
    "Additionally, I would like to express my willingness to assist in any way I can.",
    "Given the circumstances, I believe a prompt response from your end would help us move forward efficiently.",
    "Taking this further, I am keen to ensure this is handled in the most professional manner possible.",
    "I would also like to note that I have documented all relevant details and can share them upon request.",
]

# -- Call to action sentences ------------------------------------------
CALL_TO_ACTION = [
    "I would be grateful if you could look into this at your earliest convenience.",
    "Kindly let me know if you need any further information from my end.",
    "I look forward to your positive response.",
    "Please feel free to reach out if any clarification is required.",
    "I would appreciate it if we could connect at your earliest convenience.",
    "Looking forward to hearing from you soon.",
    "I would welcome the opportunity to discuss this further.",
    "Please do not hesitate to contact me with any questions.",
    "I remain available to provide any additional details you may require.",
    "Your prompt response would be greatly appreciated.",
    "I hope to hear back from you at your earliest convenience.",
    "Feel free to schedule a time to discuss this whenever suits you.",
]

# -- Premium Plus extra sentences (polish / confidence boosters) -------
PREMIUM_PLUS_EXTRAS = [
    "I have given this careful thought and am confident this reflects a well-considered position.",
    "I want to assure you that I have taken every aspect of this matter into careful consideration before reaching out.",
    "I am happy to provide any additional documentation, data, or context that may help in moving this forward efficiently.",
    "It is my sincere belief that a timely response to this matter will benefit all parties involved.",
    "I remain committed to maintaining a professional and productive relationship, and I appreciate your cooperation in this regard.",
    "I would be more than happy to hop on a brief call or meeting to walk you through the details at your convenience.",
    "I have ensured that all relevant information has been included in this email so that you have everything needed to take action.",
]

# -- Closing lines (keyed by tone) -------------------------------------
CLOSING_LINES = {
    "Formal":       [
        "Thank you for your time and consideration.",
        "I appreciate your attention to this matter.",
        "I am grateful for your understanding and cooperation.",
        "I remain at your disposal for any further clarification.",
    ],
    "Professional": [
        "Thank you for your time.",
        "I appreciate your attention to this request.",
        "Thank you for considering this matter.",
        "Your time and consideration are greatly appreciated.",
    ],
    "Friendly":     [
        "Thanks a lot for your time!",
        "Really appreciate your help on this!",
        "Thanks so much — means a lot!",
        "Looking forward to connecting!",
    ],
    "Confident":    [
        "I am confident this matter will be handled smoothly.",
        "Thank you for considering my request.",
        "I trust this will be addressed promptly.",
        "I look forward to a swift resolution.",
    ],
    "Polite":       [
        "Thank you very much for your kind consideration.",
        "I sincerely appreciate your help and cooperation.",
        "I am deeply grateful for your time.",
        "Your understanding means a great deal to me.",
    ],
    "Persuasive":   [
        "I truly believe this would be a great opportunity for both of us.",
        "I am confident that this aligns well with your goals.",
        "This is an opportunity I genuinely believe is worth your consideration.",
        "Thank you for taking the time to evaluate this proposal.",
    ],
    "Respectful":   [
        "I deeply appreciate your time and guidance in this matter.",
        "Thank you for your valuable support and understanding.",
        "Your guidance is deeply appreciated.",
        "I remain sincerely grateful for your consideration.",
    ],
    "Apologetic":   [
        "Once again, I sincerely apologize for any inconvenience caused.",
        "I am truly sorry for the trouble this may have caused.",
        "I deeply regret the inconvenience and assure you it will not recur.",
        "Thank you for your patience and understanding in this matter.",
    ],
    "Simple":       [
        "Thanks!",
        "Thank you.",
        "Appreciate it.",
        "Thanks for your time.",
    ],
}

# -- Sign-offs (keyed by tone) -----------------------------------------
SIGN_OFFS = {
    "Formal":       ["Yours sincerely,", "Yours faithfully,", "Respectfully yours,", "Respectfully,"],
    "Professional": ["Best regards,", "Kind regards,", "Sincerely,", "Warm regards,"],
    "Friendly":     ["Best,", "Cheers,", "Warm regards,", "Take care,", "All the best,"],
    "Confident":    ["Best regards,", "Regards,", "With confidence,"],
    "Polite":       ["Kind regards,", "With regards,", "Respectfully,"],
    "Persuasive":   ["Best regards,", "Looking forward to your reply,", "Eagerly awaiting your response,"],
    "Respectful":   ["Respectfully,", "With sincere regards,", "Yours respectfully,"],
    "Apologetic":   ["With sincere apologies,", "Apologetically,", "Sincerely,"],
    "Simple":       ["Thanks,", "Regards,", "Bye,"],
}


# -- Premium Plus polish sentences (added before closing) -------------
PREMIUM_PLUS_POLISH = [
    (
        "I have given this matter careful thought and am confident that "
        "this email accurately reflects a well-considered and professional position."
    ),
    (
        "I want to assure you that every relevant aspect has been taken into account "
        "before reaching out, and I am committed to seeing this through in a "
        "professional and timely manner."
    ),
    (
        "I would be more than happy to arrange a brief call or meeting to walk you "
        "through the details at a time that works best for you."
    ),
    (
        "I have ensured all relevant information is included so you have everything "
        "needed to take the appropriate next steps without delay."
    ),
    (
        "It is my sincere belief that a timely and thoughtful response to this matter "
        "will benefit all parties involved and help us move forward efficiently."
    ),
    (
        "I remain fully committed to maintaining a transparent and professional "
        "communication channel throughout this process, and I am grateful for your "
        "attention and cooperation."
    ),
    (
        "I am confident in the strength of this request and am prepared to support it "
        "with any additional documentation, data, or context you may require."
    ),
]

# -- Generic conclusion paragraphs (Premium Plus fallback) ------------
CONCLUSIONS_GENERIC = [
    (
        "I am confident that with your support and timely consideration, "
        "this matter will be resolved in the best possible manner. "
        "I remain committed to maintaining open and transparent communication "
        "throughout this process."
    ),
    (
        "I appreciate the time you have taken to read through this email. "
        "It is my sincere hope that we can address this matter constructively "
        "and efficiently. I am fully available to provide any additional "
        "information or documentation that may be required."
    ),
    (
        "Thank you for your patience and understanding in this regard. "
        "I believe that with clear communication and mutual cooperation, "
        "we can arrive at the best possible outcome. "
        "Please do not hesitate to reach out if you require anything further."
    ),
    (
        "I would like to reiterate my commitment to handling this matter "
        "with the utmost professionalism and integrity. "
        "Your support in moving this forward promptly is deeply appreciated, "
        "and I remain at your disposal for any further action required."
    ),
    (
        "I am eager to move forward and look forward to a positive outcome. "
        "Should you need to speak with me directly, please feel free to reach "
        "out and I will make myself available at the earliest opportunity."
    ),
    (
        "To summarise, I trust this email has provided all the necessary context "
        "for you to take the appropriate next steps. "
        "I am fully prepared to assist in any way I can to facilitate a smooth "
        "and efficient resolution."
    ),
]


# ======================================================================
# 3.  TOPIC TEMPLATES
#     Each topic has:
#       subject    – 5 options (may contain {topic})
#       body       – 5 main paragraph variants (may contain {topic})
#       support    – 5-6 supporting sentences (Medium/Large)
#       conclusion – 4 closing paragraph options (Premium Plus / Large)
#       body     – list of main paragraph options (may contain {topic})
# ======================================================================

TEMPLATES = {

    # ------------------------------------------------------------------
    "leave": {
        "subject": [
            "Leave Application",
            "Request for Leave of Absence",
            "Application for Leave – {topic}",
            "Leave Request – Personal",
            "Requesting a Few Days Off",
        ],
        "body": [
            (
                "I am writing to formally request leave from work. I need to be away for a few days due "
                "to personal reasons that require my immediate attention. I will ensure that all pending "
                "tasks are completed or properly handed over before my leave begins."
            ),
            (
                "I would like to request leave for a short period as I need to attend to an important "
                "personal matter that cannot be postponed. I assure you that I will coordinate with my "
                "team to ensure there is no disruption to ongoing projects during my absence."
            ),
            (
                "I am requesting a few days of leave due to a personal commitment that demands my "
                "presence. I have already informed my team members and will make sure all my "
                "responsibilities are covered while I am away."
            ),
            (
                "I wish to formally apply for leave. The reason for my request is a personal matter "
                "that I need to attend to with urgency. I will be available over email for any critical "
                "communications during this period."
            ),
        ],
        "support": [
            "I will submit all pending deliverables before the leave commences.",
            "My colleague has agreed to handle any urgent work in my absence.",
            "I am available on email for any critical queries during this period.",
            "I will ensure a smooth transition of responsibilities before I leave.",
        ],
    },

    # ------------------------------------------------------------------
    "job": {
        "subject": [
            "Application for the Position of {topic}",
            "Job Application – {topic}",
            "Application for Open Role: {topic}",
            "Expression of Interest – {topic}",
            "Applying for the Role of {topic}",
        ],
        "body": [
            (
                "I am writing to express my sincere interest in the position currently open at your "
                "esteemed organization. Having reviewed the role carefully, I believe my skills, "
                "experience, and career aspirations align strongly with what you are looking for, and "
                "I would welcome the opportunity to contribute to your team."
            ),
            (
                "I came across the job opening at your organization and was immediately drawn to it. "
                "With my background and hands-on experience in relevant areas, I am confident that I "
                "can add significant value to your team and contribute meaningfully from day one."
            ),
            (
                "I am reaching out to apply for the position advertised by your organization. "
                "Throughout my career, I have developed a solid foundation in the required skill areas "
                "and I am eager to bring my expertise to a dynamic and growth-oriented company like yours."
            ),
            (
                "Please accept this email as my formal application for the role you have advertised. "
                "I have been following your company's work with great admiration, and I believe this "
                "opportunity is perfectly aligned with my professional goals and skill set."
            ),
        ],
        "support": [
            "I have attached my updated resume and cover letter for your kind consideration.",
            "My portfolio and work samples are available upon request.",
            "I would be happy to provide references from previous employers if required.",
            "I am available for an interview at any time convenient for your team.",
        ],
    },

    # ------------------------------------------------------------------
    "internship": {
        "subject": [
            "Internship Application",
            "Application for Internship Opportunity",
            "Request for Summer Internship",
            "Internship Application – {topic}",
        ],
        "body": [
            (
                "I am reaching out to apply for an internship opportunity at your esteemed organization. "
                "As a student eager to bridge the gap between academic learning and industry practice, "
                "I believe interning with your team would be an incredibly enriching experience. "
                "I am hardworking, quick to learn, and genuinely enthusiastic about contributing "
                "meaningfully during my time here."
            ),
            (
                "I am very interested in pursuing an internship with your team. Having studied "
                "extensively in this field, I am now looking for an opportunity to apply that knowledge "
                "to real-world challenges. I am confident that working under your guidance would "
                "accelerate my professional development significantly."
            ),
            (
                "I am writing to express my interest in an internship position at your organization. "
                "I am keen to learn from industry professionals and contribute to your team's work "
                "during the internship period. I assure you of my full dedication and enthusiasm."
            ),
        ],
        "support": [
            "I have enclosed my academic transcripts and a brief portfolio for your review.",
            "I am flexible with the internship duration and can start immediately if required.",
            "I am comfortable working on any projects your team assigns me.",
            "I would love to discuss how I can contribute to your team's goals.",
        ],
    },

    # ------------------------------------------------------------------
    "complaint": {
        "subject": [
            "Formal Complaint Regarding {topic}",
            "Complaint – {topic}",
            "Raising a Concern About {topic}",
            "Raising a Concern Regarding {topic}",
            "Official Complaint: {topic}",
        ],
        "body": [
            (
                "I am writing to bring to your attention a serious concern I have experienced regarding "
                "{topic}. Despite waiting patiently for a resolution, the situation remains unresolved, "
                "which has caused significant inconvenience on my end. I am requesting your immediate "
                "intervention to address and resolve this matter."
            ),
            (
                "I wish to formally lodge a complaint about {topic}. The experience I had was far "
                "below the standard I expected, and I believe this situation needs to be addressed "
                "urgently. I am hoping for a prompt and satisfactory resolution."
            ),
            (
                "I am reaching out to formally raise a concern regarding {topic}. As a valued customer "
                "and someone who has always had a positive experience with your organization, I am "
                "disappointed with the current situation and hope this can be resolved at the earliest."
            ),
            (
                "This letter serves as a formal complaint regarding {topic}. I have faced considerable "
                "difficulty and inconvenience as a direct result of this issue. I expect this to be "
                "addressed with priority and trust that appropriate corrective action will be taken."
            ),
        ],
        "support": [
            "I have attached relevant screenshots and documentation to support my complaint.",
            "I would appreciate a written acknowledgment of this complaint and an expected resolution timeline.",
            "If this is not resolved within a reasonable time, I may need to escalate the matter further.",
            "I hope we can resolve this amicably without any further escalation.",
        ],
    },

    # ------------------------------------------------------------------
    "meeting": {
        "subject": [
            "Request for a Meeting",
            "Meeting Request: {topic}",
            "Scheduling a Discussion on {topic}",
            "Let's Connect – {topic}",
            "Requesting a Brief Meeting",
        ],
        "body": [
            (
                "I would like to request a meeting to discuss {topic}. I believe a focused conversation "
                "would help us align our perspectives and move forward more effectively. Please let me "
                "know a date and time that works best for you, and I will adjust my schedule accordingly."
            ),
            (
                "I am writing to schedule a meeting regarding {topic}. It would be great to have a "
                "structured discussion to address the key points and ensure we are all on the same page. "
                "I am flexible with the timing and happy to work around your availability."
            ),
            (
                "I would love the opportunity to connect with you to talk through {topic}. "
                "A short meeting would help us clarify things efficiently. Please share your "
                "available slots and I will confirm promptly."
            ),
            (
                "Could we set up a brief meeting to go over {topic}? I think a direct conversation "
                "would be far more productive than going back and forth over email. I am available "
                "on most days and will happily accommodate your preferred time."
            ),
        ],
        "support": [
            "I am happy to arrange a video call, phone call, or in-person meeting, as you prefer.",
            "The estimated duration of the meeting would be approximately 30 minutes.",
            "Please share a meeting link or dial-in details at your convenience.",
            "I will send a calendar invite once we confirm the time.",
        ],
    },

    # ------------------------------------------------------------------
    "proposal": {
        "subject": [
            "Business Proposal: {topic}",
            "Partnership Proposal – {topic}",
            "A Proposal for Your Consideration",
            "Exciting Business Opportunity: {topic}",
            "Proposal for Collaboration on {topic}",
        ],
        "body": [
            (
                "I am writing to propose a business opportunity that I firmly believe has the potential "
                "to be mutually beneficial. Regarding {topic}, I have put together a detailed plan that "
                "outlines the scope, benefits, and roadmap for our potential collaboration. "
                "I would be delighted to walk you through it at your earliest convenience."
            ),
            (
                "I would like to present a proposal concerning {topic}. After thorough research and "
                "planning, I am confident that this collaboration could yield excellent results for both "
                "our organizations. I would love the opportunity to present the full details to you "
                "and address any questions you may have."
            ),
            (
                "Please allow me to introduce a business proposal related to {topic}. This initiative "
                "has been carefully thought out, and I believe the synergy between our organizations "
                "makes this an ideal opportunity to explore. I am eager to discuss this further at your convenience."
            ),
        ],
        "support": [
            "I have prepared a detailed proposal document which I can share upon your confirmation.",
            "A short presentation can be arranged at a time most convenient for you.",
            "I am open to customizing the proposal to better suit your organization's priorities.",
            "I look forward to the possibility of building a strong and lasting partnership.",
        ],
    },

    # ------------------------------------------------------------------
    "interview": {
        "subject": [
            "Interview Confirmation",
            "Regarding the Upcoming Interview",
            "Interview Schedule for {topic}",
            "Follow-up: Interview for {topic}",
        ],
        "body": [
            (
                "Thank you for considering me for this opportunity. I am writing to confirm my "
                "availability for the interview as discussed and to express my excitement about "
                "the possibility of joining your team. I will be fully prepared and punctual."
            ),
            (
                "I appreciate the opportunity to be shortlisted for this role. I am writing to "
                "confirm the interview details and to express my genuine enthusiasm. "
                "Please let me know if there is anything specific I should prepare or bring along."
            ),
            (
                "I would like to confirm my attendance for the interview scheduled as part of "
                "the selection process for {topic}. I am looking forward to this conversation "
                "and am well-prepared to demonstrate my suitability for the role."
            ),
        ],
        "support": [
            "Please let me know the interview format – whether it will be in-person, telephonic, or virtual.",
            "I will ensure I am available well in advance of the scheduled time.",
            "Kindly share any documents or preparation guidelines ahead of the interview.",
            "I look forward to meeting your team and learning more about the role.",
        ],
    },

    # ------------------------------------------------------------------
    "resignation": {
        "subject": [
            "Resignation Letter",
            "Notice of Resignation",
            "Formal Resignation – {topic}",
            "Stepping Down – {topic}",
        ],
        "body": [
            (
                "I am writing to formally submit my resignation from my current position, effective "
                "from the end of the notice period as per company policy. This has not been an easy "
                "decision, as I have genuinely valued my time here and the relationships I have built. "
                "I am committed to making this transition as smooth as possible and will ensure a "
                "thorough handover of all my responsibilities."
            ),
            (
                "Please accept this letter as my formal notice of resignation. I have deeply appreciated "
                "the opportunities for growth and learning that this role has provided. I intend to "
                "complete my duties diligently during my notice period and will do everything in my "
                "power to ensure continuity for the team."
            ),
            (
                "With a mixture of gratitude and reflection, I am writing to formally resign from my "
                "position. I am thankful for every experience, challenge, and achievement during my "
                "tenure here. I will ensure a complete and professional handover before my last working day."
            ),
        ],
        "support": [
            "I am happy to assist in training my replacement during the notice period.",
            "Please let me know how I can make the transition as seamless as possible.",
            "I would appreciate a relieving letter and experience certificate at the appropriate time.",
            "I wish the team continued success and growth in the future.",
        ],
    },

    # ------------------------------------------------------------------
    "invitation": {
        "subject": [
            "You're Invited: {topic}",
            "Cordial Invitation to {topic}",
            "Invitation – {topic}",
            "We'd Love to Have You at {topic}",
        ],
        "body": [
            (
                "It is with great pleasure that I invite you to {topic}. This promises to be a "
                "memorable occasion, and your presence would make it even more special. "
                "I sincerely hope you are able to join us and look forward to celebrating this moment "
                "together with you."
            ),
            (
                "We are delighted to extend a warm invitation to you for {topic}. It would be a true "
                "honour to have you with us on this occasion. Please do let us know if you will be "
                "attending so that we can make the necessary arrangements."
            ),
            (
                "I am reaching out to formally invite you to {topic}. Your attendance would mean a "
                "great deal to us. Kindly RSVP at your earliest convenience so we can plan accordingly "
                "and ensure everything is in order for your arrival."
            ),
        ],
        "support": [
            "The event details including date, time, and venue are mentioned below.",
            "Please RSVP by the mentioned date so arrangements can be made.",
            "Feel free to bring a companion if you'd like.",
            "We look forward to your presence and participation.",
        ],
    },

    # ------------------------------------------------------------------
    "cold_email": {
        "subject": [
            "Introduction – {topic}",
            "Reaching Out Regarding {topic}",
            "Quick Introduction",
            "I'd Love to Connect About {topic}",
        ],
        "body": [
            (
                "I hope you don't mind me reaching out directly. My name is on the signature below, "
                "and I wanted to get in touch regarding {topic}. I believe there is a meaningful "
                "opportunity for us to connect, and I would love to share more if you'd be open to it."
            ),
            (
                "I am writing to introduce myself and to briefly discuss {topic}. I came across your "
                "work and was genuinely impressed, which prompted me to reach out. I would love the "
                "chance to explore whether there's a potential synergy between us."
            ),
            (
                "I realise this is an unsolicited email, and I appreciate your patience in reading it. "
                "I am reaching out because I believe {topic} is something that could be very relevant "
                "and valuable to you. I'd be happy to elaborate further if you're open to a quick call or exchange."
            ),
        ],
        "support": [
            "I'll keep this brief — just a short conversation is all I'm asking for.",
            "I am happy to share more details, a deck, or references at your request.",
            "There is absolutely no obligation, and I completely respect your decision.",
            "I hope to hear from you, and thank you for reading this far.",
        ],
    },

    # ------------------------------------------------------------------
    "follow_up": {
        "subject": [
            "Following Up: {topic}",
            "Quick Follow-up on {topic}",
            "Checking In – {topic}",
            "Any Update on {topic}?",
        ],
        "body": [
            (
                "I wanted to follow up on my previous communication regarding {topic}. I understand "
                "you may have a busy schedule, and I truly appreciate your time. If there are any "
                "updates or additional information you need from my end, please do not hesitate to let me know."
            ),
            (
                "Just checking in regarding {topic}. I sent an earlier note about this and wanted to "
                "make sure it didn't get lost in your inbox. I would really appreciate any update "
                "whenever it's convenient for you."
            ),
            (
                "I'm writing a quick follow-up in connection with {topic}. I remain very interested "
                "and keen to move forward. Please let me know if there are any next steps or if "
                "further details are required from my side."
            ),
        ],
        "support": [
            "I completely understand if things are busy at your end — no pressure at all.",
            "Please let me know if you'd like me to re-send any previously shared materials.",
            "Even a brief update would be greatly appreciated.",
            "I remain enthusiastic and available to discuss at your convenience.",
        ],
    },

    # ------------------------------------------------------------------
    "thank_you": {
        "subject": [
            "Thank You",
            "A Sincere Thank You for {topic}",
            "Thank You – Truly Appreciated",
            "Expressing My Gratitude",
        ],
        "body": [
            (
                "I wanted to take a moment to sincerely thank you for {topic}. Your support, guidance, "
                "and kindness have made a real difference, and I am truly grateful. It means more to "
                "me than words can express."
            ),
            (
                "Thank you so much for {topic}. The effort, time, and care you put into this has not "
                "gone unnoticed, and I deeply appreciate it. I feel fortunate to have your support."
            ),
            (
                "I am writing to express my heartfelt gratitude for {topic}. Your contribution has "
                "been invaluable, and I want you to know that it has had a genuinely positive impact. "
                "Thank you from the bottom of my heart."
            ),
            (
                "A simple 'thank you' hardly seems sufficient for {topic}, but I want you to know "
                "how much it means to me. I will always be grateful for your generosity and support."
            ),
        ],
        "support": [
            "I look forward to reciprocating your kindness in any way I can.",
            "Please know that your gesture has made a lasting impression on me.",
            "I hope I can be of equal support to you in the future.",
            "Once again, thank you — it truly means the world.",
        ],
    },

    # ------------------------------------------------------------------
    "congrats": {
        "subject": [
            "Heartfelt Congratulations!",
            "Congratulations on {topic}!",
            "Well Deserved – Congratulations!",
            "Celebrating Your Achievement: {topic}",
        ],
        "body": [
            (
                "Congratulations on {topic}! This is absolutely wonderful news, and I am so happy "
                "to hear it. Your hard work, dedication, and persistence have clearly paid off, "
                "and this achievement is truly well-deserved. I couldn't be more pleased for you!"
            ),
            (
                "I wanted to reach out and congratulate you on {topic}. This is a remarkable "
                "accomplishment, and it is a testament to your talent and commitment. "
                "Well done — you should be incredibly proud of yourself!"
            ),
            (
                "Many congratulations on {topic}! I have always believed in your ability to "
                "achieve great things, and this moment is a wonderful confirmation of that. "
                "Wishing you continued success and even greater achievements in the future."
            ),
        ],
        "support": [
            "I hope this success is just the beginning of many more milestones to come.",
            "You truly deserve every bit of recognition coming your way.",
            "It has been a pleasure watching you grow and succeed.",
            "Wishing you all the best in everything that lies ahead.",
        ],
    },

    # ------------------------------------------------------------------
    "festival": {
        "subject": [
            "Warm Festive Greetings!",
            "Wishing You a Joyful {topic}!",
            "Happy {topic}!",
            "Festive Greetings from My Family to Yours",
        ],
        "body": [
            (
                "On the joyous occasion of {topic}, I want to extend my warmest wishes to you and "
                "your entire family. May this festive season bring you happiness, good health, "
                "prosperity, and countless cherished memories. "
                "Wishing you a celebration filled with love and laughter!"
            ),
            (
                "Sending my heartfelt greetings to you and your loved ones on the occasion of "
                "{topic}. May this special time of year fill your home with joy, your heart with "
                "peace, and your life with everything wonderful. "
                "Have a truly blessed and memorable celebration!"
            ),
            (
                "Happy {topic}! May this wonderful occasion bring you and your family immense "
                "joy and togetherness. May the coming year be filled with success, good health, "
                "and all the happiness you deserve."
            ),
        ],
        "support": [
            "Wishing you and your loved ones a wonderful celebration.",
            "May this festive season be your best one yet.",
            "Here's to new beginnings, shared joy, and lasting memories.",
            "Warmly thinking of you during this special time of year.",
        ],
    },

    # ------------------------------------------------------------------
    "birthday": {
        "subject": [
            "Happy Birthday!",
            "Wishing You a Wonderful Birthday!",
            "Many Happy Returns of the Day!",
            "It's Your Special Day – Happy Birthday!",
        ],
        "body": [
            (
                "Wishing you a very happy and joyful birthday! I hope today is filled with all the "
                "things that make you smile — laughter, love, and wonderful surprises. "
                "May this new year of your life bring you incredible experiences and endless happiness."
            ),
            (
                "Happy Birthday! On this special day, I want you to know how much you are appreciated "
                "and valued. May the year ahead be filled with success, good health, and all the joy "
                "you so richly deserve."
            ),
            (
                "Many happy returns of the day! Wishing you a birthday that is as warm and wonderful "
                "as you are. May every dream you've been nurturing come true in the year ahead. "
                "Have an absolutely spectacular day!"
            ),
        ],
        "support": [
            "Hope you get to celebrate with all the people who matter most to you.",
            "Wishing you good health, laughter, and all the best today and always.",
            "May this year be your best one yet!",
            "Sending lots of birthday love your way!",
        ],
    },

    # ------------------------------------------------------------------
    "reminder": {
        "subject": [
            "Friendly Reminder: {topic}",
            "Reminder Regarding {topic}",
            "Gentle Reminder – {topic}",
            "Please Don't Forget: {topic}",
        ],
        "body": [
            (
                "I hope this message finds you well. I am writing to send a gentle reminder regarding "
                "{topic}. I understand that schedules can get busy, and I just wanted to make sure "
                "this does not slip through the cracks. Kindly take the necessary action at your "
                "earliest opportunity."
            ),
            (
                "This is a friendly reminder about {topic}. As the deadline / due date is "
                "approaching, I wanted to bring this to your attention to ensure we stay on track. "
                "Please let me know if there is anything I can help with."
            ),
            (
                "I wanted to drop a quick note as a reminder regarding {topic}. Kindly give this "
                "your attention when you get a moment. If you have already addressed this, please "
                "disregard this message."
            ),
        ],
        "support": [
            "Please action this at your earliest convenience.",
            "Do reach out if you need any clarification or assistance.",
            "Thank you for your prompt attention to this matter.",
            "Your timely response would be greatly appreciated.",
        ],
    },

    # ------------------------------------------------------------------
    "support": {
        "subject": [
            "Support Request: {topic}",
            "Need Assistance With {topic}",
            "Technical Support Required – {topic}",
            "Help Needed: {topic}",
        ],
        "body": [
            (
                "I am reaching out to your support team for assistance regarding {topic}. "
                "I have been facing this issue for some time now and have tried the standard "
                "troubleshooting steps without success. I would greatly appreciate your expert "
                "guidance in resolving this as quickly as possible."
            ),
            (
                "I am writing to formally raise a support request concerning {topic}. "
                "This issue is affecting my ability to use the service effectively, and I "
                "would appreciate a prompt response from your team so we can get this sorted out."
            ),
            (
                "I require assistance with {topic}. Despite my best efforts to resolve this on "
                "my own, the issue persists. I am hoping your support team can guide me through "
                "a solution or escalate this if necessary."
            ),
        ],
        "support": [
            "I have attached relevant screenshots and error logs for your reference.",
            "My account details and relevant order/ticket IDs are mentioned below.",
            "Please let me know if you need any additional information to diagnose the issue.",
            "I would appreciate an estimated time for resolution.",
        ],
    },

    # ------------------------------------------------------------------
    "refund": {
        "subject": [
            "Refund Request: {topic}",
            "Request for Refund – {topic}",
            "Requesting a Refund for My Recent Purchase",
            "Formal Refund Application",
        ],
        "body": [
            (
                "I am writing to formally request a refund in connection with {topic}. "
                "Unfortunately, the product/service did not meet the expectations set at the time "
                "of purchase, and I believe I am entitled to a refund as per your stated policy. "
                "I would appreciate a prompt review and resolution of this request."
            ),
            (
                "I would like to initiate a refund process for {topic}. The reasons for this "
                "request are detailed below. I trust that your team will process this fairly "
                "and in accordance with the applicable terms and conditions."
            ),
            (
                "I am reaching out regarding a refund for {topic}. Given the circumstances, "
                "I believe a full/partial refund is warranted, and I hope this can be processed "
                "without unnecessary delay. Please let me know the next steps."
            ),
        ],
        "support": [
            "My order/transaction details are provided below for reference.",
            "I would prefer the refund to be credited to the original payment method.",
            "Please confirm receipt of this request and provide an expected processing timeline.",
            "I appreciate your prompt assistance in resolving this matter.",
        ],
    },

    # ------------------------------------------------------------------
    "order_delay": {
        "subject": [
            "Enquiry Regarding Delayed Order: {topic}",
            "Order Delay Concern – {topic}",
            "Where Is My Order? – {topic}",
            "Delayed Shipment: {topic}",
        ],
        "body": [
            (
                "I am writing to enquire about the status of my order related to {topic}, which has "
                "been delayed beyond the expected delivery date. I have been eagerly awaiting this "
                "order, and the delay has caused some inconvenience. "
                "Could you please provide an update on the current status and revised delivery timeline?"
            ),
            (
                "I placed an order for {topic} and was given an estimated delivery date, "
                "which has now passed without the package arriving. I would appreciate an urgent "
                "update on the whereabouts of my shipment and an explanation for the delay."
            ),
            (
                "This email is regarding the delay in my order for {topic}. As the delivery date "
                "has gone by without any update from your end, I am concerned and would like clarity "
                "on when I can expect my package to arrive."
            ),
        ],
        "support": [
            "My order ID and tracking details are provided below.",
            "Please investigate this and provide an updated delivery estimate.",
            "If the order cannot be fulfilled, please let me know the cancellation and refund process.",
            "I would appreciate a swift response to resolve this inconvenience.",
        ],
    },

    # ------------------------------------------------------------------
    "project": {
        "subject": [
            "Project Update: {topic}",
            "Status Update on {topic}",
            "Progress Report – {topic}",
            "Milestone Update: {topic}",
        ],
        "body": [
            (
                "I wanted to share a timely update on the progress of {topic}. "
                "Overall, the project is tracking well against the set milestones. "
                "The team has made significant strides, and I am pleased to report that we "
                "remain on schedule. I will continue to keep you informed as key developments unfold."
            ),
            (
                "Here is a brief status update for {topic}. We have successfully completed the "
                "current phase of work, and the team is now focused on the next set of deliverables. "
                "There are no major blockers at this stage, and progress continues to be strong."
            ),
            (
                "I am writing to provide you with a project status update for {topic}. "
                "Key milestones have been achieved as planned, and the team remains fully committed "
                "to delivering the remaining objectives within the agreed timeline."
            ),
        ],
        "support": [
            "A detailed status report is attached for your reference.",
            "Please let me know if you would like to discuss any specific aspect in more detail.",
            "The next update will be shared at the next scheduled checkpoint.",
            "Feel free to flag any concerns or questions at your convenience.",
        ],
    },

    # ------------------------------------------------------------------
    "feedback": {
        "subject": [
            "Request for Your Feedback – {topic}",
            "We Value Your Opinion on {topic}",
            "Feedback Request: {topic}",
            "Share Your Thoughts on {topic}",
        ],
        "body": [
            (
                "I am reaching out to kindly request your feedback regarding {topic}. "
                "Your insights are extremely valuable to us, and we are committed to using your "
                "input to continuously improve the experience we deliver. "
                "It would mean a great deal to hear your honest thoughts."
            ),
            (
                "Could you spare a few minutes to share your feedback on {topic}? "
                "We truly value your perspective and believe that real feedback from people like "
                "you is what helps us grow and serve you better."
            ),
            (
                "I would greatly appreciate it if you could share your feedback on {topic}. "
                "Whether it's positive, critical, or a mix of both — all feedback is welcome "
                "and will be taken constructively to make meaningful improvements."
            ),
        ],
        "support": [
            "The survey / feedback form is linked below for your convenience.",
            "This should take no more than 2-3 minutes of your time.",
            "All feedback is kept confidential and used solely for improvement purposes.",
            "Thank you in advance for taking the time to share your thoughts.",
        ],
    },

    # ------------------------------------------------------------------
    "payment": {
        "subject": [
            "Payment Reminder: {topic}",
            "Gentle Reminder – Outstanding Payment for {topic}",
            "Invoice Due: {topic}",
            "Overdue Payment Notice – {topic}",
        ],
        "body": [
            (
                "I hope you are doing well. I am writing to send a gentle reminder about the "
                "outstanding payment related to {topic}. As per our records, the amount remains "
                "due, and we kindly request you to process the payment at the earliest convenience. "
                "Please do not hesitate to reach out if you have any questions regarding the invoice."
            ),
            (
                "This is a friendly follow-up regarding the pending payment for {topic}. "
                "We understand that things can get busy, and we just wanted to ensure this "
                "did not get overlooked. Kindly arrange for the payment to be processed "
                "as soon as possible."
            ),
            (
                "I am reaching out regarding invoice number / payment for {topic}, which appears "
                "to be outstanding as of today. We would appreciate it if you could process this "
                "at your earliest convenience to avoid any late fees or service interruptions."
            ),
        ],
        "support": [
            "The invoice and payment details are attached to this email.",
            "Please feel free to contact us if there are any discrepancies.",
            "If payment has already been made, please disregard this reminder.",
            "We appreciate your prompt attention to this billing matter.",
        ],
    },

    # ------------------------------------------------------------------
    "sales": {
        "subject": [
            "Exclusive Offer: {topic}",
            "Special Deal Just for You – {topic}",
            "Don't Miss Out: {topic}",
            "A Great Opportunity Awaits: {topic}",
        ],
        "body": [
            (
                "I am excited to share an exclusive offer related to {topic} that I believe "
                "could bring real value to you. This is a limited-time opportunity, and I didn't "
                "want you to miss out. I would love to walk you through the details and answer "
                "any questions you might have."
            ),
            (
                "We have something special in store for you related to {topic}. "
                "Whether you are looking to save costs, improve efficiency, or simply get "
                "more for your money, this offer has been designed with that in mind. "
                "I'd love to tell you more."
            ),
            (
                "I am personally reaching out to let you know about {topic} — a deal that "
                "we believe is perfectly suited to your needs. Our team has put a lot of effort "
                "into making this as valuable as possible for customers like you."
            ),
        ],
        "support": [
            "Full details, pricing, and terms are available on request.",
            "This offer is valid for a limited period only, so do act quickly.",
            "I am happy to arrange a demo or send over a product brochure.",
            "Let me know if you'd like to discuss this further at a time that suits you.",
        ],
    },

    # ------------------------------------------------------------------
    "marketing": {
        "subject": [
            "Introducing: {topic}",
            "Something Exciting is Here – {topic}",
            "Big News: {topic}",
            "We're Thrilled to Announce: {topic}",
        ],
        "body": [
            (
                "We are thrilled to introduce {topic}, something we have been working on with you "
                "in mind. This is more than just a product update — it is a significant step "
                "forward, and we are excited to share it with you first. "
                "We believe you are going to love it."
            ),
            (
                "The wait is over — {topic} is here! We have poured enormous effort into this, "
                "and we are incredibly proud to finally share it with our valued audience. "
                "We hope it brings as much excitement to you as it has brought to our team."
            ),
            (
                "Today marks an exciting day as we officially launch {topic}. "
                "We designed this with our community in mind, and every feature, update, "
                "and improvement has been shaped by feedback from people just like you."
            ),
        ],
        "support": [
            "Learn more by clicking the link below or replying to this email.",
            "We would love to hear your initial thoughts once you've had a chance to explore it.",
            "Stay tuned for more updates and feature releases coming very soon.",
            "Thank you for being a valued part of our community.",
        ],
    },

    # ------------------------------------------------------------------
    "apology": {
        "subject": [
            "Sincere Apologies Regarding {topic}",
            "I Sincerely Apologize – {topic}",
            "Apology and Explanation: {topic}",
            "We Are Sorry: {topic}",
        ],
        "body": [
            (
                "I am writing to sincerely apologize for the inconvenience caused regarding {topic}. "
                "I fully understand the frustration and disappointment this may have caused, and I "
                "want you to know that this was not intentional. I take full responsibility and am "
                "committed to ensuring this does not happen again."
            ),
            (
                "Please accept my heartfelt apologies for {topic}. I recognize that my actions/our "
                "service fell short of the standard expected, and I am truly sorry for any trouble "
                "or inconvenience this has caused. I am taking immediate steps to address and rectify the situation."
            ),
            (
                "I owe you an apology regarding {topic}. Looking back, I/we should have handled "
                "things differently, and I genuinely regret the impact this has had on you. "
                "I assure you that I am committed to making things right."
            ),
        ],
        "support": [
            "I am taking steps to ensure this situation is not repeated.",
            "Please let me know how I can make this right for you.",
            "Your understanding and patience in this matter are deeply appreciated.",
            "I am open to discussing any compensation or corrective measures you deem appropriate.",
        ],
    },

    # ------------------------------------------------------------------
    "promotion_req": {
        "subject": [
            "Request for Promotion Consideration",
            "Discussing Career Growth: {topic}",
            "Requesting Appraisal Discussion",
            "Performance Review and Growth Discussion",
        ],
        "body": [
            (
                "I am writing to respectfully request a meeting to discuss my career growth and "
                "the possibility of a promotion or salary review. Over the past period, I have "
                "consistently delivered strong results, taken on additional responsibilities, and "
                "demonstrated a commitment to the organization's goals. I believe the time is right "
                "to have this conversation and explore the next step in my journey here."
            ),
            (
                "I would like to bring to your attention my interest in being considered for "
                "a promotion as part of the upcoming appraisal cycle. "
                "I have made meaningful contributions to {topic} and feel confident that my "
                "performance and commitment meet the criteria for advancement."
            ),
            (
                "I am requesting a dedicated discussion about my career trajectory within the "
                "organization. Having reflected on my performance, contributions, and the value "
                "I bring to the team, I feel it is the right time to explore opportunities for "
                "growth, whether in terms of title, compensation, or expanded responsibilities."
            ),
        ],
        "support": [
            "I am happy to prepare a formal performance summary ahead of our discussion.",
            "I welcome any feedback on areas for further improvement.",
            "I remain fully committed to the organization's success regardless of the outcome.",
            "I look forward to an open and constructive conversation on this topic.",
        ],
    },

    # ------------------------------------------------------------------
    "generic": {
        "subject": [
            "Regarding: {topic}",
            "{topic}",
            "Important Matter: {topic}",
            "Writing to You About {topic}",
        ],
        "body": [
            (
                "I am writing to you today regarding {topic}. I believe this is an important "
                "matter that deserves your attention, and I hope we can address it together "
                "in a timely and constructive manner."
            ),
            (
                "I wanted to reach out concerning {topic}. Please let me know your thoughts "
                "or any next steps you feel would be appropriate. I am happy to discuss this "
                "further at your convenience."
            ),
            (
                "I am contacting you in connection with {topic}. I would appreciate your time "
                "and consideration on this matter, and look forward to your response."
            ),
        ],
        "support": [
            "Please feel free to ask if you require any additional information.",
            "I remain available to discuss this at your convenience.",
            "Thank you for taking the time to consider this.",
            "I look forward to your earliest response.",
        ],
    },
}


# ======================================================================
# 4.  CONCLUSION BLOCKS  (Premium Plus / Large emails only)
#     Keyed by the same topic keys used in TEMPLATES.
#     generate_email() picks one at random and appends it before the
#     closing line to give Premium Plus emails a proper 5-section
#     structure: Opening → Body → Support → Conclusion → Closing.
# ======================================================================

CONCLUSIONS = {
    "leave": [
        (
            "I sincerely hope you will consider my request favorably. "
            "I assure you that my commitment to work remains unwavering, and I will "
            "ensure minimal disruption during my absence. I look forward to your "
            "kind approval at the earliest."
        ),
        (
            "I appreciate your understanding in granting me this leave. "
            "I remain dedicated to meeting all my professional responsibilities "
            "and will ensure a complete handover so that no work suffers in my absence. "
            "Kindly let me know if you need any further details."
        ),
        (
            "I am grateful for your consideration of this request. "
            "Please be assured that my absence will be well-managed and that all "
            "ongoing deliverables will be accounted for before I leave."
        ),
        (
            "I trust this request will be approved, and I assure you it will not "
            "adversely impact our team's workflow or productivity. "
            "I am happy to discuss any concerns you may have regarding the arrangement."
        ),
    ],
    "job": [
        (
            "I would be honored to discuss my application further and provide any "
            "additional information you may require. I am excited about the opportunity "
            "to contribute to your organization and confident in my ability to make a "
            "positive impact from day one. Thank you for considering my application."
        ),
        (
            "I am very enthusiastic about this opportunity and would love the chance "
            "to demonstrate my capabilities in person. I am available for an interview "
            "at any time convenient for you. Thank you for your careful consideration."
        ),
        (
            "I believe I have the right mix of skills, attitude, and experience to "
            "excel in this role. I would be thrilled to be given the chance to prove "
            "myself as a part of your talented team. I look forward to hearing from you."
        ),
        (
            "I am fully committed to contributing to the success and growth of your "
            "organization. I would welcome the opportunity to meet and discuss how I "
            "can add value. Thank you once again for this opportunity."
        ),
    ],
    "internship": [
        (
            "I would be truly grateful for the opportunity to be part of your team. "
            "I am committed to making the most of this experience and contributing "
            "positively. I look forward to hearing from you."
        ),
        (
            "I am enthusiastic about learning from your team and contributing my best "
            "during the internship period. I would be happy to appear for an interview "
            "at your convenience. Thank you for considering my application."
        ),
        (
            "I am confident that this internship would be a turning point in my "
            "professional journey, and I would approach it with the highest level of "
            "dedication and enthusiasm. I look forward to a positive response."
        ),
        (
            "I sincerely hope you will consider my application favorably. "
            "I promise to make the most of this opportunity. "
            "Thank you for your time and consideration."
        ),
    ],
    "complaint": [
        (
            "I sincerely hope this complaint will be taken seriously and acted upon "
            "swiftly. A timely and effective resolution would go a long way in restoring "
            "my confidence in your organization. I look forward to a prompt response."
        ),
        (
            "I trust that your organization will handle this with the professionalism "
            "and urgency it deserves. I am available to provide further information or "
            "discuss the issue in detail if needed."
        ),
        (
            "I would appreciate a detailed response outlining the steps you will take "
            "to address this complaint. I remain hopeful that this situation will be "
            "resolved to my satisfaction and that such incidents will not recur."
        ),
        (
            "Please treat this complaint as urgent and provide an update at the earliest. "
            "I believe that with open communication and prompt action, this matter can "
            "be resolved efficiently."
        ),
    ],
    "meeting": [
        (
            "I believe this meeting will be highly productive and help us move forward "
            "with clarity and confidence. I am looking forward to a great discussion and "
            "am fully prepared to make the most of your time. Please do let me know your availability."
        ),
        (
            "I am eager to connect and am confident that our discussion will lead to "
            "great outcomes for both parties. Kindly revert with your available time "
            "slots and I will confirm promptly."
        ),
        (
            "I appreciate your willingness to meet and I assure you that our time will "
            "be well spent. I will come fully prepared with relevant materials to ensure "
            "an efficient and focused discussion."
        ),
        (
            "Your time is valuable and I intend to make this meeting as focused and "
            "productive as possible. Please feel free to share a preferred time and "
            "format, and I will accommodate accordingly."
        ),
    ],
    "proposal": [
        (
            "I am genuinely excited about the potential of this collaboration and believe "
            "it represents a win-win opportunity. I look forward to your feedback and hope "
            "to schedule a follow-up discussion at the earliest."
        ),
        (
            "I would be grateful for the opportunity to present this proposal in more "
            "detail and answer any questions. I am confident that once you review the "
            "complete plan, you will see the immense value it brings."
        ),
        (
            "I firmly believe this partnership has the potential to create lasting and "
            "meaningful impact. I look forward to exploring this further with you and am "
            "available to meet at your convenience."
        ),
        (
            "Thank you for taking the time to consider this proposal. I am fully committed "
            "to making this collaboration a success. I hope we can connect soon to discuss "
            "the next steps."
        ),
    ],
    "interview": [
        (
            "I am very much looking forward to meeting your team and discussing how I can "
            "contribute to your organization. I will arrive fully prepared and am excited "
            "to make a strong impression. Thank you for this wonderful opportunity."
        ),
        (
            "I am eager to learn more about the role during the interview. I am confident "
            "this will be a mutually productive discussion. Please do not hesitate to "
            "contact me if you need anything prior to the interview."
        ),
        (
            "Thank you again for this opportunity. I look forward to a great conversation "
            "and am confident this interview will be the beginning of a long and fruitful "
            "professional relationship."
        ),
        (
            "I am thoroughly prepared and committed to giving my best. "
            "I greatly appreciate the trust you have placed in me by shortlisting me. "
            "I look forward to meeting you."
        ),
    ],
    "resignation": [
        (
            "I want to express my sincere gratitude to the entire team for making my "
            "time here truly memorable. I am proud of what we achieved together and leave "
            "with many fond memories. I wish the company continued success and growth."
        ),
        (
            "I hope my resignation is received in the same professional spirit in which "
            "it is tendered. I look forward to wrapping up responsibilities in the best "
            "way possible and departing on a positive note."
        ),
        (
            "I remain committed to ensuring this transition is as smooth as possible. "
            "I am grateful for the opportunity to have served this organization and leave "
            "with immense respect for the team and the leadership."
        ),
        (
            "Thank you for the valuable career experience I have gained during my time here. "
            "I hope to remain in touch and wish the company every success in the years ahead."
        ),
    ],
    "invitation": [
        (
            "We truly hope you will grace us with your presence on this special occasion. "
            "Your attendance would make the event truly memorable and we look forward to "
            "celebrating with you and creating beautiful memories together."
        ),
        (
            "We are eagerly looking forward to your confirmation and to welcoming you. "
            "Please do not hesitate to reach out if you have any questions about the event."
        ),
        (
            "Your presence would make this occasion truly special. We sincerely hope you "
            "will be able to join us and share in the joy. We await your response."
        ),
        (
            "We look forward to having you with us and making this a truly unforgettable "
            "event. Please confirm your attendance and feel free to bring a loved one along!"
        ),
    ],
    "cold_email": [
        (
            "I am genuinely excited about the prospect of connecting and believe this could "
            "be the start of something meaningful. Even a brief reply would mean a great deal. "
            "I look forward to hearing from you."
        ),
        (
            "I appreciate your time in reading through this message. I am confident that "
            "a conversation between us would be worthwhile for both sides. I hope to hear "
            "back from you and would be happy to accommodate your schedule."
        ),
        (
            "Thank you for considering my outreach. I keep my introductions professional "
            "and purposeful, and I genuinely believe this connection holds value. "
            "Looking forward to hearing from you."
        ),
        (
            "I know your time is extremely valuable and I truly appreciate you reading this. "
            "I hope we get the chance to connect soon — I am confident it will be time well spent."
        ),
    ],
    "follow_up": [
        (
            "I truly appreciate your time and attention. I am looking forward to hearing back "
            "from you and am committed to moving forward as soon as we have clarity. "
            "Thank you for your consideration."
        ),
        (
            "Thank you for being patient with my follow-up. I remain enthusiastic and "
            "committed and am available at any time for further discussion. "
            "Looking forward to your update."
        ),
        (
            "I appreciate your understanding and look forward to an update from your end. "
            "Please feel free to contact me directly if you need anything."
        ),
        (
            "I hope we can move forward with this soon. I remain available and look forward "
            "to your earliest response. Thank you for your time and consideration."
        ),
    ],
    "thank_you": [
        (
            "Once again, thank you so sincerely for everything. Your kindness and generosity "
            "are a true reflection of your wonderful character. I hope this message brings a "
            "smile to your face as your actions brought one to mine."
        ),
        (
            "I am truly grateful for everything you have done. I hope this message conveys "
            "just how much your support has meant to me. Thank you again — may life return "
            "all the kindness you give tenfold."
        ),
        (
            "With deep gratitude, I thank you once more. You have made a real difference, "
            "and I will always remember this fondly. I look forward to reciprocating your "
            "kindness in the future."
        ),
        (
            "Your gesture has made a significant positive impact and I wanted to make sure "
            "you know how much it meant to me. Thank you with all sincerity."
        ),
    ],
    "congrats": [
        (
            "Once again, my heartiest congratulations on this amazing accomplishment. "
            "I am so happy for you and hope this is the first of many such moments of "
            "triumph. Wishing you all the very best for the exciting journey ahead."
        ),
        (
            "I am so proud of everything you have achieved and look forward to celebrating "
            "with you in person soon. Keep reaching for the stars — you are destined for great things!"
        ),
        (
            "May this achievement open doors to even greater opportunities and successes. "
            "You deserve all the happiness that comes your way. Congratulations once again!"
        ),
        (
            "Enjoy this well-earned moment of success and celebration. Here is to many more "
            "brilliant achievements in the years to come. Congratulations from the bottom of my heart."
        ),
    ],
    "festival": [
        (
            "Once again, wishing you and your family a very happy and blessed {topic}. "
            "May this celebration be everything you hoped for and more. "
            "Stay safe, stay joyful, and enjoy every moment of this festive season."
        ),
        (
            "I hope this festive season fills your home with warmth, your heart with joy, "
            "and your life with everything beautiful. Happy {topic} once again!"
        ),
        (
            "May the spirit of {topic} stay with you throughout the year and bring light "
            "and happiness to every chapter of your life. Warm festive wishes from me to you."
        ),
        (
            "Here is wishing you a festive season filled with peace, prosperity, and purpose. "
            "May every good wish you hold in your heart come true. Happy {topic}!"
        ),
    ],
    "birthday": [
        (
            "Once again, wishing you the happiest of birthdays! May the year ahead be filled "
            "with countless blessings, happy surprises, and beautiful milestones. "
            "Enjoy your special day to the fullest — you truly deserve it!"
        ),
        (
            "I hope your birthday is everything you wished for and more. Here's to celebrating "
            "you today and always. Many many happy returns!"
        ),
        (
            "May your birthday be the start of something truly spectacular. Wishing you "
            "happiness, health, and all the success you richly deserve. Have a wonderful celebration!"
        ),
        (
            "Happy Birthday once again! May the coming year bring you closer to all your goals "
            "and fill your life with love, laughter, and beautiful moments."
        ),
    ],
    "reminder": [
        (
            "Thank you for giving this your attention. I am confident that with your "
            "prompt action, we can keep things on track and avoid any further delays. "
            "I look forward to your update."
        ),
        (
            "I appreciate your understanding and cooperation in this matter. "
            "Please do reach out if there is anything I can do to help. "
            "Looking forward to a positive update soon."
        ),
        (
            "Thank you for taking the time to address this. I remain available for any "
            "clarification or assistance needed and look forward to your timely response."
        ),
        (
            "I trust this reminder will help you prioritize accordingly. Please feel free "
            "to reach out anytime and I will be happy to assist. Thank you for your cooperation."
        ),
    ],
    "support": [
        (
            "I appreciate your prompt attention to this matter. I trust that your support "
            "team will be able to resolve this efficiently and get me back on track. "
            "Thank you for your assistance."
        ),
        (
            "I am confident in your team's ability to resolve this issue and look forward "
            "to a quick and effective solution. Please don't hesitate to reach out if you "
            "need any further information from my end."
        ),
        (
            "Thank you in advance for your help. I look forward to hearing from your "
            "support team soon and am hopeful for a speedy resolution."
        ),
        (
            "I am counting on your team's expertise to resolve this promptly. Please feel "
            "free to contact me at your earliest convenience. I greatly appreciate your assistance."
        ),
    ],
    "refund": [
        (
            "I trust that my refund request will be processed fairly and without undue delay. "
            "I remain open to discussing this further if needed and appreciate your "
            "understanding. Thank you for your prompt attention."
        ),
        (
            "I look forward to a swift resolution to this request. Please acknowledge this "
            "email and let me know the expected turnaround time for the refund processing."
        ),
        (
            "I appreciate your cooperation in resolving this efficiently. I hope this matter "
            "can be closed quickly and amicably. Please contact me with any questions."
        ),
        (
            "Thank you for attending to this request. I am available for any verification "
            "your team may need. I look forward to a positive and timely resolution."
        ),
    ],
    "order_delay": [
        (
            "I trust that your team will treat this as a priority and provide a satisfactory "
            "resolution promptly. I look forward to receiving my order and appreciate your "
            "attention to this matter."
        ),
        (
            "I would appreciate a response with a concrete update and resolution plan within "
            "the next 24 to 48 hours. Thank you for looking into this urgently."
        ),
        (
            "I hope this can be resolved quickly and efficiently. Please keep me updated at "
            "every stage, as I am eager to receive my order. Thank you for your cooperation."
        ),
        (
            "Your prompt attention to this delay will be greatly appreciated. I look forward "
            "to a clear update and swift resolution. Thank you for your assistance."
        ),
    ],
    "project": [
        (
            "I will continue to provide regular updates and remain fully committed to "
            "delivering this project on time and to the highest standards. Please do not "
            "hesitate to reach out if you have any questions or require further clarity."
        ),
        (
            "Thank you for your continued support and guidance throughout this project. "
            "I remain dedicated to ensuring a successful and timely outcome. "
            "I will send the next scheduled update as planned."
        ),
        (
            "I am confident in the team's ability to deliver excellent results. Please feel "
            "free to share any feedback or inputs. I look forward to your continued collaboration."
        ),
        (
            "I will keep a close eye on progress and flag any issues immediately. "
            "Thank you for your trust — I am committed to exceeding expectations on this project."
        ),
    ],
    "feedback": [
        (
            "We truly appreciate the time and effort you will take to share your thoughts. "
            "Your input will play a meaningful role in shaping the improvements we make. "
            "Thank you for being such a valued part of our journey."
        ),
        (
            "Thank you in advance for taking a moment to share your feedback. It is through "
            "insights like yours that we are able to grow and serve better. We look forward "
            "to hearing from you."
        ),
        (
            "Your feedback matters more than you know. We are committed to using it to make "
            "meaningful changes. Thank you for your continued support and trust in us."
        ),
        (
            "We are grateful for your time and honest response. Your perspective helps us "
            "become better, and we look forward to delivering experiences that truly delight you."
        ),
    ],
    "payment": [
        (
            "We value our relationship with you and hope to resolve this quickly and amicably. "
            "Please process the payment at the earliest and feel free to reach out if you have "
            "any questions or concerns regarding the invoice."
        ),
        (
            "We appreciate your prompt attention to this matter. Timely payments help us serve "
            "you better and maintain the quality of our services. Thank you for your continued partnership."
        ),
        (
            "Thank you for your understanding and for attending to this matter promptly. "
            "We look forward to continuing our positive working relationship."
        ),
        (
            "We trust you will treat this as a priority. Please confirm once the payment has "
            "been initiated so we can update our records accordingly. We appreciate your cooperation."
        ),
    ],
    "sales": [
        (
            "I would love the opportunity to connect briefly and share more about how this "
            "can benefit you directly. I am confident that once you see the full picture, you "
            "will be excited about the possibilities. Looking forward to your response."
        ),
        (
            "Please do let me know if you would like to explore this further. I promise to "
            "keep the conversation focused, informative, and respectful of your time."
        ),
        (
            "This opportunity won't be around forever, and I genuinely believe it is something "
            "you will want to take advantage of. Do reach out and let's talk more."
        ),
        (
            "Thank you for taking the time to read about this. I hope we get the chance to "
            "connect and explore how this can add real value. Looking forward to a great conversation!"
        ),
    ],
    "marketing": [
        (
            "We are so excited and cannot wait for you to be part of this new chapter. "
            "Thank you for your continued support and loyalty — it truly means everything to us. "
            "Stay tuned for more exciting updates!"
        ),
        (
            "Thank you for being part of our community. We hope you find this as exciting as "
            "we do, and we look forward to hearing your thoughts."
        ),
        (
            "We are just getting started and have many more exciting updates planned. "
            "Watch this space! Thank you for your trust and we hope this brings immense value to you."
        ),
        (
            "Your support has made this possible and we are deeply grateful. We hope this "
            "exceeds your expectations, and we look forward to growing and innovating together."
        ),
    ],
    "apology": [
        (
            "Once again, I am truly and deeply sorry. I sincerely hope you will give me "
            "the opportunity to make this right. Your satisfaction and trust are of the "
            "utmost importance and I am committed to ensuring a much better experience going forward."
        ),
        (
            "I understand that an apology alone may not undo the inconvenience, but please "
            "know it comes from genuine remorse. I am dedicated to ensuring this is fully "
            "resolved and will not happen again."
        ),
        (
            "Please give me the chance to restore your confidence. I am committed to "
            "addressing this in a timely manner and will remain accountable until you are "
            "fully satisfied with the resolution."
        ),
        (
            "I appreciate your patience and understanding. I will work hard to regain your "
            "trust and ensure a significantly better experience from this point forward. "
            "Thank you for giving me the opportunity to make things right."
        ),
    ],
    "promotion_req": [
        (
            "I am committed to continuing to deliver high-quality work and creating value "
            "for the team and organization. I hope we can schedule a meeting at your "
            "earliest convenience. I look forward to a constructive and positive conversation."
        ),
        (
            "I appreciate you taking the time to consider this request. I am passionate "
            "about my role and am eager to grow within this organization. I look forward "
            "to discussing how we can best structure this next step in my career."
        ),
        (
            "I remain fully dedicated and motivated, and I am excited about the future here. "
            "I am grateful for the support I have received and look forward to contributing "
            "at an even higher level with the appropriate recognition."
        ),
        (
            "Thank you for your time and consideration. I am confident this discussion will "
            "be positive and look forward to charting an exciting path forward together. "
            "Please let me know when would be a good time to connect."
        ),
    ],
    "generic": [
        (
            "I appreciate your time in reading this email and giving this matter your attention. "
            "I remain available for any follow-up discussion and look forward to a productive "
            "and timely response from your end."
        ),
        (
            "Thank you for your consideration. I hope we can resolve this in the most "
            "efficient and professional manner possible. I look forward to hearing from you soon."
        ),
        (
            "I trust this communication has provided sufficient context for you to take "
            "the appropriate next steps. I am here to assist in any way needed."
        ),
        (
            "Once again, thank you for your time. I look forward to a constructive "
            "dialogue and am confident we can address this matter effectively together."
        ),
    ],
}


# -- Detail / specificity connectors ------------------------------------
# Used to weave the user's chosen "specific type" (subtopic) into the body
# as its own natural sentence, for templates whose body paragraph doesn't
# already have a {topic} slot. Keeps every generated email anchored to the
# real situation instead of reading generically.
REASON_CONNECTORS = [
    "Specifically, this is regarding {detail}.",
    "To give you some context, this is about {detail}.",
    "In particular, I wanted to mention that this concerns {detail}.",
    "Just to clarify, this relates to {detail}.",
    "For your reference, the situation I'm referring to is {detail}.",
    "To be more precise, this is in connection with {detail}.",
    "I should mention that this is specifically about {detail}.",
    "For context, this has to do with {detail}.",
    "To fill you in, this is concerning {detail}.",
    "More specifically, I am writing about {detail}.",
]


# ======================================================================
# 5.  HELPER FUNCTIONS
# ======================================================================

def _get_detail_sentence(detail: str) -> str:
    """Return one random sentence weaving the specific subtopic detail in."""
    return random.choice(REASON_CONNECTORS).format(detail=detail)


def _get_greeting(tone: str, receiver_name: str) -> str:
    """Pick a random greeting for the given tone, inserting the receiver name."""
    tone_key = tone if tone in GREETINGS else "Professional"
    name     = receiver_name if receiver_name else "Sir/Madam"
    return random.choice(GREETINGS[tone_key]).format(name=name)


def _get_opening() -> str:
    """Return one random opening/pleasantry sentence (Premium / Premium Plus)."""
    return random.choice(OPENINGS)


def _get_cta() -> str:
    """Return a random call-to-action sentence."""
    return random.choice(CALL_TO_ACTION)


def _get_closing(tone: str) -> str:
    """Return a random closing line matched to the given tone."""
    tone_key = tone if tone in CLOSING_LINES else "Professional"
    return random.choice(CLOSING_LINES[tone_key])


def _get_sign_off(tone: str) -> str:
    """Return a random sign-off matched to the given tone."""
    tone_key = tone if tone in SIGN_OFFS else "Professional"
    return random.choice(SIGN_OFFS[tone_key])


def _get_conclusion(topic_key: str, topic: str) -> str:
    """
    Return a topic-specific conclusion paragraph (Premium Plus / Large).
    Falls back to a generic pool if the topic key isn't in CONCLUSIONS.
    """
    pool = CONCLUSIONS.get(topic_key, CONCLUSIONS_GENERIC)
    raw  = random.choice(pool)
    return raw.format(topic=topic) if "{topic}" in raw else raw


# ======================================================================
# 6.  MAIN  generate_email()
# ======================================================================

def generate_email(
    receiver_email: str,
    sender_email: str,
    topic: str,
    category: str,
    tone: str,
    length: str,
    premium_level: str,
    sender_name: str = "",
    receiver_name: str = "",
    topic_key: str = "",
    topic_detail: str = "",
) -> dict:
    """
    Build and return {"subject": str, "body": str}.

    Every call produces a different email because greetings, openings,
    body paragraphs, support sentences, conclusions, transitions, CTAs,
    closings, and sign-offs are all randomly selected from large banks.

    Quality tiers
    -------------
    Basic       : Greeting → Body → Closing → Sign-off
    Premium     : + Opening before body
                  + Support sentence after body (Medium / Large)
                  + Transition → CTA block
    Premium Plus: All of Premium
                  + Conclusion paragraph     (Large only)
                  + Polish sentence          (Medium / Large)
                  + Enriched closing with CTA
                  Full professional 5-section structure.

    Length modifiers
    ----------------
    Small  : Body only (no support / transition / conclusion)
    Medium : Body + Support + Transition + Polish (Premium Plus)
    Large  : Body + Support + Transition + Conclusion + Polish (Premium Plus)
    """

    resolved_topic_key = topic_key.strip() if topic_key and topic_key.strip() in TEMPLATES else detect_topic_key(topic)
    tpl       = TEMPLATES.get(resolved_topic_key, TEMPLATES["generic"])
    tone_key  = tone if tone in GREETINGS else "Professional"

    detail_clean = topic_detail.strip() if topic_detail else ""
    # Whatever gets slotted into "{topic}" placeholders: prefer the specific
    # subtopic detail chosen by the user (e.g. "a defective product I received")
    # over the generic dropdown label (e.g. "Complaint"), so subjects/bodies
    # read as written about a real situation instead of a category name.
    fill_topic = detail_clean if detail_clean else topic

    # ── Subject ──────────────────────────────────────────────────────────
    subject_topic = fill_topic[0].upper() + fill_topic[1:] if fill_topic else fill_topic
    subject_raw = random.choice(tpl["subject"])
    subject = subject_raw.format(topic=subject_topic) if "{topic}" in subject_raw else subject_raw
    if not subject.strip():
        subject = subject_topic  # safe fallback

    # ── Greeting ─────────────────────────────────────────────────────────
    greeting = _get_greeting(tone_key, receiver_name)

    # ── Opening pleasantry (Premium / Premium Plus only) ─────────────────
    opening = _get_opening() if premium_level in ("Premium", "Premium Plus") else ""

    # ── Main body paragraph ──────────────────────────────────────────────
    body_raw  = random.choice(tpl["body"])
    body_has_topic_slot = "{topic}" in body_raw
    main_para = body_raw.format(topic=fill_topic) if body_has_topic_slot else body_raw

    # ── Specificity sentence ──────────────────────────────────────────────
    # If the body template has no {topic} slot to absorb the user's chosen
    # detail, weave it in as its own short sentence so every topic — not
    # just the ones with an inline placeholder — reads as specific and
    # human rather than generic.
    if detail_clean and not body_has_topic_slot:
        main_para = main_para + " " + _get_detail_sentence(detail_clean)

    # ── Support sentence (Medium/Large, Premium/Premium Plus) ────────────
    support_sentence = ""
    if length in ("Medium", "Large") and premium_level in ("Premium", "Premium Plus"):
        if "support" in tpl:
            support_sentence = random.choice(tpl["support"])

    # ── Transition + CTA block (Medium/Large, all quality levels) ────────
    # Two clean sentences: a transitional opener, then a standalone CTA.
    transition_block = ""
    if length in ("Medium", "Large"):
        transition_block = random.choice(TRANSITIONS) + " " + _get_cta()

    # ── Conclusion paragraph (Large + Premium Plus) ───────────────────────
    conclusion_para = ""
    if length == "Large" and premium_level == "Premium Plus":
        conclusion_para = _get_conclusion(resolved_topic_key, fill_topic)

    # ── Premium Plus polish sentence (Medium / Large) ─────────────────────
    polish_sentence = ""
    if premium_level == "Premium Plus" and length in ("Medium", "Large"):
        polish_sentence = random.choice(PREMIUM_PLUS_POLISH)

    # ── Closing line ─────────────────────────────────────────────────────
    closing = _get_closing(tone_key)
    if premium_level == "Premium Plus":
        # Append a second CTA for a strong, corporate closing
        closing += " " + _get_cta()

    # ── Sign-off + Signature ─────────────────────────────────────────────
    sign_off     = _get_sign_off(tone_key)
    display_name = sender_name if sender_name else sender_email

    # ── Assemble all sections ────────────────────────────────────────────
    parts: list = []

    parts.append(greeting)
    parts.append("")                        # blank line after greeting

    if opening:
        parts.append(opening)
        parts.append("")

    parts.append(main_para)
    parts.append("")

    if support_sentence:
        parts.append(support_sentence)
        parts.append("")

    if transition_block:
        parts.append(transition_block)
        parts.append("")

    if polish_sentence:
        parts.append(polish_sentence)
        parts.append("")

    if conclusion_para:
        parts.append(conclusion_para)
        parts.append("")

    parts.append(closing)
    parts.append("")
    parts.append(sign_off)
    parts.append(display_name)

    body = "\n".join(parts).strip()

    return {"subject": subject, "body": body}
