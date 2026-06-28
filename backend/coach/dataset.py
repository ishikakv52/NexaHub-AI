"""
dataset.py — Complete offline English teaching dataset.
No API key required. All responses generated from this rich local knowledge base.
Covers: Grammar, Vocabulary, Pronunciation, Speaking, Interview, Translation hints,
        Daily Challenges, and general English learning for Indian learners.
"""

import random
import re
import json
import os
from difflib import get_close_matches

# ══════════════════════════════════════════════════════════════════
#  GRAMMAR RULES DATABASE
# ══════════════════════════════════════════════════════════════════

GRAMMAR_RULES = {
    "tenses": {
        "present_simple": {
            "rule": "Subject + V1 (he/she/it → V1+s)",
            "uses": ["Habits", "Facts", "Schedules", "General truths"],
            "examples": [
                "I go to school every day.",
                "She works in a hospital.",
                "The sun rises in the east.",
                "They play cricket on weekends.",
                "He studies for two hours daily."
            ],
            "common_mistakes": [
                {"wrong": "She don't like tea.", "correct": "She doesn't like tea.", "rule": "Use 'doesn't' with he/she/it"},
                {"wrong": "He go to office.", "correct": "He goes to office.", "rule": "Add 's' for he/she/it"},
                {"wrong": "They plays cricket.", "correct": "They play cricket.", "rule": "No 's' with they/we/I/you"},
            ]
        },
        "present_continuous": {
            "rule": "Subject + is/am/are + V-ing",
            "uses": ["Action happening now", "Temporary situations", "Future arrangements"],
            "examples": [
                "I am studying right now.",
                "She is working from home these days.",
                "They are playing in the garden.",
                "We are meeting tomorrow.",
                "He is learning English this year."
            ],
            "common_mistakes": [
                {"wrong": "I am knowing the answer.", "correct": "I know the answer.", "rule": "Stative verbs (know/like/want) don't use -ing"},
                {"wrong": "She is go to market.", "correct": "She is going to market.", "rule": "Use V-ing after is/am/are"},
                {"wrong": "They are plays cricket.", "correct": "They are playing cricket.", "rule": "is/am/are + V-ing, not V1"},
            ]
        },
        "present_perfect": {
            "rule": "Subject + has/have + V3 (past participle)",
            "uses": ["Past action with present result", "Life experience", "Just completed action", "Since/For"],
            "examples": [
                "I have finished my homework.",
                "She has lived here for 10 years.",
                "They have visited Paris twice.",
                "He has just arrived.",
                "We have known each other since 2010."
            ],
            "common_mistakes": [
                {"wrong": "I have went to Delhi.", "correct": "I have gone to Delhi.", "rule": "Use past participle (V3), not past tense (V2)"},
                {"wrong": "She has came yesterday.", "correct": "She came yesterday.", "rule": "Present perfect not used with specific past time (yesterday/last year)"},
                {"wrong": "I am living here since 5 years.", "correct": "I have been living here for 5 years.", "rule": "Use 'have been + V-ing' with since/for for ongoing actions"},
            ]
        },
        "past_simple": {
            "rule": "Subject + V2 (regular: +ed, irregular: learn separately)",
            "uses": ["Completed past action", "Past habits", "Past states"],
            "examples": [
                "I went to the market yesterday.",
                "She studied all night.",
                "They won the match last week.",
                "He worked here for 3 years.",
                "We watched a movie on Sunday."
            ],
            "common_mistakes": [
                {"wrong": "I buyed a new phone.", "correct": "I bought a new phone.", "rule": "buy → bought (irregular verb)"},
                {"wrong": "She goed to Delhi.", "correct": "She went to Delhi.", "rule": "go → went (irregular verb)"},
                {"wrong": "He did not went.", "correct": "He did not go.", "rule": "After did/didn't, use V1 (base form)"},
            ]
        },
        "past_continuous": {
            "rule": "Subject + was/were + V-ing",
            "uses": ["Action in progress at a past time", "Two actions happening simultaneously", "Background action interrupted"],
            "examples": [
                "I was sleeping when you called.",
                "She was cooking dinner at 7 PM.",
                "They were playing when it started raining.",
                "He was working all night.",
                "We were watching TV when the power went out."
            ],
            "common_mistakes": [
                {"wrong": "I was study when you came.", "correct": "I was studying when you came.", "rule": "was/were + V-ing"},
                {"wrong": "They were go to market.", "correct": "They were going to market.", "rule": "was/were + V-ing, not V1"},
            ]
        },
        "future_simple": {
            "rule": "Subject + will + V1",
            "uses": ["Future decisions", "Promises", "Predictions", "Offers"],
            "examples": [
                "I will help you tomorrow.",
                "She will come to the party.",
                "It will rain tonight.",
                "We will finish the project by Friday.",
                "He will not disappoint you."
            ],
            "common_mistakes": [
                {"wrong": "I will going to Delhi.", "correct": "I will go to Delhi.", "rule": "will + V1 (base form, not V-ing)"},
                {"wrong": "She wills come.", "correct": "She will come.", "rule": "will never takes 's'"},
            ]
        },
        "future_going_to": {
            "rule": "Subject + is/am/are + going to + V1",
            "uses": ["Plans already decided", "Predictions based on evidence"],
            "examples": [
                "I am going to start a new job next month.",
                "She is going to have a baby.",
                "They are going to travel to Europe.",
                "He is going to study medicine.",
                "We are going to renovate the house."
            ],
            "common_mistakes": [
                {"wrong": "I am going to went.", "correct": "I am going to go.", "rule": "going to + V1 (base form)"},
                {"wrong": "She go to become a doctor.", "correct": "She is going to become a doctor.", "rule": "Use is/am/are + going to"},
            ]
        },
    },

    "articles": {
        "a_an": {
            "rule": "'a' before consonant sounds, 'an' before vowel sounds",
            "examples": [
                "a university (u sounds like 'yoo' — consonant sound)",
                "an hour (h is silent — vowel sound)",
                "a European country",
                "an honest man",
                "a one-rupee coin (o sounds like 'w')"
            ],
            "common_mistakes": [
                {"wrong": "She is an university student.", "correct": "She is a university student.", "rule": "'university' starts with 'y' sound"},
                {"wrong": "He is a honest man.", "correct": "He is an honest man.", "rule": "'h' in 'honest' is silent"},
                {"wrong": "I need an useful tool.", "correct": "I need a useful tool.", "rule": "'useful' starts with 'y' sound"},
            ]
        },
        "the": {
            "rule": "Use 'the' for specific, known, or unique nouns",
            "examples": [
                "The sun rises in the east.",
                "Can you pass the salt? (specific salt on table)",
                "The President of India",
                "I am going to the market. (specific, known)",
                "The Taj Mahal is beautiful."
            ],
            "common_mistakes": [
                {"wrong": "I go to the school every day.", "correct": "I go to school every day.", "rule": "No 'the' with school/college/hospital when going for its purpose"},
                {"wrong": "She is best student.", "correct": "She is the best student.", "rule": "Use 'the' with superlatives"},
                {"wrong": "He plays the cricket.", "correct": "He plays cricket.", "rule": "No article with sports/games"},
            ]
        },
        "zero_article": {
            "rule": "No article with: proper nouns, languages, sports, meals, abstract nouns (usually)",
            "examples": [
                "She speaks Hindi and English.",
                "I play cricket every evening.",
                "Breakfast is served at 8.",
                "Love is a beautiful feeling.",
                "He studies medicine at Delhi University."
            ]
        }
    },

    "prepositions": {
        "time": {
            "at": ["at 5 o'clock", "at midnight", "at noon", "at the weekend (British)"],
            "on": ["on Monday", "on 15th August", "on my birthday", "on Christmas Day"],
            "in": ["in January", "in 2024", "in the morning", "in the 21st century"],
            "common_mistakes": [
                {"wrong": "I will meet you on 5 o'clock.", "correct": "I will meet you at 5 o'clock.", "rule": "Use 'at' for specific times"},
                {"wrong": "She was born in Sunday.", "correct": "She was born on Sunday.", "rule": "Use 'on' for days"},
                {"wrong": "He arrived at January.", "correct": "He arrived in January.", "rule": "Use 'in' for months and years"},
            ]
        },
        "place": {
            "at": ["at the bus stop", "at home", "at work", "at the corner"],
            "on": ["on the table", "on the wall", "on the floor", "on page 5"],
            "in": ["in the box", "in Delhi", "in India", "in the room"],
            "common_mistakes": [
                {"wrong": "She is in the bus stop.", "correct": "She is at the bus stop.", "rule": "Use 'at' for specific points/locations"},
                {"wrong": "The book is at the table.", "correct": "The book is on the table.", "rule": "Use 'on' for surfaces"},
                {"wrong": "He lives on Delhi.", "correct": "He lives in Delhi.", "rule": "Use 'in' for cities and countries"},
            ]
        }
    },

    "subject_verb_agreement": {
        "rule": "Singular subject → singular verb; Plural subject → plural verb",
        "examples": [
            "The dog barks loudly. (singular)",
            "The dogs bark loudly. (plural)",
            "Each student has a book.",
            "Neither of them is ready.",
            "The news is shocking. (news is singular)"
        ],
        "common_mistakes": [
            {"wrong": "The team are playing well.", "correct": "The team is playing well.", "rule": "Collective nouns (team/group/family) take singular verb (American English)"},
            {"wrong": "Mathematics are difficult.", "correct": "Mathematics is difficult.", "rule": "Subject ending in -ics is usually singular"},
            {"wrong": "Everyone are invited.", "correct": "Everyone is invited.", "rule": "Everyone/somebody/anyone takes singular verb"},
            {"wrong": "Neither Ram nor Shyam are coming.", "correct": "Neither Ram nor Shyam is coming.", "rule": "Neither...nor: verb agrees with nearer subject"},
        ]
    },

    "conditionals": {
        "zero": {
            "structure": "If + present simple, present simple",
            "use": "General truths, scientific facts",
            "examples": [
                "If you heat water to 100°C, it boils.",
                "If it rains, the ground gets wet.",
                "Plants die if they don't get water."
            ]
        },
        "first": {
            "structure": "If + present simple, will + V1",
            "use": "Real/possible future situations",
            "examples": [
                "If it rains tomorrow, I will stay home.",
                "If you study hard, you will pass.",
                "She will get the job if she works hard."
            ]
        },
        "second": {
            "structure": "If + past simple, would + V1",
            "use": "Imaginary/unlikely present situations",
            "examples": [
                "If I had a million rupees, I would travel the world.",
                "If she were the president, she would change the laws.",
                "I would help you if I could."
            ]
        },
        "third": {
            "structure": "If + past perfect, would have + V3",
            "use": "Imaginary past situations (regrets)",
            "examples": [
                "If I had studied harder, I would have passed.",
                "She would have got the job if she had tried.",
                "They would have won if they had played better."
            ]
        }
    },

    "reported_speech": {
        "rule": "Tense moves one step back in reported speech",
        "changes": {
            "am/is/are → was/were",
            "will → would",
            "can → could",
            "may → might",
            "present simple → past simple",
            "present continuous → past continuous",
            "present perfect → past perfect"
        },
        "examples": [
            "Direct: 'I am happy.' → Reported: She said she was happy.",
            "Direct: 'I will come.' → Reported: He said he would come.",
            "Direct: 'I have finished.' → Reported: She said she had finished.",
        ]
    },

    "passive_voice": {
        "rule": "Object + is/am/are/was/were + V3 (+ by + agent)",
        "examples": [
            "Active: Ram writes a letter. → Passive: A letter is written by Ram.",
            "Active: Police caught the thief. → Passive: The thief was caught by the police.",
            "Active: They are building a bridge. → Passive: A bridge is being built.",
        ],
        "common_mistakes": [
            {"wrong": "A letter was wrote by him.", "correct": "A letter was written by him.", "rule": "Use past participle (V3) in passive"},
            {"wrong": "The work is did.", "correct": "The work is done.", "rule": "do → done (past participle)"},
        ]
    },

    "modals": {
        "can": {"use": "Ability / Permission / Possibility", "examples": ["I can swim.", "Can I use your phone?", "It can be dangerous."]},
        "could": {"use": "Past ability / Polite request / Possibility", "examples": ["I could run fast as a child.", "Could you help me?", "It could rain tomorrow."]},
        "must": {"use": "Strong obligation / Logical conclusion", "examples": ["You must wear a helmet.", "She must be tired after the journey."]},
        "should": {"use": "Advice / Recommendation / Duty", "examples": ["You should drink more water.", "Students should respect teachers."]},
        "may": {"use": "Formal permission / Possibility", "examples": ["May I come in?", "It may rain today."]},
        "might": {"use": "Slight possibility", "examples": ["She might come to the party.", "I might be wrong."]},
        "will": {"use": "Future / Willingness / Promise", "examples": ["I will help you.", "She will be here soon."]},
        "would": {"use": "Polite request / Past habit / Conditional", "examples": ["Would you like some tea?", "He would go for a walk every morning."]},
        "need": {"use": "Necessity / Lack of necessity", "examples": ["You need to study more.", "You needn't worry."]},
    },
}

# ══════════════════════════════════════════════════════════════════
#  MASSIVE VOCABULARY DATABASE
# ══════════════════════════════════════════════════════════════════

VOCABULARY = {
    "eloquent": {
        "meaning": "Fluent and persuasive in speaking or writing",
        "hindi": "वाकपटु, प्रभावशाली वक्ता",
        "pronunciation": "EL-oh-kwent",
        "ipa": "/ˈeləkwənt/",
        "synonyms": ["articulate", "fluent", "expressive", "persuasive", "well-spoken"],
        "antonyms": ["inarticulate", "tongue-tied", "halting", "stammering"],
        "examples": [
            "She gave an eloquent speech at the conference.",
            "His eloquent writing style impressed the judges.",
            "The lawyer made an eloquent argument in court."
        ],
        "daily_usage": "Use it to describe good speakers, writers, or powerful speeches."
    },
    "perseverance": {
        "meaning": "Continued effort despite difficulty or delay in achieving success",
        "hindi": "दृढ़ता, लगन, हिम्मत",
        "pronunciation": "pur-suh-VEER-uns",
        "ipa": "/ˌpɜːrsɪˈvɪərəns/",
        "synonyms": ["persistence", "determination", "tenacity", "dedication", "endurance"],
        "antonyms": ["laziness", "giving up", "irresolution", "hesitation"],
        "examples": [
            "Her perseverance helped her clear the IAS exam after 4 attempts.",
            "Success comes to those who show perseverance.",
            "The athlete's perseverance paid off when she won the gold medal."
        ],
        "daily_usage": "Use when talking about not giving up despite failures."
    },
    "ambiguous": {
        "meaning": "Open to more than one interpretation; unclear",
        "hindi": "अस्पष्ट, दो अर्थ वाला",
        "pronunciation": "am-BIG-yoo-us",
        "ipa": "/æmˈbɪɡjuəs/",
        "synonyms": ["unclear", "vague", "uncertain", "obscure", "equivocal"],
        "antonyms": ["clear", "definite", "explicit", "obvious", "unambiguous"],
        "examples": [
            "His answer was ambiguous — we weren't sure if he agreed or not.",
            "The new policy is ambiguous and needs clarification.",
            "Avoid ambiguous language in official documents."
        ],
        "daily_usage": "Use when something can be understood in two different ways."
    },
    "procrastinate": {
        "meaning": "To delay or postpone doing something",
        "hindi": "टालमटोल करना, काम को आगे के लिए टालना",
        "pronunciation": "pro-KRAS-tuh-nayt",
        "ipa": "/prəˈkræstɪneɪt/",
        "synonyms": ["delay", "postpone", "put off", "defer", "dawdle"],
        "antonyms": ["act immediately", "tackle", "begin", "prioritize"],
        "examples": [
            "Don't procrastinate — finish your assignment today.",
            "He always procrastinates and then rushes at the last minute.",
            "Students who procrastinate often perform poorly in exams."
        ],
        "daily_usage": "Very common word! Use it to talk about delaying important tasks."
    },
    "meticulous": {
        "meaning": "Showing great attention to detail; very careful and precise",
        "hindi": "बहुत सावधान, बारीकी से काम करने वाला",
        "pronunciation": "meh-TIK-yoo-lus",
        "ipa": "/məˈtɪkjələs/",
        "synonyms": ["thorough", "careful", "precise", "detailed", "painstaking"],
        "antonyms": ["careless", "sloppy", "hasty", "negligent"],
        "examples": [
            "She is meticulous in her work — not a single mistake.",
            "A meticulous approach is required in surgery.",
            "His meticulous planning made the event a huge success."
        ],
        "daily_usage": "Use to praise someone who does very careful, detailed work."
    },
    "inevitable": {
        "meaning": "Certain to happen; unavoidable",
        "hindi": "अटल, जो टाला न जा सके",
        "pronunciation": "in-EV-ih-tuh-bul",
        "ipa": "/ɪnˈevɪtəbl/",
        "synonyms": ["unavoidable", "certain", "inescapable", "destined", "sure"],
        "antonyms": ["avoidable", "preventable", "uncertain", "escapable"],
        "examples": [
            "Change is inevitable — accept it with a positive mindset.",
            "With such poor preparation, failure was inevitable.",
            "Death and taxes are inevitable, as they say."
        ],
        "daily_usage": "Use when something cannot be avoided or stopped."
    },
    "empathy": {
        "meaning": "The ability to understand and share the feelings of another person",
        "hindi": "दूसरों की भावनाओं को समझना, सहानुभूति",
        "pronunciation": "EM-puh-thee",
        "ipa": "/ˈempəθi/",
        "synonyms": ["compassion", "understanding", "sensitivity", "sympathy", "care"],
        "antonyms": ["indifference", "coldness", "apathy", "insensitivity"],
        "examples": [
            "A good doctor shows empathy towards patients.",
            "Empathy is an important quality in a leader.",
            "She showed great empathy when her friend lost his job."
        ],
        "daily_usage": "Very important word in interviews! Shows emotional intelligence."
    },
    "candid": {
        "meaning": "Truthful and straightforward; frank",
        "hindi": "स्पष्टवादी, खुलकर बोलने वाला",
        "pronunciation": "KAN-did",
        "ipa": "/ˈkændɪd/",
        "synonyms": ["frank", "honest", "open", "direct", "straightforward"],
        "antonyms": ["dishonest", "evasive", "secretive", "indirect"],
        "examples": [
            "I want your candid opinion on my presentation.",
            "She was candid about her mistakes in the meeting.",
            "A candid conversation helped resolve their misunderstanding."
        ],
        "daily_usage": "Use in professional situations to show honesty and transparency."
    },
    "pragmatic": {
        "meaning": "Dealing with things in a practical way rather than theoretically",
        "hindi": "व्यावहारिक, व्यवहार में लागू होने वाला",
        "pronunciation": "prag-MAT-ik",
        "ipa": "/præɡˈmætɪk/",
        "synonyms": ["practical", "realistic", "sensible", "down-to-earth", "rational"],
        "antonyms": ["idealistic", "impractical", "unrealistic", "theoretical"],
        "examples": [
            "We need a pragmatic solution to this problem.",
            "She is pragmatic — she focuses on what works, not what's ideal.",
            "A pragmatic approach to business always yields better results."
        ],
        "daily_usage": "Great interview word! Shows practical thinking and problem-solving."
    },
    "resilient": {
        "meaning": "Able to recover quickly from difficulties; tough",
        "hindi": "मुश्किलों से उबरने में सक्षम, लचीला",
        "pronunciation": "rih-ZIL-yunt",
        "ipa": "/rɪˈzɪliənt/",
        "synonyms": ["tough", "strong", "adaptable", "flexible", "hardy"],
        "antonyms": ["fragile", "weak", "vulnerable", "sensitive"],
        "examples": [
            "She is resilient — she bounced back after every failure.",
            "India's economy proved resilient despite the global crisis.",
            "Children are more resilient than we think."
        ],
        "daily_usage": "Perfect for interviews when talking about handling challenges."
    },
    "diligent": {
        "meaning": "Showing care and effort in work or duties",
        "hindi": "मेहनती, परिश्रमी",
        "pronunciation": "DIL-ih-junt",
        "ipa": "/ˈdɪlɪdʒənt/",
        "synonyms": ["hardworking", "industrious", "dedicated", "persistent", "careful"],
        "antonyms": ["lazy", "careless", "negligent", "idle"],
        "examples": [
            "She is a diligent student who never misses a class.",
            "Diligent workers are always valued by their employers.",
            "His diligent preparation helped him crack the interview."
        ],
        "daily_usage": "Excellent word for résumés and interviews to describe your work ethic."
    },
    "concise": {
        "meaning": "Giving a lot of information in few words; brief and clear",
        "hindi": "संक्षिप्त, कम शब्दों में स्पष्ट",
        "pronunciation": "kun-SICE",
        "ipa": "/kənˈsaɪs/",
        "synonyms": ["brief", "succinct", "compact", "short", "to-the-point"],
        "antonyms": ["wordy", "verbose", "lengthy", "long-winded"],
        "examples": [
            "Please give a concise answer in the interview.",
            "A good essay should be concise and well-structured.",
            "The manager appreciated the concise report."
        ],
        "daily_usage": "Important in professional communication — being concise is valued."
    },
    "acknowledge": {
        "meaning": "To accept or admit the existence or truth of something",
        "hindi": "स्वीकार करना, माना की",
        "pronunciation": "ak-NOL-ij",
        "ipa": "/əkˈnɒlɪdʒ/",
        "synonyms": ["admit", "accept", "recognize", "confirm", "concede"],
        "antonyms": ["deny", "refuse", "ignore", "reject"],
        "examples": [
            "He acknowledged his mistake and apologized.",
            "The manager acknowledged the team's hard work.",
            "Please acknowledge receipt of this email."
        ],
        "daily_usage": "Very useful in emails and professional communication."
    },
    "initiative": {
        "meaning": "The ability to take action without being told to; a new plan",
        "hindi": "पहल करना, खुद से काम शुरू करना",
        "pronunciation": "ih-NISH-ee-uh-tiv",
        "ipa": "/ɪˈnɪʃɪətɪv/",
        "synonyms": ["enterprise", "drive", "ambition", "resourcefulness", "leadership"],
        "antonyms": ["passivity", "inaction", "laziness", "reluctance"],
        "examples": [
            "She took the initiative and started the project without being asked.",
            "Employers look for candidates who show initiative.",
            "The government launched a new initiative for women's education."
        ],
        "daily_usage": "Key HR interview word. Shows leadership and self-motivation."
    },
    "collaborate": {
        "meaning": "To work jointly with others",
        "hindi": "मिलकर काम करना, सहयोग करना",
        "pronunciation": "kuh-LAB-uh-rayt",
        "ipa": "/kəˈlæbəreɪt/",
        "synonyms": ["cooperate", "work together", "partner", "team up", "join forces"],
        "antonyms": ["compete", "work alone", "oppose", "hinder"],
        "examples": [
            "The two departments collaborated to complete the project.",
            "I love to collaborate with creative people.",
            "We need to collaborate if we want to succeed."
        ],
        "daily_usage": "Essential word for teamwork discussions in interviews."
    },
    "integrity": {
        "meaning": "The quality of being honest and having strong moral principles",
        "hindi": "ईमानदारी, नैतिकता",
        "pronunciation": "in-TEG-ruh-tee",
        "ipa": "/ɪnˈteɡrɪti/",
        "synonyms": ["honesty", "ethics", "morality", "honor", "virtue"],
        "antonyms": ["dishonesty", "corruption", "deceit", "immorality"],
        "examples": [
            "A leader must have integrity to earn trust.",
            "He showed great integrity by returning the extra money.",
            "Integrity is the foundation of a good character."
        ],
        "daily_usage": "Top word used in HR interviews when asked about values."
    },
    "versatile": {
        "meaning": "Able to adapt or be used for many different purposes",
        "hindi": "बहुमुखी, हर काम में कुशल",
        "pronunciation": "VUR-suh-tul",
        "ipa": "/ˈvɜːrsətl/",
        "synonyms": ["adaptable", "flexible", "all-round", "multitalented", "resourceful"],
        "antonyms": ["limited", "specialized only", "inflexible", "narrow"],
        "examples": [
            "He is a versatile actor who can play any role.",
            "Python is a versatile programming language.",
            "A versatile employee is an asset to any company."
        ],
        "daily_usage": "Use to describe your own skills or someone who can do many things."
    },
    "proficient": {
        "meaning": "Competent and skilled in doing or using something",
        "hindi": "दक्ष, किसी काम में माहिर",
        "pronunciation": "pruh-FISH-unt",
        "ipa": "/prəˈfɪʃənt/",
        "synonyms": ["skilled", "expert", "capable", "competent", "adept"],
        "antonyms": ["incompetent", "unskilled", "inept", "amateur"],
        "examples": [
            "She is proficient in three languages.",
            "He is proficient in Python and Java.",
            "You need to be proficient in Excel for this job."
        ],
        "daily_usage": "Use on résumés: 'Proficient in MS Office / Python / Excel'."
    },
    "endeavor": {
        "meaning": "To try hard to do or achieve something; an attempt",
        "hindi": "प्रयास करना, कोशिश करना",
        "pronunciation": "en-DEV-ur",
        "ipa": "/ɪnˈdevər/",
        "synonyms": ["attempt", "try", "strive", "effort", "aim"],
        "antonyms": ["give up", "abandon", "neglect", "ignore"],
        "examples": [
            "I will endeavor to complete the task on time.",
            "Despite all endeavors, the project failed.",
            "She endeavored to learn something new every day."
        ],
        "daily_usage": "Formal word. Great for formal emails and professional writing."
    },
    "subsequently": {
        "meaning": "Coming after something else; afterwards",
        "hindi": "बाद में, उसके पश्चात्",
        "pronunciation": "SUB-suh-kwent-lee",
        "ipa": "/ˈsʌbsɪkwəntli/",
        "synonyms": ["afterwards", "later", "then", "thereafter", "following this"],
        "antonyms": ["previously", "before", "earlier", "prior to"],
        "examples": [
            "He failed the exam; subsequently, he worked harder.",
            "The plan was approved and subsequently implemented.",
            "She joined the company in 2020 and subsequently became the manager."
        ],
        "daily_usage": "Very useful connecting word in formal writing and reports."
    },
}

# ══════════════════════════════════════════════════════════════════
#  PRONUNCIATION GUIDE
# ══════════════════════════════════════════════════════════════════

PRONUNCIATION_GUIDE = {
    "common_indian_mistakes": [
        {
            "sound": "TH",
            "problem": "Indian speakers say 'D' or 'T' instead of 'TH'",
            "wrong": "'dis' for 'this', 'tree' for 'three'",
            "correct": "Put tongue lightly between teeth for voiced TH (this/the/they) and voiceless TH (think/thank/three)",
            "practice": ["the", "this", "that", "there", "three", "think", "thank", "through", "thirty", "Thursday"]
        },
        {
            "sound": "W vs V",
            "problem": "Mixing up W and V sounds",
            "wrong": "'vine' for 'wine', 'wery' for 'very'",
            "correct": "W: round lips like blowing — 'wine/water/work'. V: upper teeth touch lower lip — 'very/visit/value'",
            "practice": ["wine/vine", "west/vest", "wet/vet", "worse/verse", "while/vile"]
        },
        {
            "sound": "Short vs Long Vowels",
            "problem": "Not differentiating between short and long vowel sounds",
            "wrong": "'ship' and 'sheep' sound the same",
            "correct": "ship (short i) vs sheep (long ee). bit vs beat. full vs fool.",
            "practice": ["ship/sheep", "bit/beat", "full/fool", "pull/pool", "sit/seat"]
        },
        {
            "sound": "Final Consonants",
            "problem": "Adding 'a' sound at end of words or dropping final consonants",
            "wrong": "'boka' for 'book', 'doga' for 'dog'",
            "correct": "Practice ending words cleanly. Don't add vowel after final consonant.",
            "practice": ["book", "dog", "cat", "stop", "walk", "talk", "park", "dark"]
        },
        {
            "sound": "Silent Letters",
            "problem": "Pronouncing every letter",
            "wrong": "Saying 'k' in 'knife', 'l' in 'walk'",
            "correct": "knife=NIFE, know=NO, walk=WAWK, talk=TAWK, would=WUD, could=KUD",
            "practice": ["knife", "know", "knight", "walk", "talk", "calm", "would", "could", "should", "hour"]
        },
        {
            "sound": "P vs F",
            "problem": "Using 'P' sound instead of 'F' sound",
            "wrong": "'pire' for 'fire', 'pone' for 'phone'",
            "correct": "F: upper teeth lightly on lower lip, push air out — 'fire/phone/feel/fun'",
            "practice": ["fire", "phone", "feel", "fun", "family", "from", "first", "food", "fall", "find"]
        },
        {
            "sound": "R sound",
            "problem": "Over-rolling or trilling the R (Indian accent)",
            "wrong": "Rolling the R too much in words like 'very', 'river'",
            "correct": "In standard English, R is softer. Tongue does NOT vibrate. Curl tongue tip slightly upward — 'river, red, right'",
            "practice": ["right", "river", "round", "red", "real", "road", "rich", "rock", "race", "rule"]
        },
        {
            "sound": "Schwa Sound (ə)",
            "problem": "Pronouncing every vowel clearly instead of reducing unstressed vowels",
            "wrong": "Saying 'a-bout' fully instead of 'uh-BOUT'",
            "correct": "Unstressed syllables use the schwa (ə) — a short 'uh' sound. about=uh-BOUT, today=tuh-DAY",
            "practice": ["about", "today", "banana", "problem", "pencil", "sofa", "camera", "attend", "police", "complete"]
        },
        {
            "sound": "Long A vs Short A",
            "problem": "Not distinguishing between 'a' in 'cat' vs 'a' in 'cake'",
            "wrong": "Making both sounds the same",
            "correct": "cat (short a: æ), cake (long a: eɪ). man vs mane. tap vs tape.",
            "practice": ["cat/cake", "man/mane", "tap/tape", "cap/cape", "hat/hate", "ran/rain"]
        },
        {
            "sound": "OO vs U",
            "problem": "Not distinguishing between long OO (food) and short U (foot)",
            "wrong": "Pronouncing 'foot' like 'food'",
            "correct": "food = long OO (fuːd). foot = short U (fʊt). pool vs pull. fool vs full.",
            "practice": ["food/foot", "pool/pull", "fool/full", "boot/book", "mood/wood", "cool/cook"]
        },
        {
            "sound": "NG Sound",
            "problem": "Pronouncing the 'g' in '-ng' words or dropping the ng sound",
            "wrong": "Saying 'runnin' or 'runninG' (hard G) instead of 'running'",
            "correct": "The 'ng' sound is one nasal sound at the back of throat — no separate G. singing, ring, thing",
            "practice": ["running", "singing", "ring", "thing", "bring", "long", "strong", "wrong", "tongue", "king"]
        },
        {
            "sound": "ED Endings",
            "problem": "Always pronouncing '-ed' as 'ed'",
            "wrong": "'walked-ed' or 'talkEd' with full vowel sound",
            "correct": "After voiceless consonants → /t/ (walked, talked). After voiced consonants → /d/ (moved, called). After t/d → /ɪd/ (wanted, needed)",
            "practice": ["walked=walkt", "talked=talkt", "moved=moovd", "called=cawld", "wanted=wontid", "needed=needid"]
        },
        {
            "sound": "S vs Z at end of words",
            "problem": "Pronouncing all 's' endings as /s/",
            "wrong": "Saying 'dogss' instead of 'dogz'",
            "correct": "After voiced sounds, plural S is pronounced /z/: dogs=dogz, cars=carz, bags=bagz. After voiceless: cats=catss",
            "practice": ["dogs=dogz", "cars=carz", "bags=bagz", "cats=catss", "books=bookss", "his=hiz"]
        },
        {
            "sound": "Stress on Wrong Syllable",
            "problem": "Placing stress on wrong syllable in multi-syllable words",
            "wrong": "PROgress instead of proGRESS (verb), CEment instead of ceMENT",
            "correct": "Nouns: stress first syllable. Verbs: stress second syllable. PREsent vs preSENT. REcord vs reCORD.",
            "practice": ["PREsent/preSENT", "REcord/reCORD", "PROtest/proTEST", "OBject/obJECT", "INcrease/inCREASE"]
        },
        {
            "sound": "Z sound",
            "problem": "Not using the Z sound in words where it appears",
            "wrong": "'Soo' for 'Zoo', 'Sero' for 'Zero'",
            "correct": "Z is voiced — vocal cords vibrate. Zero=Zeero (buzz sound). Zip, zeal, zone, jazz.",
            "practice": ["zero", "zoo", "zone", "zip", "buzz", "jazz", "pizza", "quiz", "freeze", "realize"]
        },
        {
            "sound": "H Sound",
            "problem": "Dropping or over-emphasizing the H",
            "wrong": "Saying 'im' for 'him', or breathing too heavily on H",
            "correct": "H is a soft breath of air — 'hello, happy, him, her, house, have'",
            "practice": ["hello", "happy", "him", "her", "house", "have", "heat", "hill", "hope", "help"]
        },
        {
            "sound": "Linking Words",
            "problem": "Speaking every word separately without linking",
            "wrong": "Saying 'I am eating' with full pause between each word",
            "correct": "In natural English, words link together: 'I_am_eating' sounds like 'I'meating'. Consonant + vowel link strongly.",
            "practice": ["an apple=anapple", "at all=atall", "get on=geton", "pick up=pickup", "not at all=notatall"]
        },
        {
            "sound": "CH vs SH",
            "problem": "Mixing up CH and SH sounds",
            "wrong": "'sheep' for 'cheap', 'shop' for 'chop'",
            "correct": "CH: tongue touches roof of mouth, releases — 'cheap/church/chair'. SH: tongue stays back, no release — 'sheep/share/shine'",
            "practice": ["cheap/sheep", "chair/share", "chin/shin", "chop/shop", "cheese/she's", "chip/ship"]
        },
        {
            "sound": "OW vs AH",
            "problem": "Not distinguishing 'ow' (cow) from 'oh' (no)",
            "wrong": "Pronouncing 'cow' like 'co'",
            "correct": "ow (cow, now, how): mouth opens wide then rounds. oh (no, go, show): lips form an O shape.",
            "practice": ["cow/go", "now/no", "how/hoe", "out/oat", "down/done", "found/fond"]
        },
        {
            "sound": "Clear vs Dark L",
            "problem": "Using only one type of L in all positions",
            "wrong": "Same L sound in 'light' and 'ball'",
            "correct": "Clear L at start (light, love, like) — tongue touches ridge. Dark L at end (ball, full, milk) — tongue stays low.",
            "practice": ["light vs ball", "love vs well", "like vs milk", "look vs pull", "leap vs feel", "late vs halt"]
        },
    ],
    "word_stress_rules": [
        "Two-syllable NOUNS: stress on FIRST syllable — PREsent, REcord, OBject, PROtest",
        "Two-syllable VERBS: stress on SECOND syllable — preSENT, reCORD, obJECT, proTEST",
        "Words ending in -tion/-sion: stress on syllable BEFORE — inforMAtion, educAtion, telEVision",
        "Words ending in -ic: stress on syllable BEFORE — photoGRAPHic, econOMic, autoMATic",
        "Compound nouns: stress on FIRST part — BLACKboard, BUSstop, FOOTball",
        "Phrasal verbs: stress on PARTICLE — stand UP, sit DOWN, give IN",
        "Words ending in -ity: stress on syllable before -ity — aBILity, posSIBility, creaTIVity",
        "Words ending in -ous: stress shifts backward — DANgerous, FAMous, SERious",
        "Three-syllable words often stress the MIDDLE — underSTAND, enterTAIN, reCOGnize",
        "Content words (nouns, verbs, adjectives) are stressed; function words (the, a, of) are reduced",
    ],
    "tongue_twisters": [
        "She sells seashells by the seashore.",
        "Red lorry, yellow lorry.",
        "Peter Piper picked a peck of pickled peppers.",
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
        "The thirty-three thieves thought that they thrilled the throne throughout Thursday.",
        "Whether the weather is fine or whether the weather is not, we'll weather the weather.",
        "Six sick slick slim sycamore saplings.",
        "I scream, you scream, we all scream for ice cream.",
        "Betty Botter bought some butter but the butter was bitter.",
        "A big black bug bit a big black bear.",
        "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair. Fuzzy Wuzzy wasn't very fuzzy, was he?",
        "Which witch is which? Which witch switched the Swiss wristwatches?",
        "I saw Susie sitting in a shoeshine shop. Where she sits she shines.",
        "Can you can a can as a canner can can a can?",
        "Unique New York, unique New York, you know you need unique New York.",
        "The seething sea ceaseth and thus the seething sea sufficeth us.",
        "Fred fed Ted bread, and Ted fed Fred bread.",
        "How can a clam cram in a clean cream can?",
        "Lesser leather never weathered wetter weather better.",
        "We surely shall see the sun shine soon.",
    ]
}

# ══════════════════════════════════════════════════════════════════
#  SPEAKING TOPICS DATABASE
# ══════════════════════════════════════════════════════════════════

SPEAKING_TOPICS = {
    "introduce": {
        "title": "Introduce Yourself",
        "prompt": "Talk about yourself — your name, background, education, hobbies, and goals.",
        "key_points": ["Full name and hometown", "Educational background", "Work experience (if any)", "Hobbies and interests", "Future goals"],
        "sample_vocabulary": ["I am originally from...", "I completed my degree in...", "I am currently working as...", "In my free time, I enjoy...", "My goal is to..."],
        "model_answer": "Good morning! My name is Rahul Sharma and I am from Lucknow, Uttar Pradesh. I completed my Bachelor's degree in Computer Science from Lucknow University in 2022. Currently, I am working as a junior software developer at a tech startup. In my free time, I enjoy reading books, playing cricket, and learning new technologies. My goal is to become a full-stack developer within the next two years and eventually start my own tech company.",
        "tips": ["Speak clearly and confidently", "Maintain eye contact", "Smile while speaking", "Don't rush — take your time", "Practice until it feels natural"]
    },
    "family": {
        "title": "My Family",
        "prompt": "Describe your family — members, relationships, values, and traditions.",
        "key_points": ["Family members and their professions", "Family values and traditions", "Role of family in your life", "Memorable family moments", "What family means to you"],
        "sample_vocabulary": ["My family consists of...", "My parents are...", "We follow the tradition of...", "Family plays a crucial role in...", "I am grateful for..."],
        "model_answer": "I come from a close-knit middle-class family of four. My father is a government employee and my mother is a homemaker who has dedicated her life to raising us. I have a younger sister who is currently pursuing her engineering degree. We follow the tradition of eating dinner together every evening, which gives us quality time to share our day's experiences. My family has always been my biggest support system, encouraging me during tough times and celebrating my achievements. I believe the values of hard work, honesty, and respect that my parents instilled in us have shaped my character significantly.",
        "tips": ["Use present tense for current situations", "Use specific examples", "Show emotion and warmth", "Expand on relationships, not just names"]
    },
    "college": {
        "title": "College Life",
        "prompt": "Share your college experiences — studies, friends, activities, and lessons learned.",
        "key_points": ["College name and course", "Academic experiences", "Extracurricular activities", "Friends and relationships", "Challenges faced", "Lessons learned"],
        "sample_vocabulary": ["I pursued my degree from...", "College taught me...", "I was involved in...", "One memorable experience was...", "I overcame the challenge of..."],
        "model_answer": "I pursued my Bachelor's degree from Delhi University, where I studied Economics for three years. College was a transformative experience for me. Academically, I consistently maintained good grades, but more importantly, I developed skills beyond the classroom. I was an active member of the debate club and the cultural committee, which significantly improved my communication and leadership skills. I made lifelong friends from different states and backgrounds, which broadened my perspective. The biggest challenge I faced was managing academics with extracurricular activities, but it taught me excellent time management skills. College shaped me into a confident, well-rounded individual.",
        "tips": ["Include both positive and challenging experiences", "Mention specific activities", "Show personal growth and learning"]
    },
    "job": {
        "title": "My Job / Career",
        "prompt": "Talk about your current job, career goals, and professional journey.",
        "key_points": ["Current role and company", "Daily responsibilities", "Skills you use", "Career achievements", "Future career goals", "Work-life balance"],
        "sample_vocabulary": ["I work as a... at...", "My responsibilities include...", "I am skilled in...", "My biggest professional achievement is...", "I aspire to..."],
        "model_answer": "I currently work as a Marketing Executive at a digital marketing agency in Noida. My primary responsibilities include managing social media campaigns, creating content strategy, and analyzing data to improve campaign performance. I use tools like Google Analytics, Hootsuite, and Canva on a daily basis. In the past year, I successfully led a campaign that increased our client's social media engagement by 40%, which was my biggest achievement so far. I am passionate about digital marketing and aspire to become a Marketing Manager within the next three years. I believe in maintaining a healthy work-life balance — I work efficiently during office hours and spend evenings on personal development.",
        "tips": ["Use specific numbers and achievements", "Show enthusiasm for your field", "Connect present role to future goals"]
    },
    "technology": {
        "title": "Technology",
        "prompt": "Discuss the role of technology in modern life — benefits, challenges, and future.",
        "key_points": ["Technology in daily life", "Benefits of technology", "Negative impacts", "AI and the future", "Technology and education", "Your personal views"],
        "sample_vocabulary": ["Technology has revolutionized...", "On one hand... on the other hand...", "Artificial Intelligence is...", "The biggest concern is...", "In the future, technology will..."],
        "model_answer": "Technology has fundamentally transformed every aspect of modern life. On one hand, it has made communication instantaneous, education accessible, and businesses more efficient. Platforms like YouTube have democratized education — I personally learned graphic design through free online tutorials. Artificial Intelligence is now changing entire industries, from healthcare to transportation. However, technology also has its challenges — excessive screen time affects mental health, and automation is causing job displacement. Cybersecurity threats and privacy concerns are growing rapidly. Despite these challenges, I believe technology, when used responsibly, is the most powerful tool humanity has. The key is digital literacy — teaching people how to use technology wisely.",
        "tips": ["Cover both pros and cons", "Use specific examples", "Share a personal connection to the topic", "Mention recent developments like AI"]
    },
    "health": {
        "title": "Health and Fitness",
        "prompt": "Discuss the importance of health, your fitness habits, and healthy lifestyle choices.",
        "key_points": ["Physical health importance", "Mental health", "Your exercise routine", "Diet and nutrition", "Stress management", "Healthy habits vs bad habits"],
        "sample_vocabulary": ["A healthy lifestyle includes...", "I make it a point to...", "Mental health is as important as...", "I follow a balanced diet of...", "One should avoid..."],
        "model_answer": "Good health is truly the greatest wealth one can possess. I believe in a holistic approach to health that includes both physical and mental well-being. I make it a point to exercise for at least 30 minutes every morning — I alternate between jogging and yoga. For nutrition, I follow a balanced diet rich in vegetables, proteins, and whole grains, while limiting junk food and sugary drinks. Mental health is equally important — I practice meditation for 15 minutes daily and maintain a journal to manage stress. In today's fast-paced world, many people neglect their health due to busy schedules, but I firmly believe that investing time in health today prevents major problems in the future.",
        "tips": ["Share personal habits and routines", "Distinguish between physical and mental health", "Use data and facts when possible"]
    },
    "hobbies": {
        "title": "Hobbies and Interests",
        "prompt": "Talk about your hobbies, passions, and how they enrich your life.",
        "key_points": ["Your main hobbies", "How you started", "Time you dedicate", "What you've learned from them", "How they benefit you professionally", "Future hobby goals"],
        "sample_vocabulary": ["I have a deep passion for...", "I took up... when...", "This hobby has taught me...", "I dedicate... hours per week to...", "Apart from being enjoyable, it also..."],
        "model_answer": "Reading is my greatest passion, and I try to read at least one book per month. I have a diverse taste — from fiction by Chetan Bhagat to self-help books like Atomic Habits. Apart from reading, I enjoy photography. I started taking photos during the pandemic to document everyday beauty around me, and it has since become a serious interest. Photography has taught me to observe the world more carefully and has greatly improved my visual communication skills, which are incredibly useful in my marketing career. I also enjoy cooking — especially trying regional Indian recipes. These hobbies keep me grounded, creative, and continuously learning, which I believe makes me a more well-rounded professional.",
        "tips": ["Choose hobbies you genuinely enjoy", "Connect hobbies to professional skills", "Show how hobbies shape your personality"]
    },
    "food": {
        "title": "Food and Cuisine",
        "prompt": "Discuss food culture, your favorites, cooking, and the relationship between food and culture.",
        "key_points": ["Your favorite foods", "Indian food culture", "Cooking experience", "Healthy eating", "Regional cuisines", "Food and social connections"],
        "sample_vocabulary": ["Indian cuisine is known for...", "My absolute favorite dish is...", "I have a special fondness for...", "Food in India varies greatly by region...", "Nothing brings people together like..."],
        "model_answer": "India's culinary diversity is one of its greatest treasures. Every state offers a unique gastronomic experience — from the spicy curries of Rajasthan to the coconut-based dishes of Kerala, the street food of Delhi to the sweets of Bengal. My absolute favorite dish is my mother's homemade rajma chawal — simple yet incredibly satisfying. I also love experimenting with cooking and have recently started making Italian pasta and Chinese stir-fries at home. Food, in Indian culture, is not just sustenance — it is an expression of love, hospitality, and tradition. Every festival, celebration, and family gathering revolves around food. I believe that understanding a culture through its food is one of the most delightful ways to connect with people.",
        "tips": ["Show appreciation for diversity", "Include personal stories", "Talk about food and culture connection"]
    },
    "travel": {
        "title": "Travel and Places",
        "prompt": "Share your travel experiences, favorite places, and the value of exploring new places.",
        "key_points": ["Places you've visited", "Favorite travel destination", "What you learned from travel", "Travel tips", "Dream destination", "Benefits of travelling"],
        "sample_vocabulary": ["Travel broadens one's perspective...", "The most memorable place I've visited is...", "What struck me most was...", "Travel has taught me...", "I dream of visiting..."],
        "model_answer": "Travel, for me, is the greatest education one can receive. I have been fortunate to visit several states in India — from the majestic forts of Rajasthan to the serene backwaters of Kerala, and the vibrant streets of Mumbai. The most memorable journey was a solo trip to Spiti Valley in Himachal Pradesh. The stark, beautiful landscape and the warm hospitality of the local people left a deep impression on me. Travel has taught me adaptability, open-mindedness, and appreciation for diverse cultures. It has also made me realize how vast and beautiful India is, and how much more there is to explore. My dream destination is Japan — a country that beautifully blends ancient traditions with cutting-edge modernity.",
        "tips": ["Use vivid, descriptive language", "Share personal stories from travel", "Connect travel to personal growth"]
    },
    "dreams": {
        "title": "Dreams and Goals",
        "prompt": "Share your dreams, long-term goals, and your plan to achieve them.",
        "key_points": ["Your short-term goals", "Long-term dreams", "Action plan", "Challenges you foresee", "Role models", "What motivates you"],
        "sample_vocabulary": ["My short-term goal is...", "In the next five years, I aspire to...", "I am working towards...", "The biggest obstacle is...", "I draw inspiration from..."],
        "model_answer": "I strongly believe that clarity of vision is the first step towards success. My immediate goal is to complete my digital marketing certification and become proficient in data analytics within the next six months. In the long term, I aspire to lead a digital marketing team for a multinational company and eventually launch my own social media marketing agency. I am working towards this dream by reading industry publications daily, taking online courses, and building a portfolio of projects. I am aware that the road will have challenges — competition is fierce and the industry evolves rapidly. But I draw inspiration from figures like Ratan Tata, who built a global empire through persistence and ethics. My greatest motivation is to make my parents proud and create a life where I can give back to my community.",
        "tips": ["Be specific about goals", "Show your action plan", "Connect dreams to values", "Be authentic and passionate"]
    },
    "environment": {
        "title": "Environment & Climate Change",
        "prompt": "Discuss environmental problems, their causes, and what individuals and governments should do.",
        "key_points": ["Major environmental issues today", "Causes of climate change", "Impact on India specifically", "What you personally do to help", "Government responsibilities", "Solutions for a sustainable future"],
        "sample_vocabulary": ["Climate change is one of the most pressing...", "In India, we face issues like...", "I personally try to...", "Governments must implement..."],
        "model_answer": "Climate change is undoubtedly the defining challenge of our generation. Rising temperatures, unpredictable monsoons, melting glaciers, and extreme weather events are all signs that our planet is in distress. India is particularly vulnerable — floods in Assam, droughts in Maharashtra, and shrinking water tables in the north all reflect this crisis. At a personal level, I try to reduce my carbon footprint by using public transport, avoiding single-use plastic, and conserving water. However, individual action alone is not enough. Governments must enforce strict emission standards, invest in renewable energy, and phase out fossil fuels.",
        "tips": ["Use real examples from India", "Balance individual and collective responsibility", "Show genuine concern"]
    },
    "social_media": {
        "title": "Social Media — Benefits & Dangers",
        "prompt": "Discuss the role of social media in modern life, its advantages and its negative impacts.",
        "key_points": ["How social media changed communication", "Benefits for individuals and businesses", "Mental health impact", "Misinformation and fake news", "Screen addiction", "How to use it responsibly"],
        "sample_vocabulary": ["Social media has transformed...", "On the positive side...", "However, one major concern is...", "To use it responsibly..."],
        "model_answer": "Social media has fundamentally changed how we communicate and build communities. It enables instant connection, gives voice to ordinary people, and creates opportunities for small businesses. However, excessive use has been linked to anxiety and depression, especially among teenagers. Misinformation spreads faster than truth, and addiction-by-design keeps users scrolling for hours. I use social media intentionally — consuming content that adds value and never comparing my real life with others' curated highlights.",
        "tips": ["Cover both positive and negative aspects", "Reference mental health impact", "Give practical usage tips"]
    },
    "education": {
        "title": "Education System in India",
        "prompt": "Discuss the Indian education system — its strengths, weaknesses, and how it should evolve.",
        "key_points": ["Strengths of the system", "Problems — rote learning and exam pressure", "NEP 2020 reforms", "Need for skill-based education", "Your personal experience"],
        "sample_vocabulary": ["The Indian education system produces...", "A major problem is...", "NEP 2020 aims to...", "Education should focus on..."],
        "model_answer": "India has one of the world's largest education systems, producing exceptional talent in STEM fields globally. However, our system suffers from over-reliance on rote learning over critical thinking. Exam pressure is immense, and many students choose streams based on societal pressure rather than interest. The New Education Policy 2020 is a welcome step — it emphasizes multidisciplinary learning, vocational skills, and regional languages. I believe education should nurture curiosity and emotional intelligence, not just the ability to score marks.",
        "tips": ["Reference NEP 2020", "Share your personal experience", "Be specific about reforms needed"]
    },
    "money": {
        "title": "Money Management & Financial Literacy",
        "prompt": "Talk about the importance of money management, saving, investing, and achieving financial independence.",
        "key_points": ["Importance of financial literacy", "Budgeting habits", "Investment options in India", "Common mistakes of youth", "Financial independence goal", "Your personal money habits"],
        "sample_vocabulary": ["Financial literacy means...", "A common mistake is...", "I follow the rule of...", "SIPs and mutual funds..."],
        "model_answer": "Financial literacy is one of the most important life skills schools rarely teach. Many young Indians fall into lifestyle inflation — earning more but spending more without saving. I follow the 50-30-20 rule: 50% on needs, 30% on wants, and 20% on savings and investments. I invest monthly in SIPs and maintain an emergency fund. My long-term goal is financial independence by 40 — not to stop working, but to have the freedom to choose how I work.",
        "tips": ["Use real instruments like SIP and PPF", "Share your own budgeting approach", "Connect money to life goals"]
    },
    "leadership": {
        "title": "Leadership & Management Skills",
        "prompt": "Discuss what makes a great leader, leadership styles, and your own leadership experiences.",
        "key_points": ["Definition of effective leadership", "Key qualities of a good leader", "Different leadership styles", "Leaders who inspired you", "Your own leadership experience", "Leadership in the Indian context"],
        "sample_vocabulary": ["Effective leadership means...", "The qualities I admire most are...", "One leader who inspired me is...", "My experience leading a team taught me..."],
        "model_answer": "Leadership is about inspiring people toward a shared goal while developing their potential. I admire empathy, vision, and the ability to remain calm under pressure. APJ Abdul Kalam exemplified servant leadership — humble, visionary, and tireless. In my own experience leading a college project team, I learned that understanding each member's strengths and keeping them motivated mattered far more than micromanaging. Great leaders create other leaders — they share credit, take blame, and invest in those around them.",
        "tips": ["Reference Indian leaders", "Use a personal leadership story", "Discuss servant vs transformational leadership"]
    },
    "sports": {
        "title": "Sports & Its Importance in Life",
        "prompt": "Discuss the role of sports in life — physical, mental, social, and national significance.",
        "key_points": ["Physical benefits", "Mental and emotional benefits", "Sports and national pride", "Your favorite sport or sportsperson", "Sports vs academic pressure in India", "Better sports infrastructure needed"],
        "sample_vocabulary": ["Beyond physical fitness, sports teach...", "Cricket in India is...", "My favorite sportsperson is...", "India needs to invest in..."],
        "model_answer": "Sports are powerful teachers of discipline, teamwork, resilience, and sportsmanship. Physically, they improve cardiovascular health and immunity. Mentally, they reduce stress and teach how to handle victory and defeat gracefully. Cricket unites a billion Indians and creates inspiring heroes. However, India must invest far more in non-cricket sports — kabaddi, wrestling, badminton, and athletics. Our Olympic performance shows how much untapped athletic potential exists in this country.",
        "tips": ["Go beyond cricket", "Connect sports to life lessons", "Discuss India's sporting infrastructure gap"]
    },
    "women_empowerment": {
        "title": "Women Empowerment in India",
        "prompt": "Discuss the importance of women's empowerment, progress made, and challenges that remain in India.",
        "key_points": ["What empowerment truly means", "Progress India has made", "Challenges that still exist", "Role of education", "Inspiring Indian women", "What individuals can do"],
        "sample_vocabulary": ["Women's empowerment means...", "India has made progress in...", "Challenges like... remain", "Education is the foundation of...", "Women like... have shown..."],
        "model_answer": "Women's empowerment means giving women freedom, resources, and opportunities to make their own decisions and contribute equally to society. India has made remarkable progress — women lead global corporations, win Olympic medals, command spacecraft, and head political parties. However, the gender pay gap, safety concerns, and limited rural education access remain serious challenges. Education is the most powerful tool for empowerment — an educated woman makes better decisions for herself, her family, and her community. As a society, we must actively challenge patriarchal mindsets and create equal opportunities in every field.",
        "tips": ["Cite real Indian women achievers", "Balance achievements with remaining challenges", "Be thoughtful and evidence-based"]
    },
    "startups": {
        "title": "Startups & Entrepreneurship in India",
        "prompt": "Discuss India's startup ecosystem, the entrepreneurial mindset, and what it takes to build a successful business.",
        "key_points": ["India's startup boom", "What makes a successful entrepreneur", "Startup challenges", "Startup vs corporate life", "Your entrepreneurial aspirations", "Role of failure in entrepreneurship"],
        "sample_vocabulary": ["India is the world's third largest startup ecosystem...", "The entrepreneurial mindset requires...", "The biggest challenge for startups is...", "Failure is part of..."],
        "model_answer": "India is now the world's third largest startup ecosystem, home to over 100 unicorns. This revolution is driven by a young tech-savvy population and a growing culture of problem-solving. What makes a successful entrepreneur is not just a great idea, but grit, willingness to pivot, and resilience in failure. I am inspired by founders like Nithin Kamath and Falguni Nayar who built category-defining companies with clarity of vision. I aspire to start something in the EdTech space within the next five years.",
        "tips": ["Use current Indian startup examples", "Discuss both opportunity and risk", "Show your own entrepreneurial thinking"]
    },
    "mental_health": {
        "title": "Mental Health Awareness",
        "prompt": "Discuss the importance of mental health, the stigma in India, and how we can better support each other.",
        "key_points": ["What mental health means", "Common issues among youth", "Stigma in Indian society", "Importance of seeking help", "Role of family and friends", "Self-care strategies"],
        "sample_vocabulary": ["Mental health is as important as...", "In India, stigma around...", "Seeking professional help is a sign of...", "Self-care practices include..."],
        "model_answer": "Mental health is as important as physical health — yet it remains deeply stigmatized in India. Many people suffering from anxiety or depression are told to simply think positively rather than seeking professional help. Mental health conditions are real, common, and treatable. The COVID-19 pandemic revealed how widespread these struggles were across all age groups. Seeking therapy is not weakness — it is courage. Simple self-care practices like exercise, journaling, quality sleep, and meaningful social connections can significantly improve mental well-being. We must normalize this conversation in every home and classroom.",
        "tips": ["Handle with sensitivity", "Avoid stigmatizing language", "Connect to post-COVID mental health reality"]
    },
    "artificial_intelligence": {
        "title": "Artificial Intelligence & the Future of Work",
        "prompt": "Discuss how AI is transforming industries and what it means for jobs, education, and society.",
        "key_points": ["What AI is in simple terms", "Industries AI is transforming", "Jobs at risk vs new jobs created", "AI in India", "Ethical concerns", "How to stay relevant"],
        "sample_vocabulary": ["AI enables machines to...", "AI is revolutionizing sectors like...", "While some jobs may be automated...", "In India, AI is being used for...", "To stay relevant, develop..."],
        "model_answer": "Artificial Intelligence enables machines to learn from data and make intelligent decisions. It is revolutionizing healthcare with early disease detection, transforming agriculture with precision farming, and reshaping finance with fraud detection. While repetitive jobs are at risk, AI creates new roles — AI trainers, ethicists, and prompt engineers. India is leveraging AI through Digital India and AI for Agriculture initiatives. The key to staying relevant is developing uniquely human skills: creativity, emotional intelligence, and ethical reasoning — skills machines cannot replicate.",
        "tips": ["Show specific AI applications in India", "Balance optimism with caution about risks", "Emphasize uniquely human irreplaceable skills"]
    },
    "work_life_balance": {
        "title": "Work-Life Balance in the Modern Age",
        "prompt": "Discuss the challenges of maintaining a healthy work-life balance and practical strategies to achieve it.",
        "key_points": ["What work-life balance means", "Challenges — remote work and hustle culture", "Impact of imbalance on health", "Strategies you use", "Corporate culture in India", "Employer responsibility"],
        "sample_vocabulary": ["Work-life balance means...", "Hustle culture glorifies...", "Research shows overwork leads to...", "I maintain balance by...", "Companies have a responsibility to..."],
        "model_answer": "Work-life balance means giving appropriate time to both professional responsibilities and personal well-being. In today's hyper-connected world, lines between work and life are increasingly blurred. Hustle culture glorifies overwork as a badge of honour, but research consistently shows chronic overwork leads to burnout, illness, and broken relationships. I maintain balance by setting clear work hours, exercising daily, and protecting weekends for personal time. Companies must also take responsibility — preventing after-hours emails, encouraging vacations, and measuring output rather than hours worked.",
        "tips": ["Reference hustle culture and burnout as real phenomena", "Share a practical personal strategy", "Discuss employer responsibility alongside personal discipline"]
    },
    "indian_culture": {
        "title": "Indian Culture, Heritage & Diversity",
        "prompt": "Discuss the richness of Indian culture, its diversity, and its significance in the modern world.",
        "key_points": ["Incredible cultural diversity", "Festivals and traditions", "Art, music, literature", "Core cultural values", "Tradition vs modernization balance", "India's global soft power"],
        "sample_vocabulary": ["India is a land of incredible...", "The diversity is reflected in...", "Traditional values like...", "India's soft power through yoga and Bollywood...", "Tradition and modernity are..."],
        "model_answer": "India's culture is arguably the world's most diverse — a tapestry of thousands of languages, hundreds of cuisines, dozens of classical art forms, and countless festivals. This diversity is our greatest strength. Values like respect for elders, hospitality, and family bonds have kept our social fabric strong across millennia. India's cultural soft power is growing globally — yoga is practised by 300 million people worldwide and Bollywood reaches audiences in 70 countries. Balancing cultural preservation with modernization is key — and I believe embracing progress need not mean abandoning our roots.",
        "tips": ["Celebrate specific art forms, festivals, and foods", "Mention India's soft power with pride", "Frame tradition and modernity as complementary"]
    },
    "peer_pressure": {
        "title": "Peer Pressure & Building Personal Identity",
        "prompt": "Discuss how peer pressure affects young people and how one can stay true to their own values.",
        "key_points": ["What peer pressure is", "Positive vs negative peer pressure", "Common areas it appears", "Impact on identity", "Strategies to handle it", "Importance of knowing your values"],
        "sample_vocabulary": ["Peer pressure is the influence...", "Positive peer pressure can...", "Negative peer pressure leads to...", "The key is knowing your values...", "Saying no confidently requires..."],
        "model_answer": "Peer pressure is the influence that people of similar age exert on each other's choices. Positive peer pressure — like being inspired by hardworking friends — is beneficial. But negative peer pressure to compromise one's values for social acceptance can cause lasting harm. The key to handling it is a strong sense of personal identity. When you know who you are and what you stand for, declining peer pressure becomes far easier. Surrounding yourself with people who respect your boundaries is equally essential for long-term well-being.",
        "tips": ["Distinguish positive from negative with examples", "Share a relatable personal experience", "Give specific strategies for saying no confidently"]
    },
    "reading_habits": {
        "title": "The Power of Reading Books",
        "prompt": "Discuss the importance of developing a reading habit and how books can transform a person's life.",
        "key_points": ["Benefits of regular reading", "Fiction vs non-fiction value", "Reading in the age of social media", "How you developed your habit", "Books that changed your perspective", "Reading vs passive scrolling"],
        "sample_vocabulary": ["Reading is the most...", "Books have the power to...", "I prefer reading... because...", "Even 20 minutes daily...", "A book that changed me was..."],
        "model_answer": "Reading is the single most powerful habit for growth, knowledge, and empathy. Books transport you into different worlds and expand your thinking in ways no other medium can fully match. I developed my reading habit at 15 when my teacher recommended Wings of Fire by APJ Abdul Kalam — that one book completely changed my outlook on perseverance. Since then I read across genres — self-help, fiction, and business. Even 20 minutes of focused reading daily — just 3% of waking hours — can mean 24 books a year. In a world dominated by short reels, deep sustained reading is a genuine superpower.",
        "tips": ["Share specific book recommendations to sound authentic", "Create a personal connection to your reading journey", "Contrast deep reading with passive social media scrolling"]
    },
}

# ══════════════════════════════════════════════════════════════════
#  INTERVIEW QUESTIONS & MODEL ANSWERS
# ══════════════════════════════════════════════════════════════════

INTERVIEW_QA = {
    "hr": [
        {
            "question": "Tell me about yourself.",
            "key_points": ["Educational background", "Work experience", "Skills", "Personality traits", "Career goals"],
            "model_answer": "I am [Name], a [degree] graduate from [College]. I have [X] years of experience in [field]. I am skilled in [skills]. I am a proactive, detail-oriented professional who loves [passion relevant to job]. My goal is to [career goal relevant to company].",
            "tips": ["Keep it 90 seconds", "Follow Present-Past-Future structure", "End with why you want this job", "Don't recite your resume"],
            "common_mistakes": ["Sharing too much personal info", "Being too long-winded", "Reading from memory robotically", "Not connecting to the role"]
        },
        {
            "question": "What are your strengths?",
            "key_points": ["Choose strengths relevant to the job", "Give specific examples", "Use the STAR method"],
            "model_answer": "My key strength is problem-solving. For example, in my previous role, when our campaign was underperforming, I analyzed the data, identified the issue, and restructured the strategy — resulting in a 35% improvement in conversions. I am also a strong communicator and a team player.",
            "tips": ["Mention 2-3 strengths only", "Always back up with real examples", "Choose strengths that fit the job description"],
            "common_mistakes": ["Saying 'I have no weaknesses'", "Listing too many strengths", "Being vague — 'I am hardworking'"]
        },
        {
            "question": "What are your weaknesses?",
            "key_points": ["Show self-awareness", "Mention a real weakness", "Show what you're doing to improve"],
            "model_answer": "I tend to be a perfectionist — I sometimes spend extra time on tasks to ensure everything is flawless. While this shows my dedication, it can affect time management. I am actively working on this by setting strict deadlines for myself and learning to distinguish between 'perfect' and 'good enough'.",
            "tips": ["Never say 'I have no weaknesses'", "Never say a weakness that is critical for the role", "Always mention how you're improving"],
            "common_mistakes": ["Fake weaknesses like 'I work too hard'", "Mentioning a weakness without improvement", "Sharing a weakness that disqualifies you"]
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "key_points": ["Be realistic and ambitious", "Show commitment to the company", "Connect to the role you're applying for"],
            "model_answer": "In five years, I see myself in a senior [role] position where I can lead a team and contribute significantly to the organization's goals. I am committed to continuously developing my skills in [specific area] and believe that [Company] provides the perfect platform for this growth.",
            "tips": ["Show ambition but stay realistic", "Show loyalty to the company", "Connect your growth to company growth", "Don't say 'your position'"],
            "common_mistakes": ["Saying 'I want your job'", "Being unrealistically ambitious", "Saying 'I don't know'", "Mentioning completely unrelated goals"]
        },
        {
            "question": "Why do you want to work here?",
            "key_points": ["Research the company beforehand", "Show genuine interest", "Connect your goals to company values"],
            "model_answer": "I have researched [Company] extensively and I am impressed by your commitment to [specific value/product/achievement]. Your work on [specific project/product] aligns perfectly with my interests and expertise in [area]. I believe that [Company]'s culture of [value] is where I can truly thrive and contribute meaningfully.",
            "tips": ["Always research the company", "Mention specific things about the company", "Connect company values to your own values"],
            "common_mistakes": ["Saying 'I need the money'", "Generic answers about 'reputed company'", "Not knowing anything about the company"]
        },
    ],
    "behavioral": [
        {
            "question": "Tell me about a time you faced a major challenge at work.",
            "method": "STAR Method: Situation → Task → Action → Result",
            "model_answer": "S: During my internship, our team had to deliver a major marketing report within 48 hours, but two team members fell sick. T: As the remaining member, I had to manage the entire workload. A: I prioritized tasks, stayed late, delegated minor tasks to available resources, and maintained constant communication with the manager. R: We delivered the report on time. The manager appreciated my dedication, and I was offered a full-time position.",
            "tips": ["Always use the STAR method", "Keep answer under 2 minutes", "Focus on YOUR actions, not the team's", "End with a positive result or lesson"]
        },
        {
            "question": "Describe a time you showed leadership.",
            "method": "STAR Method",
            "model_answer": "S: During our college fest, the event coordinator left suddenly a week before the event. T: I stepped up as the coordinator. A: I created a task checklist, divided responsibilities among team members, held daily progress meetings, and resolved last-minute venue issues. R: The fest was a huge success with 500+ attendees. I learned that leadership is about empowering others, not controlling them.",
            "tips": ["Leadership doesn't require a title", "Show initiative, not just management", "Include what you learned about leadership"]
        },
        {
            "question": "How do you handle stress and pressure?",
            "model_answer": "I believe stress is a part of any challenging role. I manage it through three strategies: First, I prioritize tasks using the Eisenhower Matrix — urgent vs important. Second, I break large tasks into smaller milestones, which gives me a sense of progress. Third, I maintain physical health through daily exercise which significantly improves my mental resilience. During high-pressure deadlines, I focus on what I can control and communicate proactively with my team about any challenges.",
            "tips": ["Show you have practical strategies", "Demonstrate self-awareness", "Give a real example if possible", "Don't say 'I don't get stressed'"]
        },
    ],
    "professional_communication": {
        "email_tips": [
            "Always start with a clear subject line",
            "Use formal salutation: Dear Mr./Ms. [Name] or Dear [Name]",
            "Keep the body concise and organized",
            "Use professional vocabulary — avoid slang",
            "Always end with: Regards / Best regards / Sincerely",
            "Proofread before sending — no grammar errors",
            "Reply within 24 hours professionally"
        ],
        "meeting_phrases": [
            "Let's begin the meeting — 'Shall we get started?'",
            "Agreeing — 'That's a great point.' / 'I completely agree.'",
            "Disagreeing politely — 'I see your point, however...' / 'With due respect, I think...'",
            "Asking for clarification — 'Could you please elaborate on that?' / 'What exactly do you mean by...?'",
            "Summarizing — 'To summarize the key points...' / 'So, what we've agreed is...'",
            "Ending the meeting — 'Thank you all for your contributions. The minutes will be shared shortly.'"
        ],
        "presentation_phrases": [
            "Opening — 'Good morning. I will be presenting on [topic] today.'",
            "Agenda — 'I will cover three main points: firstly... secondly... finally...'",
            "Transition — 'Moving on to the next point...' / 'Now, let's look at...'",
            "Referencing data — 'As you can see from this chart...' / 'According to our data...'",
            "Conclusion — 'To conclude, the key takeaways are...'",
            "Q&A — 'I would now like to open the floor for questions.'"
        ]
    }
}

# ══════════════════════════════════════════════════════════════════
#  DAILY CHALLENGES DATABASE
# ══════════════════════════════════════════════════════════════════

GRAMMAR_QUIZZES = [
    {
        "question": "Choose the correct sentence:",
        "options": ["A) She don't like coffee.", "B) She doesn't likes coffee.", "C) She doesn't like coffee.", "D) She not like coffee."],
        "answer": "C",
        "explanation": "With he/she/it in present simple, use 'doesn't' + base verb (like, not likes).",
        "rule": "Subject-Verb Agreement in Present Simple"
    },
    {
        "question": "Which is correct?",
        "options": ["A) I am going to market yesterday.", "B) I went to market yesterday.", "C) I go to market yesterday.", "D) I was go to market yesterday."],
        "answer": "B",
        "explanation": "Use Past Simple for completed actions with specific past time words like 'yesterday'.",
        "rule": "Past Simple Tense"
    },
    {
        "question": "Fill in the blank: She _____ in this company for 5 years.",
        "options": ["A) is working", "B) has been working", "C) works", "D) worked"],
        "answer": "B",
        "explanation": "Use Present Perfect Continuous (has/have been + V-ing) for actions that started in the past and continue to the present, especially with 'for'.",
        "rule": "Present Perfect Continuous with 'for'"
    },
    {
        "question": "Choose the correct article: He is _____ honest man.",
        "options": ["A) a", "B) an", "C) the", "D) no article"],
        "answer": "B",
        "explanation": "'Honest' begins with a vowel SOUND (the 'h' is silent), so we use 'an'.",
        "rule": "Articles — 'an' before vowel sounds"
    },
    {
        "question": "Which sentence is in passive voice?",
        "options": ["A) Ram wrote the letter.", "B) The letter was written by Ram.", "C) Ram is writing the letter.", "D) Ram will write the letter."],
        "answer": "B",
        "explanation": "Passive voice: Object + was/were + past participle (V3) + by + subject",
        "rule": "Passive Voice"
    },
    {
        "question": "If I _____ rich, I would travel the world.",
        "options": ["A) am", "B) was", "C) were", "D) will be"],
        "answer": "C",
        "explanation": "Second Conditional uses 'If + were' (not 'was' in formal English) for imaginary present situations.",
        "rule": "Second Conditional"
    },
    {
        "question": "Choose the correct preposition: The meeting is _____ Monday _____ 10 AM.",
        "options": ["A) in, at", "B) on, at", "C) at, in", "D) on, in"],
        "answer": "B",
        "explanation": "Use 'on' for days (on Monday) and 'at' for specific times (at 10 AM).",
        "rule": "Prepositions of Time"
    },
    {
        "question": "Which word correctly completes: 'I wish I _____ more time to study.'",
        "options": ["A) have", "B) had", "C) will have", "D) would have"],
        "answer": "B",
        "explanation": "'I wish' + past simple expresses a wish about the present. 'I wish I had' = I don't have, but I want to.",
        "rule": "Wish + Past Simple (Present Wish)"
    },
    {
        "question": "Identify the error: 'Everyone have their own opinion.'",
        "options": ["A) Everyone", "B) have", "C) their", "D) opinion"],
        "answer": "B",
        "explanation": "'Everyone' is singular and takes a singular verb 'has'. Correct: 'Everyone has their own opinion.'",
        "rule": "Indefinite Pronouns — Subject-Verb Agreement"
    },
    {
        "question": "Choose the correct modal: You _____ see a doctor — you look terrible!",
        "options": ["A) can", "B) may", "C) should", "D) would"],
        "answer": "C",
        "explanation": "'Should' expresses advice and recommendation. It's the appropriate modal for giving strong suggestions.",
        "rule": "Modal Verbs — Should for Advice"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) Neither of the boys have done homework.", "B) Neither of the boys has done homework.", "C) Neither of the boys are done homework.", "D) Neither of the boys did done homework."],
        "answer": "B",
        "explanation": "'Neither of' takes a singular verb. Correct: 'Neither of the boys has done homework.'",
        "rule": "Neither/Either — Subject-Verb Agreement"
    },
    {
        "question": "She asked me where _____ from.",
        "options": ["A) am I", "B) I am", "C) was I", "D) do I come"],
        "answer": "B",
        "explanation": "In indirect/reported questions, use statement word order (subject + verb), not question order.",
        "rule": "Reported Questions — Word Order"
    },
    {
        "question": "By the time they arrived, we _____ dinner.",
        "options": ["A) finished", "B) have finished", "C) had finished", "D) were finishing"],
        "answer": "C",
        "explanation": "Past Perfect (had + V3) is used for an action completed BEFORE another past action.",
        "rule": "Past Perfect Tense"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) The news are shocking.", "B) The news is shocking.", "C) The news were shocking.", "D) The news have shocked."],
        "answer": "B",
        "explanation": "'News' is an uncountable noun and always takes a singular verb 'is'.",
        "rule": "Uncountable Nouns — News, Information, Advice"
    },
    {
        "question": "He _____ in Jaipur since 2015.",
        "options": ["A) lives", "B) lived", "C) has lived", "D) is living"],
        "answer": "C",
        "explanation": "Present Perfect (has/have + V3) is used for actions that started in the past and continue to the present, with 'since'.",
        "rule": "Present Perfect with 'Since'"
    },
    {
        "question": "Choose the correct form: 'I _____ rather stay home than go out.'",
        "options": ["A) would", "B) will", "C) should", "D) could"],
        "answer": "A",
        "explanation": "'Would rather' expresses preference. Structure: would rather + base verb.",
        "rule": "Would Rather — Expressing Preference"
    },
    {
        "question": "The book _____ on the shelf belongs to Priya.",
        "options": ["A) laying", "B) lain", "C) lying", "D) laid"],
        "answer": "C",
        "explanation": "'Lying' (present participle of 'lie') means to be in a resting position. 'Laying' means to place something.",
        "rule": "Lie vs Lay — Confusing Verbs"
    },
    {
        "question": "Choose the correct indirect speech: He said, 'I will help you.'",
        "options": ["A) He said that he will help me.", "B) He said that he would help me.", "C) He said that he helps me.", "D) He said that he helped me."],
        "answer": "B",
        "explanation": "In reported speech, 'will' changes to 'would' when the reporting verb is in past tense.",
        "rule": "Reported Speech — Will → Would"
    },
    {
        "question": "_____ she works hard, she might fail the exam.",
        "options": ["A) Although", "B) Unless", "C) Because", "D) Since"],
        "answer": "B",
        "explanation": "'Unless' means 'if not'. 'Unless she works hard' = 'If she does not work hard'.",
        "rule": "Conjunctions — Unless"
    },
    {
        "question": "The jury _____ unable to reach a verdict.",
        "options": ["A) were", "B) was", "C) are", "D) have been"],
        "answer": "B",
        "explanation": "Collective nouns like 'jury', 'team', 'class' take singular verbs when acting as one unit.",
        "rule": "Collective Nouns — Singular Verb"
    },
    {
        "question": "He is one of those students who _____ always on time.",
        "options": ["A) is", "B) are", "C) was", "D) were"],
        "answer": "B",
        "explanation": "In 'one of those + noun who/that', the verb agrees with the plural noun, not 'one'. So 'are'.",
        "rule": "One of Those — Verb Agreement"
    },
    {
        "question": "Choose the correct form: 'I am used to _____ early.'",
        "options": ["A) wake", "B) woke", "C) waking", "D) have woken"],
        "answer": "C",
        "explanation": "'Be used to' means 'accustomed to' and is always followed by a gerund (V-ing).",
        "rule": "Be Used To + Gerund"
    },
    {
        "question": "Which sentence uses the gerund correctly?",
        "options": ["A) She enjoys to dance.", "B) She enjoys dance.", "C) She enjoys dancing.", "D) She enjoys danced."],
        "answer": "C",
        "explanation": "'Enjoy' is always followed by a gerund (V-ing), not infinitive. Correct: 'She enjoys dancing.'",
        "rule": "Verbs Followed by Gerund — Enjoy"
    },
    {
        "question": "The harder you work, _____.",
        "options": ["A) the more you succeed.", "B) more you succeed.", "C) you succeed more.", "D) the most you succeed."],
        "answer": "A",
        "explanation": "'The + comparative … the + comparative' structure is used to show two things increasing together.",
        "rule": "Double Comparatives"
    },
    {
        "question": "Identify the correctly punctuated sentence:",
        "options": ["A) Its a great day.", "B) It's a great day.", "C) Its' a great day.", "D) It'is a great day."],
        "answer": "B",
        "explanation": "'It's' is the contraction of 'it is'. 'Its' (no apostrophe) shows possession.",
        "rule": "It's vs Its"
    },
    {
        "question": "She _____ to the market when it started raining.",
        "options": ["A) walks", "B) walked", "C) was walking", "D) has walked"],
        "answer": "C",
        "explanation": "Past Continuous (was/were + V-ing) is used for an action in progress that was interrupted by another action.",
        "rule": "Past Continuous — Interrupted Action"
    },
    {
        "question": "Which is the correct comparative form?",
        "options": ["A) She is more smarter than him.", "B) She is smarter than him.", "C) She is smartest than him.", "D) She is most smart than him."],
        "answer": "B",
        "explanation": "One-syllable adjectives use '-er' for comparative. Never use 'more' with '-er'.",
        "rule": "Comparative Adjectives — One Syllable"
    },
    {
        "question": "Not only _____ late, but he also forgot his ID.",
        "options": ["A) he came", "B) did he come", "C) he did come", "D) came he"],
        "answer": "B",
        "explanation": "After 'Not only' at the start of a sentence, use inverted word order (auxiliary + subject + verb).",
        "rule": "Inverted Word Order — Not Only"
    },
    {
        "question": "Choose the correct use of 'fewer' vs 'less':",
        "options": ["A) There is less students today.", "B) There are fewer students today.", "C) There are less students today.", "D) There is fewer students today."],
        "answer": "B",
        "explanation": "'Fewer' is used with countable nouns (students, books), 'less' with uncountable nouns (water, time).",
        "rule": "Fewer vs Less"
    },
    {
        "question": "The manager, along with his team, _____ present at the meeting.",
        "options": ["A) were", "B) are", "C) was", "D) have been"],
        "answer": "C",
        "explanation": "When 'along with', 'as well as', 'together with' connect two subjects, the verb agrees with the FIRST subject (manager = singular → was).",
        "rule": "Along With — Subject-Verb Agreement"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) I have been to Shimla last year.", "B) I went to Shimla last year.", "C) I have went to Shimla last year.", "D) I was going to Shimla last year."],
        "answer": "B",
        "explanation": "Past Simple is used for completed actions with a specific past time ('last year'). Present Perfect cannot be used with specific past time markers.",
        "rule": "Past Simple vs Present Perfect"
    },
    {
        "question": "She speaks English as well as French, _____?",
        "options": ["A) doesn't she", "B) does she", "C) isn't she", "D) can't she"],
        "answer": "A",
        "explanation": "Question tags for positive sentences use a negative auxiliary. 'She speaks' → 'doesn't she'.",
        "rule": "Question Tags"
    },
    {
        "question": "Choose the correct sentence with 'had better':",
        "options": ["A) You had better to study hard.", "B) You had better studied hard.", "C) You had better study hard.", "D) You had better studying hard."],
        "answer": "C",
        "explanation": "'Had better' is followed by the base form of the verb (without 'to').",
        "rule": "Had Better + Base Verb"
    },
    {
        "question": "The _____ you eat junk food, the _____ your health will be.",
        "options": ["A) more, worse", "B) most, worst", "C) much, bad", "D) many, worse"],
        "answer": "A",
        "explanation": "Double comparative structure: 'The more … the worse'. Both use comparative forms.",
        "rule": "Double Comparative Structure"
    },
    {
        "question": "Which sentence has the correct use of 'since' and 'for'?",
        "options": ["A) I have known her since 10 years.", "B) I have known her for 2010.", "C) I have known her since 2010.", "D) I have known her since a long time."],
        "answer": "C",
        "explanation": "'Since' is used with a specific point in time (2010, Monday, January). 'For' is used with a duration (10 years, 3 months).",
        "rule": "Since vs For"
    },
    {
        "question": "Choose the correct passive voice: 'They built the bridge in 1990.'",
        "options": ["A) The bridge is built in 1990.", "B) The bridge was built in 1990.", "C) The bridge has been built in 1990.", "D) The bridge had built in 1990."],
        "answer": "B",
        "explanation": "Active: They built (Past Simple) → Passive: was built (was/were + V3).",
        "rule": "Passive Voice — Past Simple"
    },
    {
        "question": "He suggested that she _____ see a doctor.",
        "options": ["A) should", "B) would", "C) could", "D) might"],
        "answer": "A",
        "explanation": "After 'suggest', 'recommend', 'insist', the structure is: that + subject + should + base verb.",
        "rule": "Suggest/Recommend + That + Should"
    },
    {
        "question": "Choose the correct spelling:",
        "options": ["A) Accomodation", "B) Accommodation", "C) Acomodation", "D) Acommodation"],
        "answer": "B",
        "explanation": "The correct spelling is 'Accommodation' — with double 'c' and double 'm'.",
        "rule": "Common Spelling — Accommodation"
    },
    {
        "question": "Which sentence is grammatically correct?",
        "options": ["A) Despite of the rain, we went out.", "B) Despite the rain, we went out.", "C) Despite that it rained, we went out.", "D) Despite raining, we didn't went out."],
        "answer": "B",
        "explanation": "'Despite' is a preposition followed by a noun/gerund phrase. Do NOT use 'of' after despite.",
        "rule": "Despite (NOT Despite Of)"
    },
    {
        "question": "Choose the sentence with the correct use of apostrophe:",
        "options": ["A) The student's books are on the table. (one student)", "B) The students's books are on the table.", "C) The students book's are on the table.", "D) The students' book are on the table."],
        "answer": "A",
        "explanation": "For singular possessive, add 's. For plural possessive (students), add only ' after the s.",
        "rule": "Apostrophe — Singular vs Plural Possessive"
    },
    {
        "question": "Choose the correct form: 'I look forward to _____ from you.'",
        "options": ["A) hear", "B) heard", "C) hearing", "D) have heard"],
        "answer": "C",
        "explanation": "'Look forward to' is followed by a gerund (V-ing), NOT an infinitive.",
        "rule": "Look Forward To + Gerund"
    },
    {
        "question": "Which sentence is correct?",
        "options": ["A) He is more taller than his brother.", "B) He is the most tallest in the class.", "C) He is taller than his brother.", "D) He is tall more than his brother."],
        "answer": "C",
        "explanation": "Never double-compare — don't add 'more' before '-er' adjectives. Correct: 'taller than'.",
        "rule": "Comparative — No Double Comparison"
    },
    {
        "question": "Select the correct sentence:",
        "options": ["A) She as well as her friends are coming.", "B) She as well as her friends is coming.", "C) She as well as her friends were coming.", "D) She as well as her friends have come."],
        "answer": "B",
        "explanation": "'As well as' doesn't change the number of the main subject. Subject is 'She' (singular) → 'is'.",
        "rule": "As Well As — Verb Agreement"
    },
    {
        "question": "The thief ran away before the police _____.",
        "options": ["A) arrived", "B) had arrived", "C) arrives", "D) were arriving"],
        "answer": "A",
        "explanation": "'Before' already establishes the sequence of events, so simple past is used for both actions.",
        "rule": "Before + Simple Past (No Perfect Needed)"
    },
    {
        "question": "Choose the correct form of the verb: 'She made me _____ the whole report again.'",
        "options": ["A) to rewrite", "B) rewriting", "C) rewrite", "D) rewrote"],
        "answer": "C",
        "explanation": "Causative verbs like 'make', 'let', 'have' (causative) are followed by bare infinitive (without 'to').",
        "rule": "Causative Verbs — Make/Let + Bare Infinitive"
    },
    {
        "question": "Which sentence uses 'either...or' correctly?",
        "options": ["A) Either the manager or the employees has to stay.", "B) Either the manager or the employees have to stay.", "C) Either the manager or the employees is staying.", "D) Either the employees or the manager have to stay."],
        "answer": "B",
        "explanation": "With 'either...or / neither...nor', the verb agrees with the subject CLOSEST to it. 'employees' is plural → 'have'.",
        "rule": "Either...Or — Proximity Agreement"
    },
    {
        "question": "He _____ here for the last two hours waiting for you.",
        "options": ["A) is", "B) was", "C) has been", "D) had been"],
        "answer": "C",
        "explanation": "Present Perfect Continuous (has/have been + V-ing) is used for an action that started in the past and is still continuing.",
        "rule": "Present Perfect Continuous"
    },
    {
        "question": "Which sentence has incorrect use of articles?",
        "options": ["A) He is an MLA from UP.", "B) She is a NCC cadet.", "C) It is an NGO.", "D) He drives an SUV."],
        "answer": "B",
        "explanation": "Abbreviations are determined by their pronunciation. NCC starts with 'en' sound (vowel) → 'an NCC'. So 'a NCC' is wrong.",
        "rule": "Articles Before Abbreviations"
    },
    {
        "question": "She _____ her bag when someone snatched it.",
        "options": ["A) carries", "B) was carrying", "C) carried", "D) has carried"],
        "answer": "B",
        "explanation": "Past Continuous (was + V-ing) describes an action in progress at a specific past moment.",
        "rule": "Past Continuous — Action in Progress"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) The cattle is grazing in the field.", "B) The cattle are grazing in the field.", "C) The cattle was grazing in the field.", "D) A cattle are grazing in the field."],
        "answer": "B",
        "explanation": "'Cattle' is always plural — it has no singular form. Always use plural verb 'are'.",
        "rule": "Cattle — Always Plural"
    },
    {
        "question": "He denied _____ the money.",
        "options": ["A) to steal", "B) steal", "C) stealing", "D) stolen"],
        "answer": "C",
        "explanation": "'Deny' is followed by a gerund (V-ing). Common verbs + gerund: deny, admit, enjoy, avoid, consider.",
        "rule": "Deny + Gerund"
    },
    {
        "question": "Choose the sentence with correct use of 'so...that':",
        "options": ["A) She was so tired that she can't walk.", "B) She was so tired that she couldn't walk.", "C) She was so tired that she couldn't walked.", "D) She was so tired as she couldn't walk."],
        "answer": "B",
        "explanation": "'So...that' expresses result. When the main clause is past, the result clause also uses past modal ('couldn't').",
        "rule": "So...That — Result Clause"
    },
    {
        "question": "The chairman, together with his directors, _____ present at the press conference.",
        "options": ["A) were", "B) are", "C) was", "D) have been"],
        "answer": "C",
        "explanation": "'Together with' doesn't change the grammatical subject. Subject is 'chairman' (singular) → 'was'.",
        "rule": "Together With — Verb Agreement"
    },
    {
        "question": "Which sentence is grammatically incorrect?",
        "options": ["A) I am tired of waiting.", "B) She is fond of painting.", "C) He is interested in to learn guitar.", "D) They are good at solving problems."],
        "answer": "C",
        "explanation": "Prepositions (in, of, at, for) must be followed by a gerund (V-ing), never an infinitive. 'Interested in learning' is correct.",
        "rule": "Preposition + Gerund (Never Infinitive)"
    },
    {
        "question": "He spoke to me as if he _____ my boss.",
        "options": ["A) is", "B) was", "C) were", "D) will be"],
        "answer": "C",
        "explanation": "'As if' / 'as though' for imaginary situations uses 'were' (not 'was') in formal English — similar to second conditional.",
        "rule": "As If / As Though + Were"
    },
    {
        "question": "Choose the correct form: 'No sooner _____ than it started raining.'",
        "options": ["A) we went out", "B) did we go out", "C) we did go out", "D) had we gone out"],
        "answer": "D",
        "explanation": "'No sooner...than' uses Past Perfect (had + V3) and inverted word order: 'No sooner had we gone out than...'",
        "rule": "No Sooner...Than + Past Perfect"
    },
    {
        "question": "The police _____ looking for the suspect.",
        "options": ["A) is", "B) was", "C) are", "D) has been"],
        "answer": "C",
        "explanation": "In British English (and Indian English), 'police' is treated as a plural noun and takes a plural verb.",
        "rule": "Police — Plural in British English"
    },
    {
        "question": "She _____ her driving test three times before she finally passed.",
        "options": ["A) failed", "B) has failed", "C) had failed", "D) was failing"],
        "answer": "C",
        "explanation": "Past Perfect (had + V3) is used for actions completed before another past event ('before she finally passed').",
        "rule": "Past Perfect — Before Another Past Event"
    },
    {
        "question": "Choose the correctly punctuated sentence:",
        "options": ["A) However, he didn't listen.", "B) However he didn't listen.", "C) However; he didn't listen.", "D) However he, didn't listen."],
        "answer": "A",
        "explanation": "Conjunctive adverbs like 'however', 'therefore', 'moreover' are followed by a comma when used at the start of a clause.",
        "rule": "Conjunctive Adverbs + Comma"
    },
    {
        "question": "Which is the correct use of 'will' vs 'shall'?",
        "options": ["A) I will drown — no one shall save me!", "B) I shall drown — no one will save me!", "C) I shall drown — no one shall save me!", "D) I will drown — no one will save me!"],
        "answer": "B",
        "explanation": "Traditional rule: For simple future use 'shall' with I/We, 'will' with others. For emphasis/promise/threat, reverse: 'I shall' (threat) / 'they will' (promise/command). This sentence expresses a cry for help + command.",
        "rule": "Shall vs Will — Traditional Usage"
    },
    {
        "question": "By this time tomorrow, she _____ her finals.",
        "options": ["A) will finish", "B) will be finishing", "C) will have finished", "D) finishes"],
        "answer": "C",
        "explanation": "Future Perfect (will have + V3) is used for an action that will be completed before a specific future time.",
        "rule": "Future Perfect Tense"
    },
    {
        "question": "Choose the sentence with the correct use of 'much' and 'many':",
        "options": ["A) There are much people in the hall.", "B) There is many water in the bottle.", "C) There are many people in the hall.", "D) There is much peoples in the hall."],
        "answer": "C",
        "explanation": "'Many' is used with countable nouns (people, books). 'Much' is used with uncountable nouns (water, time).",
        "rule": "Much vs Many"
    },
    {
        "question": "If only I _____ harder for the exam!",
        "options": ["A) studied", "B) had studied", "C) would study", "D) have studied"],
        "answer": "B",
        "explanation": "'If only' with Past Perfect (had + V3) expresses regret about a past action that cannot be changed.",
        "rule": "If Only + Past Perfect — Regret"
    },
    {
        "question": "Which sentence uses a dangling modifier?",
        "options": ["A) Walking to school, I saw a rainbow.", "B) Walking to school, a rainbow was seen.", "C) While I was walking to school, I saw a rainbow.", "D) I saw a rainbow while walking to school."],
        "answer": "B",
        "explanation": "A dangling modifier occurs when the subject doing the action in the modifier doesn't match the sentence's main subject. 'A rainbow' cannot walk to school.",
        "rule": "Dangling Modifiers"
    },
    {
        "question": "Choose the correct sentence with 'used to':",
        "options": ["A) She use to live in Delhi.", "B) She used to live in Delhi.", "C) She is used to live in Delhi.", "D) She was used to live in Delhi."],
        "answer": "B",
        "explanation": "'Used to' (past habit/state) is always followed by base verb. 'She used to live' = she lived there in the past but no longer does.",
        "rule": "Used To + Base Verb (Past Habit)"
    },
    {
        "question": "The new policy _____ next Monday.",
        "options": ["A) implement", "B) is implemented", "C) will be implemented", "D) implements"],
        "answer": "C",
        "explanation": "Future Passive (will be + past participle) is used when the subject receives the action in the future.",
        "rule": "Future Passive Voice"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) He has a lot of informations.", "B) He has a lot of information.", "C) He has many informations.", "D) He has few information."],
        "answer": "B",
        "explanation": "'Information' is uncountable. No plural form. Use 'a lot of', 'some', or 'much' — never 'many' or add 's'.",
        "rule": "Information — Uncountable Noun"
    },
    {
        "question": "She asked her friend, '_____ you help me with this?' (polite)",
        "options": ["A) Can", "B) Will", "C) Could", "D) Shall"],
        "answer": "C",
        "explanation": "'Could' is more polite than 'can' for requests. 'Would' is also polite. 'Can' is informal.",
        "rule": "Modal Verbs — Polite Requests (Could)"
    },
    {
        "question": "Identify the sentence in Future Continuous tense:",
        "options": ["A) I will finish the project by Monday.", "B) I will be working on the project all weekend.", "C) I have been working on the project.", "D) I worked on the project last night."],
        "answer": "B",
        "explanation": "Future Continuous (will be + V-ing) describes an action that will be in progress at a future time.",
        "rule": "Future Continuous Tense"
    },
    {
        "question": "Choose the word that correctly fills the blank: 'She _____ in bed for three days with fever.'",
        "options": ["A) lay", "B) lied", "C) layed", "D) was laid"],
        "answer": "A",
        "explanation": "'Lay' is the past tense of 'lie' (to be in a resting position). Lie → lay → lain. Common error: confusing lay/lie.",
        "rule": "Lie vs Lay — Past Tense of Lie"
    },
    {
        "question": "Pick the sentence with the correct use of 'although':",
        "options": ["A) Although it was raining, but we went out.", "B) Although it was raining, we went out.", "C) Although it was raining, yet we went out.", "D) Although it was raining, still we went out."],
        "answer": "B",
        "explanation": "'Although' is already a conjunction. Never add 'but', 'yet', or 'still' with 'although' — it creates a double conjunction.",
        "rule": "Although — No Double Conjunction"
    },
    {
        "question": "Choose the sentence with correct subject-verb agreement:",
        "options": ["A) The list of items are on the table.", "B) The list of items is on the table.", "C) The list of items were on the table.", "D) The list of items have been on the table."],
        "answer": "B",
        "explanation": "The subject is 'list' (singular), not 'items'. Intervening phrases like 'of items' don't change the verb.",
        "rule": "Intervening Phrases — Subject Still Controls Verb"
    },
    {
        "question": "Which is correct? 'I suggest that he _____ the doctor immediately.'",
        "options": ["A) sees", "B) see", "C) should see", "D) Both B and C"],
        "answer": "D",
        "explanation": "After 'suggest/recommend/insist', you can use either: (1) that + subject + base verb (subjunctive) or (2) that + subject + should + base verb. Both are correct.",
        "rule": "Subjunctive vs Should — After Suggest"
    },
    {
        "question": "Choose the sentence with the correct use of 'which' vs 'that':",
        "options": ["A) The book which I borrowed is excellent.", "B) The book, that I borrowed, is excellent.", "C) The book, which I borrowed, is excellent.", "D) Both A and C are correct."],
        "answer": "D",
        "explanation": "'Which' with commas = non-restrictive (adds extra info). 'That' without commas = restrictive (defines which one). 'Which' without commas is also used in restrictive clauses in British English.",
        "rule": "Which vs That — Relative Clauses"
    },
    {
        "question": "She _____ to go abroad but her visa was rejected.",
        "options": ["A) wanted", "B) had wanted", "C) was wanting", "D) has wanted"],
        "answer": "A",
        "explanation": "Simple Past is used here because it's a straightforward past desire. 'Had wanted' would imply an earlier, unfulfilled desire — possible but 'wanted' is the natural choice.",
        "rule": "Past Simple for Past Desires"
    },
    {
        "question": "Choose the sentence with correct punctuation for a list:",
        "options": ["A) I need eggs, milk bread and butter.", "B) I need eggs, milk, bread, and butter.", "C) I need eggs milk, bread and butter.", "D) I need: eggs milk bread and butter."],
        "answer": "B",
        "explanation": "Items in a series are separated by commas. The Oxford comma (before 'and' in a list) is recommended for clarity.",
        "rule": "Commas in a Series — Oxford Comma"
    },
    {
        "question": "Which sentence correctly uses a semicolon?",
        "options": ["A) I love cricket; and football.", "B) I love cricket; football is also fun.", "C) I love; cricket and football.", "D) I love cricket and; football."],
        "answer": "B",
        "explanation": "A semicolon (;) joins two related independent clauses. Never use it before conjunctions like 'and', 'but', 'or'.",
        "rule": "Semicolon — Joining Independent Clauses"
    },
    {
        "question": "Choose the correct transformation: 'She is too tired to work.' = She is _____",
        "options": ["A) so tired that she can work.", "B) so tired that she cannot work.", "C) very tired that she cannot work.", "D) too tired so she works."],
        "answer": "B",
        "explanation": "'Too + adjective + to + verb' = 'so + adjective + that + subject + cannot + verb'. These are equivalent structures.",
        "rule": "Too...To = So...That...Cannot"
    },
    {
        "question": "I _____ rather you didn't tell anyone about this.",
        "options": ["A) will", "B) would", "C) should", "D) could"],
        "answer": "B",
        "explanation": "'Would rather + subject + past tense' expresses a preference about someone else's action. 'I would rather you didn't' = I prefer that you don't.",
        "rule": "Would Rather + Subject + Past Tense"
    },
    {
        "question": "Pick the sentence with correct use of hyphen:",
        "options": ["A) She is a well known singer.", "B) She is a well-known singer.", "C) She is well-known.", "D) Both B and C are correct."],
        "answer": "D",
        "explanation": "Compound adjectives before a noun are hyphenated (well-known singer). When used after the noun as a predicate, no hyphen (she is well known).",
        "rule": "Hyphen in Compound Adjectives"
    },
    {
        "question": "My mother is _____ woman I know.",
        "options": ["A) the most strongest", "B) the strongest", "C) most strongest", "D) more stronger"],
        "answer": "B",
        "explanation": "Superlative of 'strong' is 'strongest'. Never add 'most' before '-est' — that's double superlative, which is incorrect.",
        "rule": "Superlative — No Double Superlative"
    },
    {
        "question": "Choose the correct sentence with 'each other' vs 'one another':",
        "options": ["A) The two friends helped one another.", "B) The two friends helped each other.", "C) The twins help one another is technically more correct.", "D) Both A and B are equally correct in modern English."],
        "answer": "D",
        "explanation": "Traditionally, 'each other' was for two and 'one another' for three or more, but modern English accepts both for any number.",
        "rule": "Each Other vs One Another — Modern Usage"
    },
    {
        "question": "Which sentence uses 'could have' correctly?",
        "options": ["A) She could have been a great singer if she practiced.", "B) She could have been a great singer if she had practiced.", "C) She could been a great singer if she practiced.", "D) She could have been a great singer if she practices."],
        "answer": "B",
        "explanation": "Third Conditional: 'could have + past participle' in the result clause + 'if + had + past participle' in the if-clause.",
        "rule": "Third Conditional — Could Have"
    },
    {
        "question": "He works _____ to support his family.",
        "options": ["A) tirelessly", "B) tiredlessly", "C) tireless", "D) tired"],
        "answer": "A",
        "explanation": "Adverbs modify verbs (how he works). 'Tirelessly' is the correct adverb form of 'tireless'.",
        "rule": "Adverb Form — Modifying Verbs"
    },
    {
        "question": "Which sentence uses 'between' correctly?",
        "options": ["A) Distribute the sweets between all the students.", "B) Distribute the sweets among all the students.", "C) Distribute the sweets between the two students.", "D) Both B and C are correct."],
        "answer": "D",
        "explanation": "'Between' is for two (or more when items are distinct). 'Among' is for three or more as a group. B and C are both correct in their respective contexts.",
        "rule": "Between vs Among"
    },
    {
        "question": "Choose the sentence with correct use of 'whose':",
        "options": ["A) Whose going to the party?", "B) The student whose phone rang was asked to leave.", "C) I know whose responsible for this.", "D) Whose book is this belong to?"],
        "answer": "B",
        "explanation": "'Whose' = possessive form of 'who'. 'Who's' = contraction of 'who is/has'. In option B, 'whose phone' = the phone belonging to the student — correct use of possessive.",
        "rule": "Whose vs Who's"
    },
    {
        "question": "Choose the sentence in active voice:",
        "options": ["A) The cake was eaten by the children.", "B) The children ate the cake.", "C) The cake has been eaten.", "D) The cake is being eaten."],
        "answer": "B",
        "explanation": "Active voice: Subject + Verb + Object. 'The children' (subject) + 'ate' (verb) + 'the cake' (object).",
        "rule": "Active vs Passive Voice"
    },
    {
        "question": "He said that he _____ very tired.",
        "options": ["A) is", "B) was", "C) has been", "D) will be"],
        "answer": "B",
        "explanation": "In reported speech, when reporting verb is past (said), present 'is' changes to past 'was' (backshift).",
        "rule": "Reported Speech — Tense Backshift"
    },
    {
        "question": "Choose the correct form: 'The results will be announced _____.'",
        "options": ["A) soon", "B) lately", "C) late", "D) soonly"],
        "answer": "A",
        "explanation": "'Soon' means in the near future. 'Lately' = recently (used with present perfect). 'Soonly' is not a word.",
        "rule": "Adverbs — Soon vs Lately"
    },
    {
        "question": "_____ he works hard, he is unlikely to pass.",
        "options": ["A) Since", "B) Even though", "C) Unless", "D) If"],
        "answer": "B",
        "explanation": "'Even though' shows contrast (he works hard BUT still unlikely to pass). 'Unless' would mean 'if he doesn't work hard'.",
        "rule": "Even Though — Concession"
    },
    {
        "question": "The audience _____ requested to switch off their mobile phones.",
        "options": ["A) are", "B) was", "C) is", "D) were"],
        "answer": "D",
        "explanation": "'Audience' as a collective noun can take plural verb especially when referring to individual members. 'Were requested' is natural here.",
        "rule": "Audience — Collective Noun"
    },
    {
        "question": "She _____ hardly _____ her eyes when the alarm rang.",
        "options": ["A) has/closed", "B) had/closed", "C) has/closes", "D) was/closing"],
        "answer": "B",
        "explanation": "'Hardly...when' uses Past Perfect: 'She had hardly closed her eyes when the alarm rang.' = As soon as she closed her eyes.",
        "rule": "Hardly...When + Past Perfect"
    },
    {
        "question": "Choose the correct sentence:",
        "options": ["A) The more you practice, better you become.", "B) More you practice, the better you become.", "C) The more you practice, the better you become.", "D) More practice, better you become."],
        "answer": "C",
        "explanation": "Double comparative structure always needs 'the' before both comparative adjectives/adverbs.",
        "rule": "The + Comparative, The + Comparative"
    },
    {
        "question": "She was made _____ the entire assignment alone.",
        "options": ["A) do", "B) to do", "C) doing", "D) done"],
        "answer": "B",
        "explanation": "Passive causative with 'make': In passive voice, 'make' takes 'to' + infinitive. Active: They made her do → Passive: She was made to do.",
        "rule": "Passive Causative — Made To Do"
    },
    {
        "question": "Which sentence correctly uses 'despite' vs 'in spite of'?",
        "options": ["A) Despite of her efforts, she failed.", "B) In spite her efforts, she failed.", "C) Despite her efforts, she failed.", "D) In spite to her efforts, she failed."],
        "answer": "C",
        "explanation": "'Despite' and 'In spite of' are interchangeable, but 'despite' is NEVER followed by 'of'. Correct: 'despite her efforts' or 'in spite of her efforts'.",
        "rule": "Despite vs In Spite Of"
    },
    {
        "question": "Choose the correct sentence with 'few' vs 'a few':",
        "options": ["A) Few people came, so the event was a success.", "B) A few people came, so the event was cancelled.", "C) A few people came — not many, but some.", "D) Few people came — and that was enough."],
        "answer": "C",
        "explanation": "'A few' = some (positive meaning). 'Few' = hardly any (negative meaning). 'A few people came' suggests some (positive), not cancellation.",
        "rule": "Few vs A Few — Negative vs Positive"
    },
    {
        "question": "The data _____ suggesting a new trend in consumer behavior.",
        "options": ["A) is", "B) are", "C) Both A and B are correct", "D) was"],
        "answer": "C",
        "explanation": "'Data' is technically plural (datum = singular), so traditionally 'data are'. But in modern academic and everyday usage, 'data is' is widely accepted. Both are correct.",
        "rule": "Data — Singular or Plural (Both Accepted)"
    },
    {
        "question": "By next year, she _____ this company for a decade.",
        "options": ["A) will run", "B) will be running", "C) will have been running", "D) runs"],
        "answer": "C",
        "explanation": "Future Perfect Continuous (will have been + V-ing) describes an action that will have been in progress up to a specific future time.",
        "rule": "Future Perfect Continuous"
    },
    {
        "question": "Which sentence is correct?",
        "options": ["A) I am going to cinema tonight.", "B) I am going to the cinema tonight.", "C) I am going at cinema tonight.", "D) I go to cinema tonight."],
        "answer": "B",
        "explanation": "In British/Indian English, use 'the' before cinema, theatre, hospital (when referring to the place in general).",
        "rule": "Definite Article Before Venues"
    },
    {
        "question": "Choose the correct sentence with 'wish':",
        "options": ["A) I wish I am taller.", "B) I wish I was taller.", "C) I wish I were taller.", "D) Both B and C are acceptable."],
        "answer": "D",
        "explanation": "After 'wish', use past simple for present/future wishes. Formally 'were' is correct for all persons, but 'was' is widely accepted in modern usage. Both B and C are correct.",
        "rule": "Wish + Past Simple/Were"
    },
]

VOCABULARY_QUIZZES = [
    {
        "question": "What is the meaning of 'ELOQUENT'?",
        "options": ["A) Loud and rude", "B) Fluent and persuasive in speech", "C) Quiet and shy", "D) Confused and unclear"],
        "answer": "B",
        "hindi": "वाकपटु — अच्छा बोलने वाला",
        "explanation": "Eloquent describes someone who speaks or writes very effectively and persuasively.",
        "example": "She gave an eloquent speech that moved everyone to tears."
    },
    {
        "question": "Choose the SYNONYM of 'DILIGENT':",
        "options": ["A) Lazy", "B) Hardworking", "C) Careless", "D) Slow"],
        "answer": "B",
        "hindi": "Diligent = मेहनती | Synonym = Hardworking",
        "explanation": "'Diligent' means showing great care and effort. Its synonym is 'hardworking' or 'industrious'.",
        "example": "Diligent students always perform well in exams."
    },
    {
        "question": "What does 'PROCRASTINATE' mean?",
        "options": ["A) To work hard", "B) To delay doing something", "C) To finish early", "D) To make a plan"],
        "answer": "B",
        "hindi": "काम को टालना, आलस करना",
        "explanation": "Procrastinate means to keep delaying something that should be done.",
        "example": "Don't procrastinate — submit your assignment before the deadline!"
    },
    {
        "question": "Choose the ANTONYM of 'AMBIGUOUS':",
        "options": ["A) Vague", "B) Unclear", "C) Definite", "D) Confusing"],
        "answer": "C",
        "hindi": "Ambiguous = अस्पष्ट | Antonym = Definite (स्पष्ट)",
        "explanation": "Ambiguous means unclear or having two meanings. Its antonym is definite/clear.",
        "example": "His ambiguous answer was replaced with a definite yes."
    },
    {
        "question": "Fill in the blank: His _____ approach to problems impressed the management. (practical)",
        "options": ["A) Pragmatic", "B) Pessimistic", "C) Passive", "D) Petty"],
        "answer": "A",
        "hindi": "Pragmatic = व्यावहारिक, practical",
        "explanation": "Pragmatic means dealing with things practically rather than theoretically.",
        "example": "A pragmatic leader finds solutions quickly."
    },
    {
        "question": "What does 'RESILIENT' mean?",
        "options": ["A) Easily broken", "B) Recovering quickly from difficulties", "C) Very rigid", "D) Completely calm"],
        "answer": "B",
        "hindi": "मुश्किलों से जल्दी उबरने वाला",
        "explanation": "Resilient describes someone who can bounce back from setbacks and challenges.",
        "example": "She was resilient — she bounced back after every failure."
    },
    {
        "question": "Choose the word that means 'to work together':",
        "options": ["A) Collaborate", "B) Compete", "C) Contradict", "D) Confront"],
        "answer": "A",
        "hindi": "Collaborate = मिलकर काम करना",
        "explanation": "Collaborate means to work jointly with others towards a common goal.",
        "example": "The two departments collaborated to create the product."
    },
    {
        "question": "What is the meaning of 'INTEGRITY'?",
        "options": ["A) Intelligence level", "B) Physical strength", "C) Honesty and strong moral principles", "D) Integration of systems"],
        "answer": "C",
        "hindi": "ईमानदारी, नैतिकता",
        "explanation": "Integrity refers to the quality of being honest and having strong ethical principles.",
        "example": "A person of integrity never compromises on truth."
    },
    {
        "question": "Choose the SYNONYM of 'METICULOUS':",
        "options": ["A) Careless", "B) Sloppy", "C) Thorough and careful", "D) Quick and hasty"],
        "answer": "C",
        "hindi": "Meticulous = बारीकी से काम करने वाला",
        "explanation": "Meticulous means showing extreme care and precision in work.",
        "example": "Her meticulous research resulted in an excellent report."
    },
    {
        "question": "What does 'SUBSEQUENTLY' mean?",
        "options": ["A) Previously", "B) Simultaneously", "C) Immediately before", "D) Afterwards, following"],
        "answer": "D",
        "hindi": "बाद में, उसके पश्चात्",
        "explanation": "Subsequently means happening after something else; afterwards.",
        "example": "He was hired in June and subsequently promoted in December."
    },
    {
        "question": "What is the meaning of 'TENACIOUS'?",
        "options": ["A) Easily giving up", "B) Very talkative", "C) Holding firmly; not giving up", "D) Moving quickly"],
        "answer": "C",
        "hindi": "दृढ़ निश्चयी, हार न मानने वाला",
        "explanation": "Tenacious means holding on firmly and refusing to give up despite difficulties.",
        "example": "Her tenacious spirit helped her succeed despite all obstacles."
    },
    {
        "question": "Choose the ANTONYM of 'VERBOSE':",
        "options": ["A) Wordy", "B) Concise", "C) Loud", "D) Detailed"],
        "answer": "B",
        "hindi": "Verbose = बहुत ज़्यादा शब्द | Antonym = Concise (संक्षिप्त)",
        "explanation": "Verbose means using too many words. Its antonym is concise — brief and to the point.",
        "example": "Instead of a verbose report, write a concise summary."
    },
    {
        "question": "What does 'BENEVOLENT' mean?",
        "options": ["A) Cruel and harsh", "B) Kind and generous", "C) Greedy and selfish", "D) Angry and aggressive"],
        "answer": "B",
        "hindi": "दयालु, परोपकारी",
        "explanation": "Benevolent means well-meaning and kind, especially towards people in need.",
        "example": "The benevolent businessman donated millions to education."
    },
    {
        "question": "Choose the SYNONYM of 'OBSTINATE':",
        "options": ["A) Flexible", "B) Cooperative", "C) Stubborn", "D) Generous"],
        "answer": "C",
        "hindi": "Obstinate = ज़िद्दी | Synonym = Stubborn",
        "explanation": "Obstinate means stubbornly refusing to change one's opinion. Synonym: stubborn, headstrong.",
        "example": "Despite everyone's advice, he remained obstinate about his decision."
    },
    {
        "question": "What does 'EPHEMERAL' mean?",
        "options": ["A) Long-lasting", "B) Eternal", "C) Lasting for a very short time", "D) Very important"],
        "answer": "C",
        "hindi": "क्षणभंगुर, अल्पकालिक",
        "explanation": "Ephemeral describes something that lasts for only a short period of time.",
        "example": "Fame can be ephemeral if you don't continue to work hard."
    },
    {
        "question": "Fill in the blank: His _____ behaviour made everyone uncomfortable. (strange/weird)",
        "options": ["A) Eccentric", "B) Efficient", "C) Eloquent", "D) Eminent"],
        "answer": "A",
        "hindi": "Eccentric = विचित्र, अजीब ढंग का",
        "explanation": "Eccentric describes behaviour or ideas that are unusual and unconventional.",
        "example": "The eccentric scientist wore his lab coat everywhere, even to parties."
    },
    {
        "question": "What is the meaning of 'FRUGAL'?",
        "options": ["A) Wasteful and extravagant", "B) Very rich", "C) Careful with money; not wasteful", "D) Very generous"],
        "answer": "C",
        "hindi": "मितव्ययी, कम खर्च करने वाला",
        "explanation": "Frugal means being careful with money and avoiding unnecessary spending.",
        "example": "His frugal lifestyle helped him save enough to buy a house."
    },
    {
        "question": "Choose the ANTONYM of 'LOQUACIOUS':",
        "options": ["A) Talkative", "B) Noisy", "C) Quiet", "D) Cheerful"],
        "answer": "C",
        "hindi": "Loquacious = बातूनी | Antonym = Quiet (चुप)",
        "explanation": "Loquacious means very talkative. Its antonym is quiet or taciturn.",
        "example": "She's loquacious in meetings but quiet in social gatherings."
    },
    {
        "question": "What does 'AMBIVALENT' mean?",
        "options": ["A) Very certain and confident", "B) Having mixed feelings about something", "C) Extremely happy", "D) Completely opposed to something"],
        "answer": "B",
        "hindi": "दुविधा में, मिश्रित भावनाओं वाला",
        "explanation": "Ambivalent means having conflicting feelings or opinions about something.",
        "example": "She felt ambivalent about leaving her job — excited but also scared."
    },
    {
        "question": "Choose the word that means 'to make something worse':",
        "options": ["A) Ameliorate", "B) Alleviate", "C) Aggravate", "D) Appreciate"],
        "answer": "C",
        "hindi": "Aggravate = बिगाड़ना, और बुरा करना",
        "explanation": "Aggravate means to make a problem, injury, or bad situation worse.",
        "example": "Scratching the wound will only aggravate the condition."
    },
    {
        "question": "What is the meaning of 'CANDID'?",
        "options": ["A) Shy and reserved", "B) Honest and straightforward", "C) Clever and cunning", "D) Formal and polite"],
        "answer": "B",
        "hindi": "स्पष्टवादी, खुलकर बोलने वाला",
        "explanation": "Candid means truthful and straightforward, even if the truth is uncomfortable.",
        "example": "I appreciate your candid feedback on my presentation."
    },
    {
        "question": "Choose the SYNONYM of 'ALLEVIATE':",
        "options": ["A) Increase", "B) Worsen", "C) Reduce/relieve", "D) Ignore"],
        "answer": "C",
        "hindi": "Alleviate = कम करना, राहत देना",
        "explanation": "Alleviate means to make pain, suffering, or a problem less severe.",
        "example": "The medicine helped alleviate the patient's pain."
    },
    {
        "question": "What does 'PRAGMATIC' mean?",
        "options": ["A) Idealistic and dreamy", "B) Dealing with things practically", "C) Emotional and sensitive", "D) Strict and demanding"],
        "answer": "B",
        "hindi": "व्यावहारिक, जो काम करे वो करने वाला",
        "explanation": "Pragmatic means dealing with things sensibly and realistically, not theoretically.",
        "example": "A pragmatic approach to the problem solved it quickly."
    },
    {
        "question": "Choose the word meaning 'to officially stop a law or rule':",
        "options": ["A) Impose", "B) Enforce", "C) Repeal", "D) Implement"],
        "answer": "C",
        "hindi": "Repeal = कानून रद्द करना",
        "explanation": "Repeal means to officially cancel or revoke a law.",
        "example": "The government decided to repeal the outdated law."
    },
    {
        "question": "What is the meaning of 'MAGNANIMOUS'?",
        "options": ["A) Very large in size", "B) Generous and forgiving", "C) Extremely angry", "D) Full of pride"],
        "answer": "B",
        "hindi": "उदारमना, क्षमाशील",
        "explanation": "Magnanimous describes someone who is generous, kind, and forgiving, especially towards a rival or enemy.",
        "example": "The champion was magnanimous in victory, praising his opponent's effort."
    },
    {
        "question": "Choose the ANTONYM of 'PRUDENT':",
        "options": ["A) Wise", "B) Careful", "C) Reckless", "D) Practical"],
        "answer": "C",
        "hindi": "Prudent = सावधान, समझदार | Antonym = Reckless (लापरवाह)",
        "explanation": "Prudent means acting with care and thought. Its antonym is reckless — acting without thinking.",
        "example": "A prudent investor never puts all money in one place."
    },
    {
        "question": "What does 'EXACERBATE' mean?",
        "options": ["A) To improve a situation", "B) To make something worse", "C) To solve a problem completely", "D) To ignore a problem"],
        "answer": "B",
        "hindi": "बिगाड़ना, तीव्र करना",
        "explanation": "Exacerbate means to make a bad situation even worse.",
        "example": "Poor sleep habits can exacerbate anxiety and stress."
    },
    {
        "question": "Fill in the blank: She showed great _____ by donating half her income to charity. (generosity)",
        "options": ["A) Philanthropy", "B) Philosophy", "C) Phenomenon", "D) Phenomenal"],
        "answer": "A",
        "hindi": "Philanthropy = परोपकार, दान-धर्म",
        "explanation": "Philanthropy means the desire to promote the welfare of others, especially through charitable donations.",
        "example": "His philanthropy has funded hundreds of schools."
    },
    {
        "question": "What does 'REDUNDANT' mean in a workplace context?",
        "options": ["A) Being promoted to a higher role", "B) No longer needed or useful", "C) Working extra hours", "D) Taking a long holiday"],
        "answer": "B",
        "hindi": "अनावश्यक, जिसकी जरूरत न हो",
        "explanation": "Redundant in a workplace means the job is no longer required, often leading to layoffs.",
        "example": "Several employees were made redundant when the company automated its processes."
    },
    {
        "question": "Choose the SYNONYM of 'VORACIOUS':",
        "options": ["A) Full and satisfied", "B) Picky and selective", "C) Having a huge appetite; very eager", "D) Slow and hesitant"],
        "answer": "C",
        "hindi": "Voracious = अत्यधिक भूखा, लालची",
        "explanation": "Voracious means having a very large appetite for food or information.",
        "example": "She is a voracious reader who finishes a book every two days."
    },
    {
        "question": "What does 'METICULOUS' mean?",
        "options": ["A) Careless and sloppy", "B) Very quick", "C) Showing great attention to detail", "D) Extremely loud"],
        "answer": "C",
        "hindi": "बारीकी से काम करने वाला, सतर्क",
        "explanation": "Meticulous means showing extreme care and precision in one's work.",
        "example": "Her meticulous research resulted in an award-winning paper."
    },
    {
        "question": "Choose the ANTONYM of 'GREGARIOUS':",
        "options": ["A) Sociable", "B) Outgoing", "C) Introvert/Reserved", "D) Friendly"],
        "answer": "C",
        "hindi": "Gregarious = मिलनसार | Antonym = Reserved (अंतर्मुखी)",
        "explanation": "Gregarious means fond of being with others. Its antonym is reserved or introverted.",
        "example": "Unlike his gregarious sister, he preferred reading alone."
    },
    {
        "question": "What does 'INQUISITIVE' mean?",
        "options": ["A) Extremely boring", "B) Eager to learn or know things", "C) Very suspicious", "D) Completely honest"],
        "answer": "B",
        "hindi": "जिज्ञासु, जानने का शौकीन",
        "explanation": "Inquisitive means curious and eager to learn or know things.",
        "example": "Inquisitive children ask 'why' about everything."
    },
    {
        "question": "What is the meaning of 'LUCID'?",
        "options": ["A) Confusing and complicated", "B) Very dark", "C) Clear and easy to understand", "D) Extremely long"],
        "answer": "C",
        "hindi": "स्पष्ट, सुबोध",
        "explanation": "Lucid means expressed clearly and easy to understand.",
        "example": "The teacher gave a lucid explanation of the complex concept."
    },
    {
        "question": "Choose the SYNONYM of 'CONTEMPLATE':",
        "options": ["A) Ignore", "B) Reject", "C) Think deeply about", "D) Celebrate"],
        "answer": "C",
        "hindi": "Contemplate = गहराई से सोचना, विचार करना",
        "explanation": "Contemplate means to think carefully and deeply about something.",
        "example": "She contemplated her career options for weeks before deciding."
    },
    {
        "question": "What does 'INEVITABLE' mean?",
        "options": ["A) Preventable", "B) Surprising", "C) Certain to happen; unavoidable", "D) Temporary"],
        "answer": "C",
        "hindi": "अनिवार्य, अवश्यंभावी",
        "explanation": "Inevitable describes something that is certain to happen and cannot be prevented.",
        "example": "Change is inevitable — you must learn to adapt."
    },
    {
        "question": "What is the meaning of 'ANTAGONIST'?",
        "options": ["A) A close friend", "B) A person who opposes or is hostile to another", "C) A supporter or ally", "D) A neutral person"],
        "answer": "B",
        "hindi": "विरोधी, दुश्मन",
        "explanation": "An antagonist is someone who actively opposes another person or force.",
        "example": "In the story, the corrupt politician was the protagonist's main antagonist."
    },
    {
        "question": "Choose the ANTONYM of 'ARCHAIC':",
        "options": ["A) Ancient", "B) Old-fashioned", "C) Modern/Contemporary", "D) Historical"],
        "answer": "C",
        "hindi": "Archaic = पुराना, अप्रचलित | Antonym = Modern (आधुनिक)",
        "explanation": "Archaic means very old or old-fashioned. Its antonym is modern or contemporary.",
        "example": "The archaic laws were replaced with modern legislation."
    },
    {
        "question": "What does 'VERBOSE' mean?",
        "options": ["A) Silent and reserved", "B) Using too many words", "C) Very fast-speaking", "D) Speaking in a foreign language"],
        "answer": "B",
        "hindi": "बहुत ज़्यादा शब्द इस्तेमाल करने वाला",
        "explanation": "Verbose means using more words than needed; wordy.",
        "example": "His verbose reply could have been summarized in two sentences."
    },
    {
        "question": "What is the meaning of 'NOVICE'?",
        "options": ["A) An expert", "B) A beginner with little experience", "C) A retired professional", "D) A strict teacher"],
        "answer": "B",
        "hindi": "नौसिखिया, नया सीखने वाला",
        "explanation": "A novice is someone who is new to a subject or activity and has little experience.",
        "example": "As a novice programmer, she was still learning the basics."
    },
    {
        "question": "Choose the SYNONYM of 'FEROCIOUS':",
        "options": ["A) Gentle", "B) Timid", "C) Fierce and violent", "D) Playful"],
        "answer": "C",
        "hindi": "Ferocious = बेहद क्रूर, उग्र",
        "explanation": "Ferocious means savagely fierce, cruel, or violent.",
        "example": "The ferocious storm destroyed dozens of homes."
    },
    {
        "question": "What does 'PARAMOUNT' mean?",
        "options": ["A) Very small", "B) Of least importance", "C) Of supreme importance", "D) Completely irrelevant"],
        "answer": "C",
        "hindi": "सर्वोपरि, सबसे महत्वपूर्ण",
        "explanation": "Paramount means more important than everything else; supreme.",
        "example": "Patient safety is of paramount importance in healthcare."
    },
    {
        "question": "What is the meaning of 'IMPECCABLE'?",
        "options": ["A) Full of mistakes", "B) Unreliable", "C) In accordance with the highest standards; flawless", "D) Mediocre"],
        "answer": "C",
        "hindi": "बेदाग, निर्दोष",
        "explanation": "Impeccable means in accordance with the highest standards; without faults.",
        "example": "She has impeccable manners and always makes a great impression."
    },
    {
        "question": "Choose the ANTONYM of 'TRIVIAL':",
        "options": ["A) Unimportant", "B) Minor", "C) Significant/Crucial", "D) Small"],
        "answer": "C",
        "hindi": "Trivial = मामूली | Antonym = Significant (महत्वपूर्ण)",
        "explanation": "Trivial means of little importance. Its antonym is significant, crucial, or important.",
        "example": "Don't waste time on trivial matters — focus on what's significant."
    },
    {
        "question": "What does 'EMPATHY' mean?",
        "options": ["A) The ability to read minds", "B) Feeling of superiority", "C) Ability to understand and share the feelings of others", "D) A dislike of others' emotions"],
        "answer": "C",
        "hindi": "सहानुभूति, दूसरे की भावनाएं समझना",
        "explanation": "Empathy is the ability to understand and share the feelings of another person.",
        "example": "A good leader shows empathy towards their team's struggles."
    },
    {
        "question": "What is the meaning of 'PRODIGY'?",
        "options": ["A) A lazy person", "B) A person with exceptional talent at a young age", "C) A very old expert", "D) An average student"],
        "answer": "B",
        "hindi": "बाल प्रतिभा, असाधारण प्रतिभाशाली",
        "explanation": "A prodigy is a person, especially a child, who is exceptionally talented.",
        "example": "Mozart was a musical prodigy who composed at the age of five."
    },
    {
        "question": "Choose the SYNONYM of 'VINDICATE':",
        "options": ["A) Blame", "B) Punish", "C) Clear from blame or suspicion", "D) Ignore"],
        "answer": "C",
        "hindi": "Vindicate = निर्दोष साबित करना",
        "explanation": "Vindicate means to clear someone of blame or suspicion.",
        "example": "The new evidence completely vindicated the accused."
    },
    {
        "question": "What does 'PROLIFERATE' mean?",
        "options": ["A) To decrease rapidly", "B) To grow or multiply rapidly", "C) To remain the same", "D) To stop completely"],
        "answer": "B",
        "hindi": "तेज़ी से बढ़ना, फैलना",
        "explanation": "Proliferate means to increase rapidly in number; to multiply.",
        "example": "Misinformation has proliferated rapidly on social media."
    },
    {
        "question": "What is the meaning of 'ACUMEN'?",
        "options": ["A) Lack of knowledge", "B) Physical strength", "C) Keen insight and good judgment", "D) Emotional sensitivity"],
        "answer": "C",
        "hindi": "कुशाग्र बुद्धि, तीक्ष्ण समझ",
        "explanation": "Acumen means the ability to make good judgments and quick decisions.",
        "example": "Her business acumen helped turn the startup into a successful company."
    },
    {
        "question": "Choose the ANTONYM of 'TACITURN':",
        "options": ["A) Quiet", "B) Reserved", "C) Talkative", "D) Shy"],
        "answer": "C",
        "hindi": "Taciturn = चुप रहने वाला | Antonym = Talkative (बातूनी)",
        "explanation": "Taciturn means reserved and uncommunicative in speech. Antonym: talkative, loquacious.",
        "example": "He was taciturn in meetings but quite talkative with close friends."
    },
    {
        "question": "What does 'ENUMERATE' mean?",
        "options": ["A) To estimate roughly", "B) To mention one by one", "C) To delete completely", "D) To combine together"],
        "answer": "B",
        "hindi": "गिनाना, एक-एक करके बताना",
        "explanation": "Enumerate means to mention things one by one; to list.",
        "example": "The teacher asked students to enumerate the causes of World War I."
    },
    {
        "question": "What is the meaning of 'APPREHENSIVE'?",
        "options": ["A) Excited and confident", "B) Anxious or fearful about something", "C) Happy and relaxed", "D) Angry and frustrated"],
        "answer": "B",
        "hindi": "आशंकित, चिंतित, डरा हुआ",
        "explanation": "Apprehensive means worried or fearful that something unpleasant may happen.",
        "example": "She was apprehensive about her first day at the new job."
    },
    {
        "question": "Choose the SYNONYM of 'FASTIDIOUS':",
        "options": ["A) Careless", "B) Quick", "C) Very attentive to accuracy and detail", "D) Flexible"],
        "answer": "C",
        "hindi": "Fastidious = बहुत ज़्यादा ध्यान देने वाला, नखरेबाज़",
        "explanation": "Fastidious means very attentive to accuracy and detail, or difficult to please.",
        "example": "She was so fastidious that she rejected the report for a single typo."
    },
    {
        "question": "What does 'AMIABLE' mean?",
        "options": ["A) Hostile and aggressive", "B) Having a friendly and pleasant manner", "C) Extremely serious", "D) Competitive and ambitious"],
        "answer": "B",
        "hindi": "मिलनसार, सौम्य",
        "explanation": "Amiable means having a friendly, pleasant, and good-natured manner.",
        "example": "The amiable host made every guest feel welcome."
    },
    {
        "question": "What is the meaning of 'PREROGATIVE'?",
        "options": ["A) A responsibility or duty", "B) A right or privilege exclusive to a particular individual", "C) A type of punishment", "D) A formal request"],
        "answer": "B",
        "hindi": "विशेषाधिकार, अधिकार",
        "explanation": "Prerogative means a right or privilege belonging to a specific person or group.",
        "example": "It's the manager's prerogative to decide who gets promoted."
    },
    {
        "question": "Choose the ANTONYM of 'GARRULOUS':",
        "options": ["A) Talkative", "B) Verbose", "C) Silent/Reticent", "D) Friendly"],
        "answer": "C",
        "hindi": "Garrulous = बकवासी | Antonym = Reticent (चुप रहने वाला)",
        "explanation": "Garrulous means excessively talkative. Its antonym is reticent or silent.",
        "example": "His garrulous nature made it hard to have a short conversation with him."
    },
    {
        "question": "What does 'FORMIDABLE' mean?",
        "options": ["A) Weak and fragile", "B) Inspiring fear or respect through being very strong or powerful", "C) Friendly and approachable", "D) Ordinary and unremarkable"],
        "answer": "B",
        "hindi": "दुर्जेय, भयंकर रूप से शक्तिशाली",
        "explanation": "Formidable means inspiring awe or respect through great strength or power.",
        "example": "She was a formidable debater who won every argument."
    },
    {
        "question": "What is the meaning of 'DEFER'?",
        "options": ["A) To do immediately", "B) To postpone or put off to a later time", "C) To disagree strongly", "D) To complete in advance"],
        "answer": "B",
        "hindi": "टालना, स्थगित करना",
        "explanation": "Defer means to put off to a later time; to postpone.",
        "example": "The meeting was deferred to next week due to schedule conflicts."
    },
    {
        "question": "Choose the SYNONYM of 'EMULATE':",
        "options": ["A) Criticize", "B) Imitate or match, especially to surpass", "C) Avoid completely", "D) Destroy"],
        "answer": "B",
        "hindi": "Emulate = किसी की तरह बनने की कोशिश करना",
        "explanation": "Emulate means to match or surpass by imitating, especially someone admired.",
        "example": "Young players emulate Virat Kohli's training discipline."
    },
    {
        "question": "What does 'COGENT' mean?",
        "options": ["A) Weak and unconvincing", "B) Clear, logical, and convincing", "C) Emotional and passionate", "D) Long and complicated"],
        "answer": "B",
        "hindi": "ठोस, विश्वसनीय, तर्कसंगत",
        "explanation": "Cogent means clear, logical, and convincing — especially of an argument.",
        "example": "She made a cogent argument for changing the school policy."
    },
    {
        "question": "What is the meaning of 'ARDUOUS'?",
        "options": ["A) Simple and easy", "B) Involving or requiring strenuous effort; very difficult", "C) Automatic and effortless", "D) Quick and simple"],
        "answer": "B",
        "hindi": "कठिन, परिश्रमसाध्य",
        "explanation": "Arduous means requiring a great deal of effort and endurance; difficult.",
        "example": "Climbing Everest is an arduous journey that requires months of preparation."
    },
    {
        "question": "Choose the ANTONYM of 'PLACID':",
        "options": ["A) Calm", "B) Peaceful", "C) Turbulent/Agitated", "D) Serene"],
        "answer": "C",
        "hindi": "Placid = शांत | Antonym = Turbulent (उत्तेजित)",
        "explanation": "Placid means calm and peaceful. Its antonym is turbulent or agitated.",
        "example": "The placid lake suddenly turned turbulent in the storm."
    },
    {
        "question": "What does 'RETICENT' mean?",
        "options": ["A) Very talkative and open", "B) Not revealing one's thoughts; reserved", "C) Extremely confident", "D) Energetic and enthusiastic"],
        "answer": "B",
        "hindi": "चुप रहने वाला, अपनी बात न बताने वाला",
        "explanation": "Reticent means not willing to reveal one's thoughts or feelings; reserved.",
        "example": "She was reticent about her personal life even with close colleagues."
    },
    {
        "question": "What is the meaning of 'DEBACLE'?",
        "options": ["A) A great success", "B) A sudden and chaotic failure or disaster", "C) A slow process", "D) A planned event"],
        "answer": "B",
        "hindi": "करारी हार, पूर्ण विफलता",
        "explanation": "Debacle means a sudden, dramatic, and complete failure; a disaster.",
        "example": "The product launch was a complete debacle — nothing worked as planned."
    },
    {
        "question": "Choose the SYNONYM of 'BENIGN':",
        "options": ["A) Harmful", "B) Dangerous", "C) Gentle/Harmless", "D) Aggressive"],
        "answer": "C",
        "hindi": "Benign = हानिरहित, सौम्य",
        "explanation": "Benign means gentle, kind, and harmless. In medicine, it means not cancerous.",
        "example": "The doctor confirmed the tumour was benign — nothing to worry about."
    },
    {
        "question": "What does 'DISCREPANCY' mean?",
        "options": ["A) An agreement between two things", "B) A difference between two things that should be the same", "C) A very long delay", "D) A complete misunderstanding"],
        "answer": "B",
        "hindi": "विसंगति, अंतर",
        "explanation": "Discrepancy means a lack of compatibility or similarity between two things that should match.",
        "example": "There was a discrepancy between the invoice amount and what was paid."
    },
    {
        "question": "What is the meaning of 'ASTUTE'?",
        "options": ["A) Slow to understand", "B) Having an ability to accurately assess situations; clever", "C) Very emotional", "D) Physically strong"],
        "answer": "B",
        "hindi": "चतुर, बुद्धिमान, होशियार",
        "explanation": "Astute means having good judgment and a clever understanding of situations.",
        "example": "An astute investor knows when to buy and when to sell."
    },
    {
        "question": "Choose the ANTONYM of 'FRUGAL':",
        "options": ["A) Economical", "B) Thrifty", "C) Extravagant", "D) Careful"],
        "answer": "C",
        "hindi": "Frugal = कम खर्च करने वाला | Antonym = Extravagant (फ़िज़ूलखर्च)",
        "explanation": "Frugal means careful with money. Its antonym is extravagant — spending freely.",
        "example": "His frugal brother and extravagant sister could never agree on spending."
    },
    {
        "question": "What does 'CORROBORATE' mean?",
        "options": ["A) To disprove completely", "B) To confirm or support with evidence", "C) To confuse deliberately", "D) To delay an answer"],
        "answer": "B",
        "hindi": "पुष्टि करना, प्रमाण से सिद्ध करना",
        "explanation": "Corroborate means to confirm or give support to a statement or theory.",
        "example": "The witness's testimony corroborated the suspect's alibi."
    },
    {
        "question": "What is the meaning of 'NONCHALANT'?",
        "options": ["A) Extremely worried", "B) Excited and enthusiastic", "C) Appearing casually calm and relaxed", "D) Angry and aggressive"],
        "answer": "C",
        "hindi": "बेफ़िक्र, लापरवाह सा",
        "explanation": "Nonchalant means feeling or appearing casually calm and relaxed; not displaying anxiety.",
        "example": "He was surprisingly nonchalant about failing his driving test."
    },
    {
        "question": "Choose the SYNONYM of 'OBSOLETE':",
        "options": ["A) Modern", "B) Current", "C) Outdated/No longer in use", "D) Futuristic"],
        "answer": "C",
        "hindi": "Obsolete = पुराना, अप्रचलित",
        "explanation": "Obsolete means no longer produced, used, or needed; outdated.",
        "example": "Fax machines have become almost obsolete in the digital age."
    },
    {
        "question": "What does 'JEOPARDIZE' mean?",
        "options": ["A) To protect carefully", "B) To improve significantly", "C) To put into a dangerous situation; to risk", "D) To guarantee success"],
        "answer": "C",
        "hindi": "खतरे में डालना",
        "explanation": "Jeopardize means to put something in a dangerous situation or at risk.",
        "example": "One poor decision can jeopardize years of hard work."
    },
    {
        "question": "What is the meaning of 'LETHARGIC'?",
        "options": ["A) Full of energy", "B) Feeling a lack of energy; sluggish", "C) Very excited", "D) Extremely focused"],
        "answer": "B",
        "hindi": "सुस्त, आलसी, ऊर्जाहीन",
        "explanation": "Lethargic means affected by lethargy — sluggish and lacking energy.",
        "example": "I felt lethargic all day after the late-night flight."
    },
    {
        "question": "Choose the ANTONYM of 'DILIGENT':",
        "options": ["A) Hardworking", "B) Industrious", "C) Careless/Lazy", "D) Thorough"],
        "answer": "C",
        "hindi": "Diligent = मेहनती | Antonym = Lazy/Careless (आलसी)",
        "explanation": "Diligent means hardworking and careful. Its antonym is lazy, idle, or careless.",
        "example": "A diligent student always outperforms a lazy one in the long run."
    },
    {
        "question": "What does 'IMMINENT' mean?",
        "options": ["A) About to happen very soon", "B) Happening in the distant future", "C) Already happened", "D) Unlikely to happen"],
        "answer": "A",
        "hindi": "आसन्न, बस होने ही वाला",
        "explanation": "Imminent means about to happen very soon; impending.",
        "example": "With dark clouds gathering, a storm seemed imminent."
    },
    {
        "question": "What is the meaning of 'ELOQUENT'?",
        "options": ["A) Loud and aggressive", "B) Fluent and persuasive in expressing ideas", "C) Confusing and unclear", "D) Short and abrupt"],
        "answer": "B",
        "hindi": "वाकपटु, प्रभावशाली वक्ता",
        "explanation": "Eloquent means fluent, persuasive, and expressive in speech or writing.",
        "example": "His eloquent speech moved the entire audience to tears."
    },
    {
        "question": "Choose the SYNONYM of 'INSOLENT':",
        "options": ["A) Polite", "B) Respectful", "C) Rude and disrespectful", "D) Humble"],
        "answer": "C",
        "hindi": "Insolent = अहंकारी, बेअदब",
        "explanation": "Insolent means showing a rude and arrogant lack of respect.",
        "example": "The insolent student was asked to leave the classroom."
    },
    {
        "question": "What does 'BREVITY' mean?",
        "options": ["A) Great length and detail", "B) Concise and exact use of words", "C) Extreme loudness", "D) A type of courage"],
        "answer": "B",
        "hindi": "संक्षिप्तता",
        "explanation": "Brevity means concise and exact use of words in writing or speech.",
        "example": "'Brevity is the soul of wit' — Shakespeare."
    },
    {
        "question": "What is the meaning of 'ALTRUISTIC'?",
        "options": ["A) Selfish and greedy", "B) Showing concern for the well-being of others", "C) Focused only on personal gain", "D) Ambitious and competitive"],
        "answer": "B",
        "hindi": "परोपकारी, दूसरों की भलाई के लिए",
        "explanation": "Altruistic means unselfishly concerned with the well-being of others.",
        "example": "Her altruistic nature led her to donate her entire bonus to charity."
    },
    {
        "question": "Choose the ANTONYM of 'VERBOSE':",
        "options": ["A) Wordy", "B) Long-winded", "C) Concise", "D) Detailed"],
        "answer": "C",
        "hindi": "Verbose = बहुत शब्द इस्तेमाल करने वाला | Antonym = Concise",
        "explanation": "Verbose means using too many words. Its antonym is concise — brief and clear.",
        "example": "Edit the verbose draft down to a concise one-page summary."
    },
    {
        "question": "What does 'PRESUMPTUOUS' mean?",
        "options": ["A) Very humble", "B) Behaving overconfidently; taking too much for granted", "C) Very shy", "D) Extremely polite"],
        "answer": "B",
        "hindi": "ढीठ, अति आत्मविश्वासी",
        "explanation": "Presumptuous means (of a person or behavior) failing to observe proper limits; too forward.",
        "example": "It was presumptuous of him to assume he'd get the promotion."
    },
    {
        "question": "What is the meaning of 'JUXTAPOSE'?",
        "options": ["A) To remove completely", "B) To place things side by side for comparison", "C) To combine into one", "D) To analyze separately"],
        "answer": "B",
        "hindi": "दो चीज़ों को तुलना के लिए साथ रखना",
        "explanation": "Juxtapose means to place two things close together or side by side, especially for comparison.",
        "example": "The documentary juxtaposes luxury lifestyles with extreme poverty."
    },
    {
        "question": "Choose the SYNONYM of 'IMPEDE':",
        "options": ["A) Assist", "B) Accelerate", "C) Obstruct/Hinder", "D) Encourage"],
        "answer": "C",
        "hindi": "Impede = बाधा डालना, रोकना",
        "explanation": "Impede means to delay or prevent something by obstructing it.",
        "example": "The roadblock impeded the rescue operation."
    },
    {
        "question": "What does 'MEAGER' mean?",
        "options": ["A) Very large and sufficient", "B) Lacking in quality or quantity; very small", "C) Rich and abundant", "D) Strong and powerful"],
        "answer": "B",
        "hindi": "बहुत कम, अपर्याप्त",
        "explanation": "Meager means lacking in quality or quantity; very little.",
        "example": "She survived on a meager salary in her early career."
    },
    {
        "question": "What is the meaning of 'FORTUITOUS'?",
        "options": ["A) Planned carefully in advance", "B) Happening by chance, especially lucky", "C) Forced upon someone", "D) Extremely sad"],
        "answer": "B",
        "hindi": "संयोगवश, अकस्मात (अनुकूल)",
        "explanation": "Fortuitous means happening by accident or chance — often with a favorable outcome.",
        "example": "Their meeting at the airport was entirely fortuitous but changed their lives."
    },
    {
        "question": "Choose the ANTONYM of 'AUDACIOUS':",
        "options": ["A) Bold", "B) Daring", "C) Timid/Cowardly", "D) Brave"],
        "answer": "C",
        "hindi": "Audacious = साहसी, दुःसाहसी | Antonym = Timid (डरपोक)",
        "explanation": "Audacious means showing a willingness to take bold risks. Antonym: timid, cowardly.",
        "example": "His audacious plan surprised even the most experienced team members."
    },
    {
        "question": "What does 'INDULGE' mean?",
        "options": ["A) To strictly avoid something", "B) To allow oneself to enjoy something", "C) To punish severely", "D) To ignore completely"],
        "answer": "B",
        "hindi": "मनमाना करना, शौक पूरा करना",
        "explanation": "Indulge means to allow oneself or another to enjoy a particular pleasure.",
        "example": "She occasionally indulges in her love of chocolate."
    },
    {
        "question": "What is the meaning of 'PALPABLE'?",
        "options": ["A) Invisible and undetectable", "B) So intense it seems touchable; very obvious", "C) Extremely small", "D) Completely theoretical"],
        "answer": "B",
        "hindi": "स्पष्ट, महसूस करने योग्य",
        "explanation": "Palpable means so intense that it seems almost touchable; clearly noticeable.",
        "example": "The tension in the room was palpable before the results were announced."
    },
    {
        "question": "Choose the SYNONYM of 'STRINGENT':",
        "options": ["A) Flexible", "B) Lenient", "C) Strict and demanding", "D) Relaxed"],
        "answer": "C",
        "hindi": "Stringent = कठोर, सख्त",
        "explanation": "Stringent means very strict, precise, or demanding in requirements.",
        "example": "The bank has stringent rules for loan approvals."
    },
    {
        "question": "What does 'MITIGATE' mean?",
        "options": ["A) To make worse", "B) To make less severe or serious", "C) To completely eliminate", "D) To transfer responsibility"],
        "answer": "B",
        "hindi": "कम करना, घटाना",
        "explanation": "Mitigate means to lessen the gravity, seriousness, or painfulness of something.",
        "example": "The government took steps to mitigate the economic impact of the crisis."
    },
    {
        "question": "What is the meaning of 'EXEMPLARY'?",
        "options": ["A) Serving as a warning of something bad", "B) Mediocre and average", "C) Serving as a desirable model; outstanding", "D) Incomplete and partial"],
        "answer": "C",
        "hindi": "आदर्श, अनुकरणीय",
        "explanation": "Exemplary means serving as a model or example; outstandingly good.",
        "example": "She received an award for her exemplary service to the community."
    },
    {
        "question": "Choose the ANTONYM of 'AMBIGUOUS':",
        "options": ["A) Vague", "B) Unclear", "C) Unambiguous/Clear", "D) Confusing"],
        "answer": "C",
        "hindi": "Ambiguous = अस्पष्ट | Antonym = Unambiguous/Clear (स्पष्ट)",
        "explanation": "Ambiguous means unclear or having multiple meanings. Antonym: unambiguous, clear, definite.",
        "example": "Please give an unambiguous answer instead of an ambiguous one."
    },
    {
        "question": "What does 'SPURIOUS' mean?",
        "options": ["A) Genuine and authentic", "B) False or fake; not genuine", "C) Fast and sudden", "D) Slow and gradual"],
        "answer": "B",
        "hindi": "नकली, बनावटी, झूठा",
        "explanation": "Spurious means not genuine, authentic, or true; counterfeit.",
        "example": "The website was sharing spurious news to mislead the public."
    },
    {
        "question": "What is the meaning of 'VENERATE'?",
        "options": ["A) To insult or disrespect", "B) To regard with great respect and reverence", "C) To compete against", "D) To imitate closely"],
        "answer": "B",
        "hindi": "आदर करना, श्रद्धा रखना",
        "explanation": "Venerate means to regard someone with great respect and reverence.",
        "example": "In India, teachers are venerated as the second parents."
    },
    {
        "question": "What does 'DILEMMA' mean?",
        "options": ["A) A simple choice with one clear answer", "B) A situation requiring a choice between two equally difficult options", "C) A mathematical problem", "D) A type of argument"],
        "answer": "B",
        "hindi": "दुविधा, उलझन",
        "explanation": "A dilemma is a situation in which a choice must be made between two equally undesirable alternatives.",
        "example": "She faced a dilemma — quit her stable job or stay and be unhappy."
    },
    {
        "question": "Choose the SYNONYM of 'PIVOTAL':",
        "options": ["A) Unimportant", "B) Of central importance; crucial", "C) Rotating", "D) Small and insignificant"],
        "answer": "B",
        "hindi": "Pivotal = अत्यंत महत्वपूर्ण, निर्णायक",
        "explanation": "Pivotal means of crucial importance in relation to the development or success of something.",
        "example": "Winning that contract was a pivotal moment for the startup."
    },
    {
        "question": "What is the meaning of 'CANDOR'?",
        "options": ["A) Dishonesty and deception", "B) The quality of being open and honest", "C) Extreme shyness", "D) Aggressive behavior"],
        "answer": "B",
        "hindi": "स्पष्टवादिता, खुलापन",
        "explanation": "Candor means the quality of being open, honest, and straightforward.",
        "example": "I appreciate your candor — it's rare to find someone who speaks so honestly."
    },
    {
        "question": "Choose the ANTONYM of 'EUPHORIC':",
        "options": ["A) Ecstatic", "B) Joyful", "C) Depressed/Miserable", "D) Excited"],
        "answer": "C",
        "hindi": "Euphoric = अत्यंत खुश | Antonym = Depressed (दुखी)",
        "explanation": "Euphoric means intensely happy and excited. Its antonym is depressed or miserable.",
        "example": "She was euphoric after winning the award; the next day she felt depressed when criticized."
    },
    {
        "question": "What does 'TENACITY' mean?",
        "options": ["A) A tendency to give up", "B): Physical flexibility", "C) The quality of being very determined and persistent", "D) An ability to remain silent"],
        "answer": "C",
        "hindi": "दृढ़ता, दृढ़ निश्चय",
        "explanation": "Tenacity means the quality of holding firmly to something; great determination.",
        "example": "Her tenacity in the face of failure eventually led to her success."
    },
    {
        "question": "What is the meaning of 'ASTOUNDING'?",
        "options": ["A) Very ordinary", "B) Slightly surprising", "C) Shocking and amazingly impressive", "D) Completely boring"],
        "answer": "C",
        "hindi": "चौंका देने वाला, अद्भुत",
        "explanation": "Astounding means surprisingly impressive or notable; causing astonishment.",
        "example": "The gymnast's performance was astounding — the crowd gasped in amazement."
    },
]

# ══════════════════════════════════════════════════════════════════
#  TRANSLATION HINTS (Hindi → English patterns)
# ══════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "translations.json"
)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

EN_TO_HI = data.get("en_to_hi", {})
HI_TO_EN = data.get("hi_to_en", {})
from pathlib import Path


def clean_text(text):

    text = text.lower().strip()

    for ch in "!?.,;:-()[]{}\"'":
        text = text.replace(ch, "")

    text = " ".join(text.split())

    return text

TRANSLATION_PATTERNS = {
    "common_hindi_english": [
        {"hindi": "मैं खाना खाता हूँ।", "english": "I eat food.", "note": "Present Simple — daily habit"},
        {"hindi": "मैं खाना खा रहा हूँ।", "english": "I am eating food.", "note": "Present Continuous — happening now"},
        {"hindi": "मैंने खाना खाया।", "english": "I ate food.", "note": "Past Simple — completed action"},
        {"hindi": "मैं खाना खाऊँगा।", "english": "I will eat food.", "note": "Future Simple — future plan"},
        {"hindi": "क्या आप मेरी मदद करेंगे?", "english": "Will you help me? / Could you help me?", "note": "Polite request"},
        {"hindi": "मुझे नहीं पता।", "english": "I don't know.", "note": "Common phrase — NOT 'I don't know it'"},
        {"hindi": "यह मेरी गलती है।", "english": "This is my fault.", "note": "Taking responsibility"},
        {"hindi": "मैं 3 साल से यहाँ काम कर रहा हूँ।", "english": "I have been working here for 3 years.", "note": "Present Perfect Continuous with 'since/for'"},
        {"hindi": "मुझे उससे मिलना है।", "english": "I need to meet him/her.", "note": "Expressing necessity"},
        {"hindi": "काश मेरे पास ज़्यादा समय होता।", "english": "I wish I had more time.", "note": "Wish + Past Simple for present wish"},
    ],
    "common_mistakes_indians": [
        {"wrong": "I am having a car.", "correct": "I have a car.", "reason": "'Have' for possession doesn't use continuous"},
        {"wrong": "She is knowing the answer.", "correct": "She knows the answer.", "reason": "Mental state verbs don't use -ing"},
        {"wrong": "I am doing job since 3 years.", "correct": "I have been doing a job for 3 years.", "reason": "Present Perfect Continuous for ongoing past action"},
        {"wrong": "He told me that he will come.", "correct": "He told me that he would come.", "reason": "Reported speech — will → would"},
        {"wrong": "We discussed about the project.", "correct": "We discussed the project.", "reason": "'Discuss' doesn't take 'about'"},
        {"wrong": "I am agree with you.", "correct": "I agree with you.", "reason": "'Agree' is not used with 'am/is/are'"},
        {"wrong": "She gave exam yesterday.", "correct": "She took an exam yesterday.", "reason": "In English, you 'take' an exam, not 'give'"},
        {"wrong": "I will revert back to you.", "correct": "I will revert to you.", "reason": "'Revert' already means to go back — don't say 'back'"},
        {"wrong": "Please do the needful.", "correct": "Please do what is necessary. / Please take the required action.", "reason": "'Do the needful' is Indian English — not used globally"},
        {"wrong": "Kindly intimate me.", "correct": "Please inform me. / Please let me know.", "reason": "'Intimate' as a verb is rare in modern English"},
    ]
}

# ══════════════════════════════════════════════════════════════════
#  GENERAL CONVERSATION RESPONSES (Rule-based chatbot)
# ══════════════════════════════════════════════════════════════════

CHAT_RESPONSES = {
    "greeting": {
        "patterns": ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "namaste", "hii", "helo"],
        "responses": [
            "Hello! 👋 Welcome to AI English Coach! I'm Aria, your personal English teacher. How can I help you learn English today?\n\n💡 **Tip:** Instead of just saying 'Hi', try: *'Good morning! I hope you're doing well.'* — It sounds much more professional!\n\n📝 **Practice:** Now YOU greet me with a complete sentence! 🎯",
            "Hi there! 😊 Great to see you! I'm Aria, your AI English Teacher.\n\n🔍 **Grammar Note:** 'Hello' is formal, 'Hi' is informal, and 'Hey' is very casual. Use 'Hello' in professional settings!\n\n📝 **Try this:** Greet me with 'Good [morning/afternoon/evening], Aria! I am here to practice English today.' — Perfect sentence! 🌟",
        ]
    },
    "how_are_you": {
        "patterns": ["how are you", "how are u", "how r u", "kya haal hai", "kaisa hai", "how's it going", "how do you do"],
        "responses": [
            "I'm doing wonderfully, thank you for asking! 😊\n\n🔍 **Grammar Lesson:** When someone asks 'How are you?', don't just say 'Fine'. Here are better answers:\n\n📝 **Formal:** *'I'm doing very well, thank you. And yourself?'*\n📝 **Semi-formal:** *'I'm great, thanks for asking!'*\n📝 **Casual:** *'Pretty good! How about you?'*\n\n✅ Always respond AND ask back — it shows good social etiquette!\n\n❓ **Your turn:** How are YOU doing today? Write a complete answer!",
        ]
    },
    "what_is_tense": {
        "patterns": ["what is tense", "tense kya hai", "tense explain", "tell me about tenses", "tense in english", "types of tenses"],
        "responses": [
            "**📖 Tenses in English — Complete Guide**\n\nTenses tell us WHEN an action happens. There are **3 main tenses** with **4 forms each = 12 tenses total**!\n\n**1️⃣ PRESENT TENSES:**\n• Present Simple → I **eat** rice daily.\n• Present Continuous → I **am eating** rice now.\n• Present Perfect → I **have eaten** rice.\n• Present Perfect Continuous → I **have been eating** for an hour.\n\n**2️⃣ PAST TENSES:**\n• Past Simple → I **ate** rice yesterday.\n• Past Continuous → I **was eating** when she called.\n• Past Perfect → I **had eaten** before she came.\n• Past Perfect Continuous → I **had been eating** for an hour.\n\n**3️⃣ FUTURE TENSES:**\n• Future Simple → I **will eat** rice tomorrow.\n• Future Continuous → I **will be eating** at 8 PM.\n• Future Perfect → I **will have eaten** by 8 PM.\n• Future Perfect Continuous → I **will have been eating** for an hour.\n\n🏋️ **Practice:** Write one sentence in each of these tenses about YOUR daily routine!\n\n❓ Which tense confuses you the most? Ask me about it!"
        ]
    },
    "articles": {
        "patterns": ["articles", "a an the", "when to use a", "when to use an", "article rule", "use of the"],
        "responses": [
            "**📖 Articles in English — A, An, The**\n\nArticles are small words but VERY important! Here's a complete guide:\n\n**A (Indefinite Article):**\n• Use before consonant SOUNDS\n• A book, a car, a university (u = 'yoo' sound!)\n• Meaning: any one thing, not specific\n• Example: *I want a mango.* (any mango)\n\n**AN (Indefinite Article):**\n• Use before vowel SOUNDS (a, e, i, o, u)\n• An apple, an egg, an hour (h is silent!)\n• Example: *She is an engineer.*\n\n**THE (Definite Article):**\n• Use when both speaker and listener know what's meant\n• The sun, the moon, the President\n• Example: *Please close the door.* (specific door)\n\n**❌ NO ARTICLE when:**\n• Sports: I play cricket (NOT the cricket)\n• Languages: She speaks Hindi\n• Going to school/college/hospital (for purpose): He went to school.\n• General plural: Dogs are loyal. (all dogs in general)\n\n🔍 **Tricky ones:**\n• A university ✅ (not 'an university' — 'u' sounds like 'yoo')\n• An hour ✅ (not 'a hour' — 'h' is silent)\n\n🏋️ **Exercise:** Fill in A, AN, or THE:\n1. She is ___ engineer.\n2. I saw ___ movie last night. ___ movie was amazing.\n3. ___ Taj Mahal is in Agra.\n4. He plays ___ guitar.\n\n❓ Post your answers — I'll check them!"
        ]
    },
    "vocabulary_tip": {
        "patterns": ["vocabulary", "new words", "how to improve vocabulary", "word of the day", "learn new words", "english vocabulary", "vocabulary kaise improve kare"],
        "responses": [
            "**📚 How to Build a Powerful English Vocabulary**\n\n🎯 **The BEST Methods:**\n\n1️⃣ **Learn in Context** — Don't just memorize definitions. Read the word in sentences! *'She showed remarkable perseverance despite all obstacles.'*\n\n2️⃣ **Word Families** — Learn related words together:\n• persist → persistent → persistence → persistently\n• beauty → beautiful → beautify → beautifully\n\n3️⃣ **Root Words** — Learn Latin/Greek roots:\n• 'bene' = good → benefit, benevolent, beneficial\n• 'port' = carry → import, export, portable, transport\n\n4️⃣ **Spaced Repetition** — Review words after 1 day, 3 days, 1 week, 1 month.\n\n5️⃣ **Use the Word TODAY** — After learning a word, use it in 3 sentences.\n\n6️⃣ **Read Daily** — Newspapers (Times of India, The Hindu), novels, magazines.\n\n📖 **Today's Power Words:**\n• **Tenacious** (adj) = Never giving up (टिके रहने वाला)\n• **Eloquent** (adj) = Fluent and persuasive (वाकपटु)\n• **Astute** (adj) = Clever and quick to understand (चतुर)\n• **Diligent** (adj) = Hardworking (मेहनती)\n• **Resilient** (adj) = Bouncing back from problems (मजबूत)\n\n🏋️ **Exercise:** Use any 3 of these words in sentences about yourself!\n\n❓ Which topic's vocabulary would you like to focus on — Business, Academic, or Daily Conversation?"
        ]
    },
    "pronunciation": {
        "patterns": ["pronunciation", "how to pronounce", "pronunciation tips", "how to speak", "accent", "speak clearly", "pronunciation improve"],
        "responses": [
            "**🎤 Pronunciation Guide for Indian English Speakers**\n\n🔴 **Most Common Indian Pronunciation Mistakes:**\n\n**1. TH Sound** (Most difficult for Indians!)\n• Indians often say: *'dis', 'dat', 'dree'*\n• Correct: Put tongue between teeth\n• Practice: **th**ink, **th**is, **th**ere, **th**ree, **th**ank\n\n**2. W vs V** (Very common mistake!)\n• W → Round lips (like blowing): **w**ater, **w**ine, **w**ork\n• V → Upper teeth touch lip: **v**ery, **v**alue, **v**ideo\n• Practice pairs: vine/wine, vest/west, veal/wheel\n\n**3. Silent Letters** (Indians pronounce every letter!)\n• knife = NIFE (k silent)\n• know = NO (k silent)\n• walk = WAWK (l silent)\n• honest = ONEST (h silent)\n• would = WUD (l silent)\n\n**4. Word Stress Rules:**\n• 2-syllable NOUNS: stress FIRST syllable → **PRE**sent, **RE**cord\n• 2-syllable VERBS: stress SECOND syllable → pre**SENT**, re**CORD**\n• Words ending in -tion → stress syllable BEFORE → infor**MA**tion, edu**CA**tion\n\n**5. Ending Sounds:**\n• Don't add 'a' at the end → 'book' not 'booka'\n• Fully pronounce: sto**P**, wal**K**, clo**CK**\n\n🏋️ **Daily Tongue Twister:**\n*'The thirty-three thieves thought that they thrilled the throne throughout Thursday.'*\n\nSay it slowly 3 times, then faster!\n\n❓ Which sound do YOU find most difficult?"
        ]
    },
    "interview": {
        "patterns": ["interview", "job interview", "interview tips", "how to crack interview", "interview preparation", "interview english"],
        "responses": [
            "**💼 Master English for Job Interviews**\n\n🎯 **Essential Interview Vocabulary:**\n• Instead of 'good' → **excellent, outstanding, remarkable**\n• Instead of 'did' → **accomplished, achieved, delivered**\n• Instead of 'helped' → **contributed, collaborated, supported**\n• Instead of 'made' → **developed, created, implemented**\n• Instead of 'know' → **proficient in, well-versed in, skilled at**\n\n📋 **Power Phrases to Use:**\n• 'I take initiative in challenging situations.'\n• 'I am a result-oriented professional.'\n• 'I thrive in collaborative environments.'\n• 'I believe in continuous learning and growth.'\n• 'My key strength is problem-solving under pressure.'\n\n✅ **Self-Introduction Template:**\n*'Good morning. My name is [Name]. I have completed my [Degree] from [College]. I have [X] years of experience in [field] where I have successfully [achievement]. I am passionate about [relevant passion] and I believe I can bring significant value to [Company] through my skills in [skills].'*\n\n🚫 **Common Mistakes in Interviews:**\n• Saying 'I don't know nothing about this company'\n• Using Indian English phrases: 'do the needful', 'revert back'\n• Starting every sentence with 'basically'\n• Speaking too fast due to nervousness\n\n🗣️ **Body Language Tips:**\n• Maintain eye contact — shows confidence\n• Firm handshake — shows assertiveness\n• Sit upright — shows professionalism\n• Smile genuinely — shows positivity\n\n🏋️ **Practice NOW:** Answer this question in 2 minutes:\n*'Tell me about yourself.'*\n\n❓ Which interview question scares you the most?"
        ]
    },
    "grammar_mistake": {
        "patterns": ["correct my grammar", "check my english", "grammar mistake", "is this correct", "is this right", "grammar check"],
        "responses": [
            "I'd be happy to check your grammar! 😊\n\nPlease **type or paste your English text** below, and I will:\n\n1. ✅ **Correct all grammar mistakes**\n2. 🔍 **Explain WHY each correction was made**\n3. 📖 **Teach the grammar rule**\n4. 📝 **Give you 3 example sentences**\n5. 🏋️ **Give you a practice exercise**\n\nGo ahead — type your sentence or paragraph! Don't be shy — making mistakes is HOW we learn! 💪\n\n❓ Alternatively, here are some **common Indian English mistakes** I often see:\n\n1. ❌ *'I am doing job since 3 years.'* → ✅ *'I have been doing a job for 3 years.'*\n2. ❌ *'She don't know.'* → ✅ *'She doesn't know.'*\n3. ❌ *'We discussed about the project.'* → ✅ *'We discussed the project.'*\n4. ❌ *'Please do the needful.'* → ✅ *'Please take the necessary action.'*\n5. ❌ *'I will revert back.'* → ✅ *'I will revert to you.'*\n\nWhich of these mistakes do YOU make? 😊"
        ]
    },
    "thank_you": {
        "patterns": ["thank you", "thanks", "thank u", "thanks a lot", "bahut shukriya", "dhanyawad"],
        "responses": [
            "You're very welcome! 😊 I'm so glad I could help!\n\n🔍 **Quick Lesson:** There are many ways to say 'Thank you' in English:\n\n• **Formal:** 'Thank you very much. I really appreciate it.'\n• **Semi-formal:** 'Thanks a lot! That was really helpful.'\n• **Casual:** 'Thanks!' / 'Cheers!' (British)\n• **Emphasizing:** 'I cannot thank you enough for this!'\n• **Professional:** 'I truly appreciate your assistance.'\n\n💡 **Important:** Always respond to 'Thank you' properly:\n• 'You're welcome!' ✅\n• 'My pleasure!' ✅ (more gracious)\n• 'Not at all!' ✅ (British style)\n• 'Don't mention it!' ✅\n• 'No problem!' ✅ (casual)\n• 'Thank you!' ❌ (Don't say 'Thank you' back — it's awkward!)\n\n🏋️ **Practice:** Write a thank-you email to a professor who helped you. Use formal language!\n\n❓ What would you like to learn next? 🎓"
        ]
    },
    "default": {
        "responses": [
            "That's a great topic to discuss! Let me teach you about it as your English Coach. 😊\n\n🔍 **Language Insight:** Whatever you ask me, I will:\n1. Answer your question\n2. Correct any English mistakes in your message\n3. Teach you relevant vocabulary\n4. Give you example sentences\n5. Give you a practice exercise\n\nSo keep asking and keep learning! 🎓\n\n📝 **Quick Grammar Check:** Make sure you're writing complete sentences with capital letters and proper punctuation!\n\n❓ Could you tell me more specifically what you'd like to learn — Grammar, Vocabulary, Speaking, or something else?"
        ]
    }
}

# ══════════════════════════════════════════════════════════════════
#  ENGINE FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def get_chat_response(user_message: str) -> str:
    """Match user message to best response from dataset."""
    msg = user_message.lower().strip()

    # Check each category
    for category, data in CHAT_RESPONSES.items():
        if category == "default":
            continue
        patterns = data.get("patterns", [])
        for pattern in patterns:
            if pattern in msg:
                return random.choice(data["responses"])

    # Grammar correction — detect if user wrote sentences
    if len(msg.split()) > 4 and any(w in msg for w in ["i am", "i have", "she is", "he is", "they are", "we are", "i was", "i went", "i did"]):
        return grammar_check_response(user_message)

    # Question about a specific word
    if any(msg.startswith(p) for p in ["what is", "what does", "meaning of", "define ", "explain "]):
        word = msg.replace("what is", "").replace("what does", "").replace("meaning of", "").replace("define", "").replace("explain", "").strip().split()[0] if msg.split() else ""
        if word in VOCABULARY:
            return format_vocabulary_response(word)

    return random.choice(CHAT_RESPONSES["default"]["responses"])


def grammar_check_response(text: str) -> str:
    """Attempt basic grammar checking from patterns."""
    corrections = []
    result = text

    # Check all known mistakes
    all_mistakes = []
    for section in GRAMMAR_RULES.values():
        if isinstance(section, dict):
            for subsection in section.values():
                if isinstance(subsection, dict) and "common_mistakes" in subsection:
                    all_mistakes.extend(subsection["common_mistakes"])

    # Add Indian mistakes
    for m in TRANSLATION_PATTERNS["common_mistakes_indians"]:
        all_mistakes.append({"wrong": m["wrong"], "correct": m["correct"], "rule": m["reason"]})

    found = []
    text_lower = text.lower()
    for m in all_mistakes:
        if m["wrong"].lower() in text_lower:
            found.append(m)
            result = re.sub(re.escape(m["wrong"]), m["correct"], result, flags=re.IGNORECASE)

    if found:
        response = f"🔍 **Grammar Analysis of Your Text:**\n\n"
        response += f"✅ **Corrected Version:**\n*{result}*\n\n"
        response += f"📋 **Mistakes Found & Corrections:**\n"
        for i, m in enumerate(found, 1):
            response += f"\n{i}. ❌ '{m['wrong']}' → ✅ '{m['correct']}'\n   📖 Rule: {m['rule']}\n"
        response += f"\n💡 **Keep practicing!** Writing regularly is the best way to improve grammar.\n"
        response += f"\n🏋️ **Exercise:** Now write a new paragraph on the same topic using the corrected forms!\n"
        response += f"\n❓ Would you like to learn more about any of these grammar rules?"
        return response
    else:
        return f"✅ **Great job!** Your text looks grammatically correct! 🎉\n\nLet me add some vocabulary suggestions to make it even stronger:\n\n💡 **Power Words you could use:**\n• Instead of common words, try: *remarkable, accomplish, demonstrate, utilize, implement*\n\n🗣️ **Pronunciation tip:** Practice saying your text aloud — fluency comes from speaking, not just writing!\n\n🏋️ **Next step:** Write another paragraph on the same topic but try to use more advanced vocabulary!\n\n❓ What else would you like to practice?"


def format_vocabulary_response(word: str) -> str:
    """Format a vocabulary entry as a teaching response."""
    v = VOCABULARY.get(word)
    if not v:
        return f"I don't have '{word}' in my current vocabulary list, but here's what I can tell you:\n\n💡 Try exploring words like: {', '.join(list(VOCABULARY.keys())[:8])}\n\n📚 Use the **Vocabulary Coach** section for detailed word lookups!\n\n❓ Which of these words would you like to learn?"

    response = f"📚 **Word: {word.upper()}**\n\n"
    response += f"📖 **Meaning:** {v['meaning']}\n\n"
    response += f"🇮🇳 **Hindi:** {v['hindi']}\n\n"
    response += f"🗣️ **Pronunciation:** {v['pronunciation']} | IPA: {v['ipa']}\n\n"
    response += f"🔀 **Synonyms:** {', '.join(v['synonyms'])}\n\n"
    response += f"↔️ **Antonyms:** {', '.join(v['antonyms'])}\n\n"
    response += f"📝 **Examples:**\n"
    for ex in v['examples']:
        response += f"• {ex}\n"
    response += f"\n💼 **Daily Usage Tip:** {v['daily_usage']}\n"
    response += f"\n🏋️ **Exercise:** Write 2 original sentences using '{word}' in different contexts!\n"
    response += f"\n❓ Would you like to learn more words from the same category?"
    return response


def get_vocabulary_info(word: str) -> str:
    """Get vocabulary info for a word."""
    word = word.lower().strip()
    if word in VOCABULARY:
        return format_vocabulary_response(word)
    # Find partial match
    for key in VOCABULARY:
        if word in key or key in word:
            return format_vocabulary_response(key)
    # Return generic advice
    return f"📚 **Word: {word.upper()}**\n\nI don't have a specific entry for '{word}' in my offline database, but here's my teaching advice:\n\n🔍 **How to learn any new word:**\n1. Look it up in a dictionary (Oxford/Merriam-Webster)\n2. Note its pronunciation using IPA symbols\n3. Find 3 example sentences\n4. Learn its synonyms and antonyms\n5. Use it in your own sentence TODAY\n\n📖 **Words I CAN teach you right now:**\n{chr(10).join(['• ' + w + ' — ' + VOCABULARY[w]['meaning'][:50] + '...' for w in list(VOCABULARY.keys())[:8]])}\n\n❓ Would you like to learn any of these words?"


def get_grammar_feedback(text: str, user_id: str = None) -> str:
    """
    Upgraded grammar feedback using grammar_engine.
    Falls back to legacy grammar_check_response if engine fails.
    """
    try:
        from .grammar_engine import check as engine_check
        result = engine_check(text, user_id=str(user_id) if user_id else None)
        if "error" in result:
            return grammar_check_response(text)
        return _format_engine_result(result)
    except Exception:
        return grammar_check_response(text)


def _format_engine_result(result: dict) -> str:
    """Format grammar_engine result dict into rich markdown string for the frontend."""
    lines = []

    # ── Header
    score = result.get("score", 100)
    grade = result.get("grade", "")
    errors = result.get("errors", [])
    n = len(errors)

    lines.append(f"## 📊 Grammar Analysis Results\n")
    lines.append(f"**Score:** {score}/100  |  **Grade:** {grade}\n")

    # ── Corrected version
    if result.get("corrected"):
        lines.append(f"### ✅ Corrected Version\n*{result['corrected']}*\n")
    else:
        lines.append(f"### ✅ Original Text\n*{result['original']}*\n")
        lines.append("**Your text has no major errors! 🎉**\n")

    if not errors:
        lines.append("---")
        lines.append("### 💡 Vocabulary Enhancement")
        lines.append("Your grammar is solid! To sound even more advanced, try these power words:")
        lines.append("• *remarkable* instead of *good*")
        lines.append("• *demonstrate* instead of *show*")
        lines.append("• *endeavour* instead of *try*")
        lines.append("• *accomplish* instead of *do*\n")
        lines.append("🏋️ **Next Challenge:** Write a 3-sentence paragraph using 2 of these words!")
        return "\n".join(lines)

    # ── Errors
    lines.append(f"### 🔍 {n} Issue{'s' if n > 1 else ''} Found\n")

    for i, err in enumerate(errors, 1):
        lines.append(f"---")
        lines.append(f"**{i}. {err['category_label']}**")
        lines.append(f"❌ **Error Pattern:** `{err['wrong_template']}`")
        lines.append(f"✅ **Correct Pattern:** `{err['correct_template']}`")
        lines.append(f"📖 **Why:** {err['explanation']}")
        lines.append(f"📌 **Rule:** *{err['rule']}*")
        lines.append(f"💡 **Tip:** {err['tip']}")
        if err.get("examples"):
            lines.append("📝 **Examples:**")
            for ex in err["examples"][:2]:
                lines.append(f"   • {ex}")
        lines.append("")

    # ── Categories affected
    cats = result.get("categories_affected", [])
    if cats:
        lines.append(f"---")
        lines.append(f"### 📋 Topics to Review")
        for c in cats:
            lines.append(f"• {c}")
        lines.append("")

    # ── Personal tip
    pt = result.get("personal_tip", "")
    if pt and "Keep practicing" not in pt:
        lines.append(f"---")
        lines.append(f"### 🎯 Personalized Feedback")
        lines.append(f"*{pt}*\n")

    # ── Practice suggestion
    lines.append(f"---")
    lines.append("### 🏋️ Practice Exercise")
    lines.append("Now rewrite your original sentence applying ALL the corrections above.")
    lines.append("Then try the **Grammar Challenge** for topic-wise MCQ practice!\n")

    return "\n".join(lines)


def get_speaking_feedback(topic: str, speech: str) -> str:
    """Generate speaking feedback from dataset."""
    topic_data = SPEAKING_TOPICS.get(topic, {})
    
    response = f"🎯 **Speaking Feedback — Topic: {topic_data.get('title', topic)}**\n\n"
    
    # Basic assessment
    word_count = len(speech.split())
    response += f"📊 **Your Response Stats:**\n"
    response += f"• Words used: {word_count}\n"
    response += f"• Recommended: 100–200 words for 2-minute speech\n\n"
    
    # Grammar check
    grammar_issues = []
    for m in TRANSLATION_PATTERNS["common_mistakes_indians"]:
        if m["wrong"].lower() in speech.lower():
            grammar_issues.append(m)
    
    if grammar_issues:
        response += f"🔍 **Grammar Corrections:**\n"
        for m in grammar_issues[:3]:
            response += f"• ❌ '{m['wrong']}' → ✅ '{m['correct']}' ({m['reason']})\n"
        response += "\n"
    else:
        response += f"✅ **Grammar:** Looks good! No major mistakes spotted.\n\n"
    
    # Content feedback
    if topic_data:
        response += f"📋 **Content Checklist (Did you cover these?):**\n"
        for point in topic_data.get("key_points", []):
            response += f"• {point}\n"
        response += "\n"
        
        response += f"💡 **Vocabulary Suggestions (Use these next time):**\n"
        for phrase in topic_data.get("sample_vocabulary", [])[:3]:
            response += f"• {phrase}\n"
        response += "\n"
        
        response += f"🌟 **Model Answer (Study this):**\n"
        response += f"*{topic_data.get('model_answer', '')}*\n\n"
        
        response += f"🗣️ **Pro Tips:**\n"
        for tip in topic_data.get("tips", []):
            response += f"• {tip}\n"
    
    response += f"\n🏋️ **Practice Task:** Record yourself speaking on this topic for 2 minutes. Compare with the model answer above!\n"
    response += f"\n❓ Which part of speaking would you like to improve — vocabulary, grammar, or fluency?"
    
    return response


def get_interview_feedback(question: str, answer: str) -> str:
    """Generate interview feedback from dataset."""
    # Find matching question
    all_qa = []
    for category in INTERVIEW_QA.values():
        if isinstance(category, list):
            all_qa.extend(category)
    
    matched = None
    for qa in all_qa:
        if isinstance(qa, dict) and any(word in question.lower() for word in qa.get("question", "").lower().split()[:3]):
            matched = qa
            break
    
    word_count = len(answer.split())
    response = f"💼 **Interview Answer Evaluation**\n\n"
    response += f"❓ **Question:** {question}\n\n"
    response += f"📊 **Score Card:**\n"
    response += f"| Category | Score | Feedback |\n"
    response += f"|---|---|---|\n"
    
    # Score based on word count and common phrases
    grammar_score = 8 if word_count > 30 else 6
    vocab_score = 8 if any(w in answer.lower() for w in ["achieve", "accomplish", "develop", "implement", "collaborate"]) else 6
    fluency_score = 7 if word_count > 50 else 5
    confidence_score = 8 if not any(w in answer.lower() for w in ["i think maybe", "i'm not sure", "probably"]) else 6
    prof_score = 8 if not any(w in answer.lower() for w in ["basically", "like", "you know", "umm"]) else 6
    
    response += f"| Grammar | {grammar_score}/10 | {'Good sentence structure' if grammar_score > 7 else 'Work on grammar accuracy'} |\n"
    response += f"| Vocabulary | {vocab_score}/10 | {'Good word choice' if vocab_score > 7 else 'Use more professional vocabulary'} |\n"
    response += f"| Fluency | {fluency_score}/10 | {'Good length and flow' if fluency_score > 6 else 'Expand your answer more'} |\n"
    response += f"| Confidence | {confidence_score}/10 | {'Sounds confident' if confidence_score > 7 else 'Avoid uncertain phrases'} |\n"
    response += f"| Professionalism | {prof_score}/10 | {'Professional tone' if prof_score > 7 else 'Avoid casual language'} |\n\n"
    
    # Grammar check
    grammar_issues = [m for m in TRANSLATION_PATTERNS["common_mistakes_indians"] if m["wrong"].lower() in answer.lower()]
    if grammar_issues:
        response += f"🔍 **Grammar Corrections:**\n"
        for m in grammar_issues[:3]:
            response += f"• ❌ '{m['wrong']}' → ✅ '{m['correct']}'\n"
        response += "\n"
    
    # Model answer
    if matched:
        response += f"🌟 **Model Answer:**\n*{matched.get('model_answer', '')}*\n\n"
        response += f"💡 **Key Tips:**\n"
        for tip in matched.get("tips", [])[:4]:
            response += f"• {tip}\n"
        response += "\n"
    
    # Professional vocabulary suggestions
    response += f"💼 **Power Words to Use:**\n"
    response += f"• accomplished, delivered, implemented, spearheaded\n"
    response += f"• result-oriented, proactive, collaborative, innovative\n"
    response += f"• 'I take initiative...', 'I thrive under pressure...', 'I am passionate about...'\n\n"
    
    response += f"🏋️ **Practice:** Answer the same question again incorporating the model answer's style!\n"
    response += f"\n❓ Which interview question would you like to practice next?"
    
    return response


def get_translation_help(text, direction="en_to_hi"):
    print("Direction:", direction)
    print("Input:", text)
    print("JSON PATH:", JSON_PATH)
    print("Exists:", Path(JSON_PATH).exists())
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(type(data))
    print(data.keys())
    if direction in ["en-hi", "en_to_hi", "enhi"]:
        print("EN dictionary size:", len(EN_TO_HI))
        print("Found:", text in EN_TO_HI)

    elif direction in ["hi-en", "hi_to_en", "hien"]:
        print("HI dictionary size:", len(HI_TO_EN))
        print("Found:", text in HI_TO_EN)
    text = clean_text(text)

    # English -> Hindi
    if direction in ["en-hi", "en_to_hi", "enhi"]:

        if text in EN_TO_HI:
            return EN_TO_HI[text]

        match = get_close_matches(text, EN_TO_HI.keys(), n=1, cutoff=0.60)

        if match:
            return EN_TO_HI[match[0]]

        return None

    # Hindi -> English
    elif direction in ["hi-en", "hi_to_en", "hien"]:

        if text in HI_TO_EN:
            return HI_TO_EN[text]

        match = get_close_matches(text, HI_TO_EN.keys(), n=1, cutoff=0.60)

        if match:
            return HI_TO_EN[match[0]]

        return None

    return None

def get_pronunciation_analysis(sentence: str) -> str:
    """Analyze pronunciation of a sentence from dataset."""
    response = f"🎤 **Pronunciation Analysis**\n\n"
    response += f"📝 **Sentence:** *{sentence}*\n\n"
    
    # Check for known difficult sounds
    difficult_words = []
    for guide in PRONUNCIATION_GUIDE["common_indian_mistakes"]:
        for word in guide["practice"]:
            if word.lower() in sentence.lower():
                difficult_words.append({"word": word, "guide": guide})
                break
    
    if difficult_words:
        response += f"⚠️ **Difficult Words for Indian Speakers:**\n"
        for item in difficult_words[:4]:
            g = item["guide"]
            response += f"\n🔸 **{item['word']}** ({g['sound']} sound)\n"
            response += f"  Problem: {g['problem']}\n"
            response += f"  Fix: {g['correct']}\n"
    else:
        response += f"✅ **Good news!** No major pronunciation trouble-spots found in this sentence.\n\n"
    
    response += f"\n🎵 **Word Stress Guide:**\n"
    for rule in random.sample(PRONUNCIATION_GUIDE["word_stress_rules"], 3):
        response += f"• {rule}\n"
    
    response += f"\n🌊 **Fluency Tips:**\n"
    response += f"• Link words together: 'Could you' → 'Couldja'\n"
    response += f"• Use natural rhythm — not every word gets equal stress\n"
    response += f"• Breathe at punctuation marks\n"
    response += f"• Slow down for important words, speed up for less important ones\n"
    
    response += f"\n🏋️ **Tongue Twister Practice:**\n"
    tt = random.choice(PRONUNCIATION_GUIDE["tongue_twisters"])
    response += f"*'{tt}'*\n"
    response += f"Say it slowly 3 times, then gradually faster!\n"
    
    response += f"\n❓ Which sound do you find most difficult to pronounce?"
    return response


def get_daily_challenge(challenge_type: str, difficulty: str = "medium") -> dict:
    """Return a daily challenge from the local dataset."""
    if challenge_type == "grammar":
        questions = random.sample(GRAMMAR_QUIZZES, min(5, len(GRAMMAR_QUIZZES)))
        return {"type": "grammar", "questions": questions, "title": "📖 Grammar Quiz"}
    elif challenge_type == "vocabulary":
        questions = random.sample(VOCABULARY_QUIZZES, min(5, len(VOCABULARY_QUIZZES)))
        return {"type": "vocabulary", "questions": questions, "title": "📚 Vocabulary Quiz"}
    elif challenge_type == "speaking":
        topic_key = random.choice(list(SPEAKING_TOPICS.keys()))
        topic = SPEAKING_TOPICS[topic_key]
        return {
            "type": "speaking",
            "title": "🗣️ Speaking Challenge",
            "topic": topic["title"],
            "prompt": topic["prompt"],
            "key_points": topic["key_points"],
            "vocabulary": topic["sample_vocabulary"],
            "model": topic["model_answer"][:300] + "...",
            "tips": topic["tips"]
        }
    elif challenge_type == "pronunciation":
        return {
            "type": "pronunciation",
            "title": "🎤 Pronunciation Challenge",
            "tongue_twister": random.choice(PRONUNCIATION_GUIDE["tongue_twisters"]),
            "sentences": random.sample(
                [p["practice"][:3] for p in PRONUNCIATION_GUIDE["common_indian_mistakes"] if p.get("practice")],
                min(3, len(PRONUNCIATION_GUIDE["common_indian_mistakes"]))
            ),
            "tips": PRONUNCIATION_GUIDE["word_stress_rules"][:3],
            "common_mistakes": random.sample(PRONUNCIATION_GUIDE["common_indian_mistakes"], 3)
        }
    return {}
