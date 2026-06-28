"""
grammar_engine.py — Intelligent offline grammar engine.
Token-aware checks + targeted regex for high accuracy.
No external APIs. Fully offline.
"""
import re
import json
import os
from collections import defaultdict
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
#  WORD LISTS
# ─────────────────────────────────────────────────────────────────

IRREGULAR_PAST = {
    "went":"go","came":"come","saw":"see","gave":"give","took":"take",
    "wrote":"write","spoke":"speak","ate":"eat","ran":"run","made":"make",
    "got":"get","bought":"buy","thought":"think","brought":"brought",
    "caught":"catch","fought":"fight","found":"find","kept":"keep",
    "left":"leave","lost":"lose","met":"meet","paid":"pay","read":"read",
    "said":"say","sat":"sit","slept":"sleep","spent":"spend","stood":"stand",
    "taught":"teach","told":"tell","understood":"understand","won":"win",
    "wore":"wear","built":"build","chose":"choose","drove":"drive",
    "felt":"feel","fell":"fall","flew":"fly","grew":"grow","held":"hold",
    "knew":"know","led":"lead","meant":"mean","rode":"ride","rose":"rise",
    "sent":"send","set":"set","showed":"show","sang":"sing","swam":"swim",
    "threw":"throw",
}
IRREGULAR_PAST_PARTICIPLE = {
    "went":"gone","came":"come","saw":"seen","gave":"given","took":"taken",
    "wrote":"written","spoke":"spoken","ate":"eaten","ran":"run","made":"made",
    "got":"got","bought":"bought","thought":"thought","brought":"brought",
    "caught":"caught","fought":"fought","found":"found","kept":"kept",
    "left":"left","lost":"lost","met":"met","paid":"paid","said":"said",
    "sat":"sat","slept":"slept","spent":"spent","stood":"stood",
    "taught":"taught","told":"told","won":"won","wore":"worn",
    "built":"built","chose":"chosen","drove":"driven","felt":"felt",
    "fell":"fallen","flew":"flown","grew":"grown","held":"held",
    "knew":"known","led":"led","meant":"meant","rode":"ridden",
    "rose":"risen","sent":"sent","set":"set","sang":"sung","swam":"swum",
    "threw":"thrown","did":"done","had":"had","was":"been","were":"been",
}

STATIVE_VERBS = {
    "know","understand","believe","think","prefer","love","hate","like",
    "want","need","seem","appear","contain","belong","own","possess",
    "involve","mean","matter","mind","remember","forget","recognise",
    "recognize","realize","suppose","doubt","impress","satisfy","please",
}

PAST_TIME_WORDS = re.compile(
    r'\b(yesterday|last\s+\w+|ago|\d+\s+years?\s+ago|\d+\s+days?\s+ago|'
    r'in\s+19\d\d|in\s+20\d\d|last\s+year|last\s+month|last\s+week|'
    r'last\s+night|last\s+monday|last\s+tuesday|last\s+wednesday|'
    r'last\s+thursday|last\s+friday|last\s+saturday|last\s+sunday)\b',
    re.IGNORECASE
)

UNCOUNTABLE = {
    "information","advice","furniture","luggage","equipment","knowledge",
    "progress","research","scenery","traffic","weather","news","water",
    "milk","rice","sugar","salt","sand","air","oil","butter","bread",
    "meat","gold","silver","iron","paper","wood","glass","plastic","soil",
    "dust","smoke","fire","light","heat","music","money","time","work",
    "food","fruit","homework","vocabulary","grammar","poetry","beauty",
    "courage","happiness","honesty","intelligence","patience","wisdom",
}

SINCE_FOR_WORDS = re.compile(
    r'\b(since|for)\s+(\d+|a|an|several|many|few|the\s+last|some)\b',
    re.IGNORECASE
)

CATEGORY_LABELS = {
    "subject_verb_agreement": "Subject–Verb Agreement",
    "tense":                  "Tense Error",
    "articles":               "Articles (A/An/The)",
    "prepositions":           "Prepositions",
    "stative_verbs":          "Stative Verbs",
    "double_negative":        "Double Negatives",
    "indian_english":         "Indian English",
    "pronouns":               "Pronouns",
    "modals":                 "Modal Verbs",
    "word_form":              "Word Forms",
    "capitalization":         "Capitalization",
    "reported_speech":        "Reported Speech",
    "punctuation":            "Punctuation",
    "comparative":            "Comparatives/Superlatives",
    "questions":              "Question Formation",
    "passive_voice":          "Passive Voice",
    "confusable_words":       "Confusable Words",
    "countable_uncountable":  "Countable vs Uncountable",
}


# ─────────────────────────────────────────────────────────────────
#  INDIVIDUAL CHECKER FUNCTIONS
#  Each returns list of error dicts or []
# ─────────────────────────────────────────────────────────────────

def _err(id_, category, wrong, correct, explanation, rule, tip, examples, fix=None):
    return {
        "id": id_,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "wrong_template": wrong,
        "correct_template": correct,
        "explanation": explanation,
        "rule": rule,
        "tip": tip,
        "examples": examples,
        "fix": fix,
    }


def check_sva(text):
    errors = []
    t = text.lower()

    # X and Y + is/was (compound subject needs plural verb: are/were)
    m = re.search(r'\b(\w+)\s+and\s+(\w+(?:\s+\w+)?)\s+(is|was)\b', t)
    if m:
        errors.append(_err(
            "sva_00", "subject_verb_agreement",
            "[person] and [person] + is/was",
            "[person] and [person] + are/were",
            "When two subjects are joined by 'and', the verb must be plural: 'are' (not 'is'), 'were' (not 'was').",
            "Compound Subjects with AND Take Plural Verb",
            "Ram AND Shyam ARE coming ✅ | Ram AND Shyam IS coming ❌. Two people = plural = are/were.",
            ["❌ Ram and Shyam is coming. → ✅ Ram and Shyam are coming.",
             "❌ My friend and I was late. → ✅ My friend and I were late.",
             "❌ Me and my friend is going. → ✅ My friend and I are going."],
            lambda t: re.sub(
                r'\b(\w+\s+and\s+\w+(?:\s+\w+)?)\s+is\b',
                lambda m: m.group(1) + " are", t, flags=re.IGNORECASE
            )
        ))

    # they/we/you + is
    if re.search(r'\b(they|we|you)\s+is\b', t):
        errors.append(_err(
            "sva_01", "subject_verb_agreement",
            "they/we/you + is", "they/we/you + are",
            "With plural subjects (they, we) and second-person (you), use 'are' — never 'is'.",
            "Are (Not Is) with They/We/You",
            "Quick check: I→am, he/she/it→is, we/you/they→ARE.",
            ["❌ They is good. → ✅ They are good.",
             "❌ We is ready. → ✅ We are ready.",
             "❌ You is right. → ✅ You are right."],
            lambda t: re.sub(r'\b(they|we|you)\s+is\b', lambda m: m.group(1)+" are", t, flags=re.IGNORECASE)
        ))

    # he/she/it + are
    if re.search(r'\b(he|she|it)\s+are\b', t):
        errors.append(_err(
            "sva_02", "subject_verb_agreement",
            "he/she/it + are", "he/she/it + is",
            "With singular third-person subjects (he, she, it), use 'is' — never 'are'.",
            "Is (Not Are) with He/She/It",
            "he/she/it → IS always. 'She are happy' is ALWAYS wrong.",
            ["❌ She are happy. → ✅ She is happy.",
             "❌ He are a doctor. → ✅ He is a doctor.",
             "❌ It are very hot. → ✅ It is very hot."],
            lambda t: re.sub(r'\b(he|she|it)\s+are\b', lambda m: m.group(1)+" is", t, flags=re.IGNORECASE)
        ))

    # I + is/are
    if re.search(r'\bi\s+(is|are)\b', t):
        errors.append(_err(
            "sva_03", "subject_verb_agreement",
            "I + is/are", "I + am",
            "With 'I', always use 'am'. Never 'is' or 'are'.",
            "Am (Not Is/Are) with I",
            "I→AM only. 'I is' and 'I are' are always wrong.",
            ["❌ I is fine. → ✅ I am fine.",
             "❌ I are ready. → ✅ I am ready."],
            lambda t: re.sub(r'\bI\s+(is|are)\b', 'I am', t)
        ))

    # he/she/it + don't
    if re.search(r'\b(he|she|it|[A-Z][a-z]+)\s+(don\'t|dont)\b', text):
        errors.append(_err(
            "sva_04", "subject_verb_agreement",
            "he/she/it + don't", "he/she/it + doesn't",
            "With he/she/it (third-person singular), use 'doesn't' not 'don't'.",
            "Subject–Verb Agreement: Doesn't with He/She/It",
            "Trick: If you can replace the subject with 'he'/'she', use 'doesn't'.",
            ["❌ She don't like tea. → ✅ She doesn't like tea.",
             "❌ He don't know. → ✅ He doesn't know.",
             "❌ Ram don't want to come. → ✅ Ram doesn't want to come."],
            lambda t: re.sub(r"\bdon't\b", "doesn't", t, flags=re.IGNORECASE)
        ))

    # he/she/it + have (not have been)
    if re.search(r'\b(he|she|it)\s+have\b(?!\s+been)', text, re.IGNORECASE):
        errors.append(_err(
            "sva_05", "subject_verb_agreement",
            "he/she/it + have", "he/she/it + has",
            "With he/she/it, always use 'has' (not 'have') in present tense.",
            "Has vs Have",
            "he/she/it → HAS. I/we/you/they → HAVE.",
            ["❌ She have a car. → ✅ She has a car.",
             "❌ He have two brothers. → ✅ He has two brothers."],
            lambda t: re.sub(r'\b(he|she|it)\s+have\b', lambda m: m.group(1)+" has", t, flags=re.IGNORECASE)
        ))

    # they/we/you + was
    if re.search(r'\b(they|we|you)\s+was\b', t):
        errors.append(_err(
            "sva_06", "subject_verb_agreement",
            "they/we/you + was", "they/we/you + were",
            "Past tense of 'be': I/he/she/it → was. We/you/they → were.",
            "Was vs Were",
            "Was = singular. Were = plural. 'They was' is ALWAYS wrong.",
            ["❌ They was playing. → ✅ They were playing.",
             "❌ We was going. → ✅ We were going."],
            lambda t: re.sub(r'\b(they|we|you)\s+was\b', lambda m: m.group(1)+" were", t, flags=re.IGNORECASE)
        ))

    # everyone/somebody/nobody + are/were/have
    if re.search(r'\b(everyone|everybody|someone|somebody|anyone|anybody|no\s*one|nobody|each|either|neither)\s+(are|were|have)\b', t):
        errors.append(_err(
            "sva_07", "subject_verb_agreement",
            "everyone/someone/nobody + are/were/have",
            "everyone/someone/nobody + is/was/has",
            "Indefinite pronouns (everyone, somebody, nobody, each, either, neither) are grammatically singular.",
            "Indefinite Pronouns Take Singular Verb",
            "Even though 'everyone' sounds plural, it is grammatically singular. Test: 'Everyone IS here' ✅",
            ["❌ Everyone are ready. → ✅ Everyone is ready.",
             "❌ Nobody were home. → ✅ Nobody was home.",
             "❌ Each of them have finished. → ✅ Each of them has finished."],
        ))

    # uncountable noun + are/were
    for word in UNCOUNTABLE:
        if re.search(rf'\b{word}\s+(are|were)\b', t):
            errors.append(_err(
                "sva_08", "subject_verb_agreement",
                f"{word} + are/were", f"{word} + is/was",
                f"'{word.capitalize()}' is an uncountable noun — it always takes a singular verb.",
                "Uncountable Nouns Take Singular Verb",
                "Uncountable nouns (news, information, advice, furniture, luggage) are always singular.",
                [f"❌ The {word} are bad. → ✅ The {word} is bad."],
            ))
            break

    # he/she/it + base verb (missing -s): simple present
    PLAIN_VERBS = r'\b(go|come|eat|play|run|work|study|walk|talk|live|write|read|speak|drive|sing|cook|sleep|watch|like|love|hate|know|think|want|need|help|learn|make|take|give|buy|sell|start|finish|leave|arrive|sit|stand|swim|teach|clean|open|close|call|visit|plan|try|use|ask|tell|show|carry|find|keep|meet|join|travel|wait|stay|decide|forget|remember|believe|understand|explain|choose|follow|change|save|spend|earn|share|support|return|build|bring|feel|put|send|receive|grow|hold|fly|draw|break|cut|fight|win|lose|pay|wear|hear|see|catch|fall|rise|ride|throw|become|seem|appear|contain|belong|own|include|require|involve|produce|provide|create|offer|allow|accept|avoid|add|apply|begin|compare|consider|control|cover|deal|develop|discuss|do|drink|drop|enjoy|enter|exist|expect|experience|fail|fix|focus|gain|get|give|handle|happen|hit|hold|hope|improve|increase|indicate|introduce|manage|move|note|occur|perform|place|prepare|prevent|process|push|reach|reduce|remain|remove|report|respond|result|reveal|review|set|show|solve|suggest|support|test|turn)\b'
    m = re.search(r'\b(he|she|it)\s+' + PLAIN_VERBS, text, re.IGNORECASE)
    if m:
        verb = m.group(2)
        errors.append(_err(
            "sva_09", "subject_verb_agreement",
            f"he/she/it + {verb} (base form)",
            f"he/she/it + {verb}s/es",
            f"In Simple Present, he/she/it must have -s or -es added to the verb. '{verb}' → '{verb}s'.",
            "Simple Present: He/She/It + Verb+S",
            "I go, you go, they go — BUT he GOES, she PLAYS, it WORKS. Always add -s/-es!",
            [f"❌ He {verb} every day. → ✅ He {verb}s every day.",
             "❌ She play cricket. → ✅ She plays cricket.",
             "❌ It work well. → ✅ It works well."],
        ))

    return errors

def check_tense(text):
    errors = []
    t = text

    # Present/Past Continuous + specific past time word
    # e.g. "is going to market yesterday" / "was playing yesterday"
    if re.search(r'\b(is|am|are|was|were)\s+\w+ing\b', t, re.IGNORECASE) and PAST_TIME_WORDS.search(t):
        errors.append(_err(
            "tense_00", "tense",
            "is/am/are + V-ing + yesterday/last.../ago",
            "Simple Past (V2) for completed past actions",
            "Continuous tense describes ongoing actions, NOT completed past events. With 'yesterday', 'last week', 'ago' — use Simple Past.",
            "No Continuous Tense with Past Time Words",
            "yesterday/last week/ago → Simple Past. 'was going yesterday' ❌ → 'went yesterday' ✅",
            ["❌ I am going to market yesterday. → ✅ I went to market yesterday.",
             "❌ She was playing cricket last Monday. → ✅ She played cricket last Monday.",
             "❌ He is eating lunch an hour ago. → ✅ He ate lunch an hour ago."],
        ))

    # Present Perfect + specific past time word
    has_past_time = PAST_TIME_WORDS.search(t)
    has_pp = re.search(r'\b(have|has)\s+\w+(ed|en|one|awn|own|ain|een|ung|unk|ang|ank|ound|ept|elt|ent|eft|ost|old|ight|aught|ought)\b', t, re.IGNORECASE)
    has_pp_simple = re.search(r'\b(have|has)\s+(seen|been|done|gone|come|eaten|taken|given|run|made|got|bought|thought|brought|caught|found|kept|left|lost|met|paid|said|sat|slept|spent|stood|taught|told|won|worn|built|chosen|driven|felt|fallen|flown|grown|held|known|led|meant|ridden|risen|sent|sung|swum|thrown|written|spoken|read)\b', t, re.IGNORECASE)

    if has_past_time and (has_pp or has_pp_simple):
        errors.append(_err(
            "tense_01", "tense",
            "have/has + V3 + past time word (yesterday/last year/ago)",
            "Simple Past (V2) + past time word",
            "Present Perfect CANNOT be used with specific past time markers like 'yesterday', 'last year', 'ago', or a specific year. Use Simple Past instead.",
            "Present Perfect vs Simple Past",
            "If you see: yesterday / last week / last year / in [year] / [number] ago → ALWAYS Simple Past.",
            ["❌ I have seen him yesterday. → ✅ I saw him yesterday.",
             "❌ She has gone to Delhi last week. → ✅ She went to Delhi last week.",
             "❌ They have finished it 2 hours ago. → ✅ They finished it 2 hours ago."],
        ))

    # don't/doesn't/didn't + had  (very common Indian error: "we don't had")
    if re.search(r"\b(don't|dont|doesn't|didn't|didn't)\s+(had|have\s+had)\b", t, re.IGNORECASE):
        errors.append(_err(
            "tense_don't_had", "tense",
            "don't/doesn't/didn't + had",
            "didn't + have  OR  don't + have",
            "'Don't had' and 'didn't had' are both wrong. Use 'didn't have' (past) or 'don't have' (present). 'Had' is already past — adding 'don't/didn't' creates a tense conflict.",
            "Don't/Didn't Cannot Be Used with 'Had'",
            "didn't HAVE ✅ | didn't HAD ❌. don't HAVE ✅ | don't HAD ❌.",
            ["❌ We don't had enough time. → ✅ We didn't have enough time.",
             "❌ She didn't had money. → ✅ She didn't have money.",
             "❌ I don't had a phone. → ✅ I don't have a phone."],
            lambda t: re.sub(r"\b(don't|dont)\s+had\b", "didn't have",
                        re.sub(r"\bdidn't\s+had\b", "didn't have", t, flags=re.IGNORECASE),
                        flags=re.IGNORECASE)
        ))

    # have/has + V2 (past tense form used instead of V3)
    m = re.search(r'\b(have|has)\s+(went|came|did|ran|gave|took|wrote|spoke|ate|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore)\b', t, re.IGNORECASE)
    if m:
        v2 = m.group(2).lower()
        v3 = IRREGULAR_PAST_PARTICIPLE.get(v2, v2)
        errors.append(_err(
            "tense_02", "tense",
            f"have/has + {v2} (past tense V2)",
            f"have/has + {v3} (past participle V3)",
            f"After 'have/has', always use the past participle (V3), not the simple past (V2). '{v2}' is V2 — the correct V3 is '{v3}'.",
            "Present Perfect Requires Past Participle (V3)",
            "have GONE ✅ (not 'have went'). has DONE ✅ (not 'has did'). has SEEN ✅ (not 'has saw').",
            [f"❌ I have {v2} there. → ✅ I have {v3} there.",
             "❌ She has went to school. → ✅ She has gone to school.",
             "❌ He has did the work. → ✅ He has done the work."],
            lambda t: re.sub(
                r'\b(have|has)\s+(went|came|did|ran|gave|took|wrote|spoke|ate|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore)\b',
                lambda x: x.group(1)+" "+IRREGULAR_PAST_PARTICIPLE.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))

    # am/is/are + V-ing + since/for → should be have/has been + V-ing
    m = re.search(r'\b(am|is|are|was|were)\s+(\w+ing)\b.{0,40}' + SINCE_FOR_WORDS.pattern, t, re.IGNORECASE)
    if m:
        errors.append(_err(
            "tense_03", "tense",
            "am/is/are + V-ing + since/for",
            "have/has been + V-ing + since/for",
            "For actions that started in the past and are still continuing, use Present Perfect Continuous: have/has been + V-ing. NOT simple present continuous.",
            "Present Perfect Continuous with Since/For",
            "since 2018 / for 5 years + ongoing action → have/has BEEN + V-ing",
            ["❌ I am living here since 5 years. → ✅ I have been living here for 5 years.",
             "❌ She is working here since 2018. → ✅ She has been working here since 2018.",
             "❌ He is studying for 3 hours. → ✅ He has been studying for 3 hours."],
        ))
    else:
        # Also catch: am/is/are + action + since/for (without V-ing directly adjacent)
        m2 = re.search(r'\b(am|is|are)\b.{0,30}\b(since|for)\s+\d+', t, re.IGNORECASE)
        if m2:
            errors.append(_err(
                "tense_03b", "tense",
                "am/is/are ... since/for [number]",
                "have/has been + V-ing ... since/for [number]",
                "For ongoing actions with 'since' or 'for', use Present Perfect Continuous — not simple present continuous.",
                "Present Perfect Continuous with Since/For",
                "I am doing this since 5 years ❌ → I have been doing this for 5 years ✅",
                ["❌ I am doing this job since 5 years. → ✅ I have been doing this job for 5 years.",
                 "❌ She is living here since 2010. → ✅ She has been living here since 2010."],
            ))

    # will + V-ing
    m = re.search(r'\bwill\s+(\w+ing)\b', t, re.IGNORECASE)
    if m:
        base = m.group(1)[:-3]
        errors.append(_err(
            "tense_04", "tense",
            f"will + {m.group(1)} (V-ing)",
            f"will + {base} (base verb V1)",
            "After 'will', always use the BASE form of the verb (V1), NOT the -ing form.",
            "Future Simple: Will + Base Verb (V1)",
            "will GO ✅ | will COME ✅ | will going ❌ | will coming ❌",
            ["❌ I will going to Delhi. → ✅ I will go to Delhi.",
             "❌ She will coming tomorrow. → ✅ She will come tomorrow."],
            lambda t: re.sub(r'\bwill\s+(\w+)ing\b', lambda x: "will "+x.group(1), t, flags=re.IGNORECASE)
        ))

    # didn't + V2 (past tense)
    m = re.search(r"\b(did\s*not|didn't)\s+(went|came|saw|bought|thought|brought|took|wrote|spoke|taught|kept|found|sent|told|felt|led|held|met|ate|gave|ran|made|got|drove|wore|knew|grew|flew|fell|chose|built|caught|fought|lost|paid|sat|slept|spent|stood|threw|won)\b", t, re.IGNORECASE)
    if m:
        v2 = m.group(2).lower()
        base = IRREGULAR_PAST.get(v2, v2)
        errors.append(_err(
            "tense_05", "tense",
            f"didn't + {v2} (past form)",
            f"didn't + {base} (base form)",
            f"After 'did not/didn't', ALWAYS use the BASE form (V1). 'did' already carries the past tense.",
            "Auxiliary 'Did' Requires Base Form (V1)",
            "didn't GO ✅ | didn't WENT ❌. The 'did' handles the tense — main verb returns to base.",
            [f"❌ I didn't {v2}. → ✅ I didn't {base}.",
             "❌ She didn't came. → ✅ She didn't come.",
             "❌ He didn't went. → ✅ He didn't go."],
            lambda t: re.sub(
                r"\b(did\s*not|didn't)\s+(went|came|saw|bought|thought|brought|took|wrote|spoke|taught|kept|found|sent|told|felt|led|held|met|ate|gave|ran|made|got)\b",
                lambda x: x.group(1)+" "+IRREGULAR_PAST.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))

    # incorrect irregular past tense (buyed, goed, etc.)
    wrong_past = {
        "buyed":"bought","goed":"went","thinked":"thought","bringed":"brought",
        "catched":"caught","taked":"took","writed":"wrote","speaked":"spoke",
        "teached":"taught","readed":"read","finded":"found","meeted":"met",
        "sended":"sent","telled":"told","feeled":"felt","keeped":"kept",
        "leaded":"led","holded":"held","losted":"lost","payed":"paid",
        "winned":"won","beated":"beat","comed":"came","heared":"heard",
        "knowed":"knew","leaved":"left","maked":"made","putted":"put",
        "runned":"ran","sitted":"sat","sleeped":"slept","spended":"spent",
        "standed":"stood","throwed":"threw","weard":"wore",
    }
    for wv, cv in wrong_past.items():
        if re.search(rf'\b{wv}\b', t, re.IGNORECASE):
            errors.append(_err(
                "tense_06", "tense",
                f"{wv} (wrong past tense)",
                f"{cv} (correct irregular past tense)",
                f"'{wv}' is NOT a valid English word. The correct past tense is '{cv}'.",
                "Irregular Past Tense Verbs",
                "go→went, buy→bought, think→thought, bring→brought, take→took, write→wrote.",
                [f"❌ I {wv} a phone. → ✅ I {cv} a phone.",
                 "❌ She goed to school. → ✅ She went to school."],
                lambda t, wv=wv, cv=cv: re.sub(rf'\b{wv}\b', cv, t, flags=re.IGNORECASE)
            ))
            break

    return errors
    has_present_perfect = re.search(r'\b(have|has)\s+\w+(ed|en|one|awn|own|ain|een|ung|unk|ung|ang|ank|ound|ound|ept|elt|ent|ent|eft|ost|old|ight|aught|ought)\b', t, re.IGNORECASE)
    has_pp_simple = re.search(r'\b(have|has)\s+(seen|been|done|gone|come|eaten|taken|given|run|made|got|bought|thought|brought|caught|found|kept|left|lost|met|paid|said|sat|slept|spent|stood|taught|told|won|worn|built|chosen|driven|felt|fallen|flown|grown|held|known|led|meant|ridden|risen|sent|sung|swum|thrown|written|spoken|read)\b', t, re.IGNORECASE)

    if has_past_time and (has_present_perfect or has_pp_simple):
        errors.append(_err(
            "tense_01", "tense",
            "have/has + V3 + past time word (yesterday/last year/ago)",
            "Simple Past (V2) + past time word",
            "Present Perfect CANNOT be used with specific past time markers like 'yesterday', 'last year', 'ago', or a specific year. Use Simple Past instead.",
            "Present Perfect vs Simple Past",
            "If you see: yesterday / last week / last year / in [year] / [number] ago → ALWAYS Simple Past.",
            ["❌ I have seen him yesterday. → ✅ I saw him yesterday.",
             "❌ She has gone to Delhi last week. → ✅ She went to Delhi last week.",
             "❌ They have finished it 2 hours ago. → ✅ They finished it 2 hours ago."],
        ))

    # have/has + V2 (past tense form used instead of V3)
    m = re.search(r'\b(have|has)\s+(went|came|did|ran|gave|took|wrote|spoke|ate|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore)\b', t, re.IGNORECASE)
    if m:
        v2 = m.group(2).lower()
        v3 = IRREGULAR_PAST_PARTICIPLE.get(v2, v2+"n")
        errors.append(_err(
            "tense_02", "tense",
            f"have/has + {v2} (past tense V2)",
            f"have/has + {v3} (past participle V3)",
            f"After 'have/has', always use the past participle (V3), not the simple past (V2). '{v2}' is V2 — the correct V3 is '{v3}'.",
            "Present Perfect Requires Past Participle (V3)",
            "have GONE ✅ (not 'have went'). has DONE ✅ (not 'has did'). has SEEN ✅ (not 'has saw').",
            [f"❌ I have {v2} there. → ✅ I have {v3} there.",
             "❌ She has went to school. → ✅ She has gone to school.",
             "❌ He has did the work. → ✅ He has done the work."],
            lambda t: re.sub(
                r'\b(have|has)\s+(went|came|did|ran|gave|took|wrote|spoke|ate|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore)\b',
                lambda x: x.group(1)+" "+IRREGULAR_PAST_PARTICIPLE.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))

    # am/is/are + V-ing + since/for → should be have/has been + V-ing
    m = re.search(r'\b(am|is|are|was|were)\s+(\w+ing)\b.{0,40}' + SINCE_FOR_WORDS.pattern, t, re.IGNORECASE)
    if m:
        errors.append(_err(
            "tense_03", "tense",
            "am/is/are + V-ing + since/for",
            "have/has been + V-ing + since/for",
            "For actions that started in the past and are still continuing, use Present Perfect Continuous: have/has been + V-ing. NOT simple present continuous.",
            "Present Perfect Continuous with Since/For",
            "since 2018 / for 5 years + ongoing action → have/has BEEN + V-ing",
            ["❌ I am living here since 5 years. → ✅ I have been living here for 5 years.",
             "❌ She is working here since 2018. → ✅ She has been working here since 2018.",
             "❌ He is studying for 3 hours. → ✅ He has been studying for 3 hours."],
        ))
    else:
        # Also catch: am/is/are + action + since/for (without V-ing directly adjacent)
        m2 = re.search(r'\b(am|is|are)\b.{0,30}\b(since|for)\s+\d+', t, re.IGNORECASE)
        if m2:
            errors.append(_err(
                "tense_03b", "tense",
                "am/is/are ... since/for [number]",
                "have/has been + V-ing ... since/for [number]",
                "For ongoing actions with 'since' or 'for', use Present Perfect Continuous — not simple present continuous.",
                "Present Perfect Continuous with Since/For",
                "I am doing this since 5 years ❌ → I have been doing this for 5 years ✅",
                ["❌ I am doing this job since 5 years. → ✅ I have been doing this job for 5 years.",
                 "❌ She is living here since 2010. → ✅ She has been living here since 2010."],
            ))

    # will + V-ing
    m = re.search(r'\bwill\s+(\w+ing)\b', t, re.IGNORECASE)
    if m:
        base = m.group(1)[:-3]  # strip -ing
        errors.append(_err(
            "tense_04", "tense",
            f"will + {m.group(1)} (V-ing)",
            f"will + {base} (base verb V1)",
            "After 'will', always use the BASE form of the verb (V1), NOT the -ing form.",
            "Future Simple: Will + Base Verb (V1)",
            "will GO ✅ | will COME ✅ | will going ❌ | will coming ❌",
            ["❌ I will going to Delhi. → ✅ I will go to Delhi.",
             "❌ She will coming tomorrow. → ✅ She will come tomorrow."],
            lambda t: re.sub(r'\bwill\s+(\w+)ing\b', lambda x: "will "+x.group(1), t, flags=re.IGNORECASE)
        ))

    # didn't + V2 (past tense)
    m = re.search(r"\b(did\s*not|didn't)\s+(went|came|saw|bought|thought|brought|took|wrote|spoke|taught|kept|found|sent|told|felt|led|held|met|ate|gave|ran|made|got|drove|wore|knew|grew|flew|fell|chose|built|caught|fought|lost|paid|read|sat|slept|spent|stood|threw|won)\b", t, re.IGNORECASE)
    if m:
        v2 = m.group(2).lower()
        base = IRREGULAR_PAST.get(v2, v2)
        errors.append(_err(
            "tense_05", "tense",
            f"didn't + {v2} (past form)",
            f"didn't + {base} (base form)",
            f"After 'did not/didn't', ALWAYS use the BASE form (V1). 'did' already carries the past tense. '{v2}' is the past tense — use '{base}' instead.",
            "Auxiliary 'Did' Requires Base Form (V1)",
            "didn't GO ✅ | didn't WENT ❌. The 'did' handles the tense — main verb returns to base.",
            [f"❌ I didn't {v2}. → ✅ I didn't {base}.",
             "❌ She didn't came. → ✅ She didn't come.",
             "❌ He didn't went. → ✅ He didn't go."],
            lambda t: re.sub(
                r"\b(did\s*not|didn't)\s+(went|came|saw|bought|thought|brought|took|wrote|spoke|taught|kept|found|sent|told|felt|led|held|met|ate|gave|ran|made|got)\b",
                lambda x: x.group(1)+" "+IRREGULAR_PAST.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))

    # incorrect irregular past tense (buyed, goed, etc.)
    wrong_past = {
        "buyed":"bought","goed":"went","thinked":"thought","bringed":"brought",
        "catched":"caught","taked":"took","writed":"wrote","speaked":"spoke",
        "teached":"taught","readed":"read","finded":"found","meeted":"met",
        "sended":"sent","telled":"told","feeled":"felt","keeped":"kept",
        "leaded":"led","holded":"held","losted":"lost","payed":"paid",
        "winned":"won","beated":"beat","comed":"came","heared":"heard",
        "knowed":"knew","leaved":"left","maked":"made","putted":"put",
        "runned":"ran","sitted":"sat","sleeped":"slept","spended":"spent",
        "standed":"stood","throwed":"threw","weard":"wore",
    }
    for wv, cv in wrong_past.items():
        if re.search(rf'\b{wv}\b', t, re.IGNORECASE):
            errors.append(_err(
                "tense_06", "tense",
                f"{wv} (wrong past tense)",
                f"{cv} (correct irregular past tense)",
                f"'{wv}' is NOT a valid English word. The past tense of this verb is irregular: it's '{cv}'.",
                "Irregular Past Tense Verbs",
                "Common irregular verbs: go→went, buy→bought, think→thought, bring→brought, take→took, write→wrote.",
                [f"❌ I {wv} a phone. → ✅ I {cv} a phone.",
                 "❌ She goed to school. → ✅ She went to school.",
                 "❌ He taked my book. → ✅ He took my book."],
                lambda t, wv=wv, cv=cv: re.sub(rf'\b{wv}\b', cv, t, flags=re.IGNORECASE)
            ))
            break

    return errors


def check_stative(text):
    errors = []
    # am/is/are/was/were + V-ing where V is stative
    m = re.search(r'\b(am|is|are|was|were)\s+(\w+ing)\b', text, re.IGNORECASE)
    if m:
        ving = m.group(2).lower()
        base = ving[:-3] if ving.endswith("ing") else ving
        # handle double consonant: knowing → know, liking → like
        if base.endswith(base[-1]) and len(base) > 3:
            base_alt = base[:-1]
        else:
            base_alt = base
        if base in STATIVE_VERBS or base_alt in STATIVE_VERBS:
            actual_base = base if base in STATIVE_VERBS else base_alt
            errors.append(_err(
                "stat_01", "stative_verbs",
                f"am/is/are + {ving}",
                f"{actual_base} (simple tense)",
                f"'{actual_base.capitalize()}' is a stative verb — it describes a state, not an action. Stative verbs NEVER use the -ing (continuous) form.",
                "Stative Verbs Don't Use -ing Form",
                "Stative verbs: know, understand, believe, like, love, hate, want, need, seem, have (possession), belong, prefer, contain, own.",
                [f"❌ I am {ving}. → ✅ I {actual_base}.",
                 "❌ She is knowing the answer. → ✅ She knows the answer.",
                 "❌ They are wanting to go. → ✅ They want to go.",
                 "❌ He is liking cricket. → ✅ He likes cricket."],
            ))
    return errors


def check_articles(text):
    errors = []
    t = text

    # an + university/unique/useful (vowel letter but consonant sound)
    if re.search(r'\ban\s+(university|unique|uniform|union|unit|user|useful|usual|utmost|unanimous|euro|european|one-)', t, re.IGNORECASE):
        errors.append(_err(
            "art_01", "articles",
            "an + university/unique/useful",
            "a + university/unique/useful",
            "'University', 'unique', 'useful' start with a 'y' sound (consonant sound), so use 'a' not 'an'.",
            "Articles: A vs An Based on SOUND",
            "Use 'a' or 'an' based on SOUND: 'a university' (yoo-sound) ✅. 'an hour' (silent h) ✅.",
            ["❌ She studies in an university. → ✅ She studies in a university.",
             "❌ This is an unique idea. → ✅ This is a unique idea.",
             "❌ It is an useful tip. → ✅ It is a useful tip."],
            lambda t: re.sub(r'\ban\s+(university|unique|uniform|union|unit|user|useful|usual)\b', r'a \1', t, flags=re.IGNORECASE)
        ))

    # a + honest/hour/honour (silent H → needs 'an')
    if re.search(r'\ba\s+(honest|hour|honour|heir|honor)\b', t, re.IGNORECASE):
        errors.append(_err(
            "art_02", "articles",
            "a + honest/hour/honour",
            "an + honest/hour/honour",
            "When the 'h' is silent, the word starts with a vowel sound — use 'an'.",
            "Silent H Words Need 'An'",
            "an honest man ✅ | an hour ✅ | an honour ✅ — 'h' is silent in these.",
            ["❌ He is a honest man. → ✅ He is an honest man.",
             "❌ Wait a hour. → ✅ Wait an hour."],
            lambda t: re.sub(r'\ba\s+(honest|hour|honour|heir|honor)\b', r'an \1', t, flags=re.IGNORECASE)
        ))

    # the + sport (no article before sports)
    if re.search(r'\b(plays?|played|playing|loves?|enjoys?)\s+the\s+(cricket|football|tennis|hockey|chess|badminton|basketball|volleyball|golf|polo|kabaddi)\b', t, re.IGNORECASE):
        errors.append(_err(
            "art_03", "articles",
            "plays the cricket/football",
            "plays cricket/football (no article)",
            "No article is used before sports and games.",
            "No Article Before Sports/Games",
            "I play cricket ✅ | I play the cricket ❌. Same for chess, football, tennis.",
            ["❌ He plays the cricket. → ✅ He plays cricket.",
             "❌ She loves the tennis. → ✅ She loves tennis."],
            lambda t: re.sub(r'\bthe\s+(cricket|football|tennis|hockey|chess|badminton|basketball|volleyball|golf|kabaddi)\b', r'\1', t, flags=re.IGNORECASE)
        ))

    return errors


def check_prepositions(text):
    errors = []
    t = text

    # discuss about
    if re.search(r'\bdiscuss(ed|es|ing)?\s+about\b', t, re.IGNORECASE):
        errors.append(_err(
            "prep_01", "prepositions",
            "discuss about", "discuss (no 'about')",
            "'Discuss' is a transitive verb — it takes a direct object WITHOUT 'about'. Very common Indian English mistake.",
            "Discuss Never Takes 'About'",
            "discuss the problem ✅ | discuss about the problem ❌",
            ["❌ We discussed about the plan. → ✅ We discussed the plan.",
             "❌ Let's discuss about this. → ✅ Let's discuss this."],
            lambda t: re.sub(r'\b(discuss(?:ed|es|ing)?)\s+about\b', r'\1', t, flags=re.IGNORECASE)
        ))

    # married with
    if re.search(r'\bmarried\s+with\b', t, re.IGNORECASE):
        errors.append(_err(
            "prep_02", "prepositions",
            "married with", "married to",
            "In English, you are 'married TO' someone — not 'married with'.",
            "Married To (Not With)",
            "She is married to him ✅ | She is married with him ❌",
            ["❌ She is married with a doctor. → ✅ She is married to a doctor."],
            lambda t: re.sub(r'\bmarried\s+with\b', 'married to', t, flags=re.IGNORECASE)
        ))

    # at/in + day of week
    if re.search(r'\b(at|in)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t, re.IGNORECASE):
        errors.append(_err(
            "prep_03", "prepositions",
            "at/in + day of week", "on + day of week",
            "Use 'on' with days of the week, not 'at' or 'in'.",
            "On + Days of the Week",
            "AT specific times. ON days. IN months/years.",
            ["❌ I'll meet you at Monday. → ✅ I'll meet you on Monday.",
             "❌ The class is in Friday. → ✅ The class is on Friday."],
            lambda t: re.sub(r'\b(at|in)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', r'on \2', t, flags=re.IGNORECASE)
        ))

    # revert back / return back
    if re.search(r'\b(revert|return)\s+back\b', t, re.IGNORECASE):
        errors.append(_err(
            "prep_04", "prepositions",
            "revert back / return back", "revert / return",
            "'Revert' already means 'to go back'. Adding 'back' is redundant.",
            "Redundant: Revert Back / Return Back",
            "Revert = go back. Return = come back. Never add 'back'.",
            ["❌ I will revert back to you. → ✅ I will revert to you.",
             "❌ Please return back the book. → ✅ Please return the book."],
            lambda t: re.sub(r'\b(revert|return)\s+back\b', r'\1', t, flags=re.IGNORECASE)
        ))

    return errors


def check_indian_english(text):
    errors = []
    t = text

    if re.search(r'\bdo\s+the\s+needful\b', t, re.IGNORECASE):
        errors.append(_err(
            "ind_01", "indian_english",
            "do the needful", "take the necessary action / do what is required",
            "'Do the needful' is Indian English — not used in global/international English.",
            "Indian English: Do the Needful",
            "Replace with: 'please take the required action' / 'please do what is necessary'.",
            ["❌ Please do the needful. → ✅ Please take the necessary action."],
            lambda t: re.sub(r'\bdo\s+the\s+needful\b', 'do what is necessary', t, flags=re.IGNORECASE)
        ))

    if re.search(r'\bgave?\s+(the\s+)?(exam|test|interview)\b', t, re.IGNORECASE):
        errors.append(_err(
            "ind_02", "indian_english",
            "gave exam/test", "took the exam/test",
            "In English, a student 'takes' an exam, not 'gives' it. The examiner 'gives/sets' the exam.",
            "Indian English: Gave Exam",
            "I took the exam ✅ | I gave the exam ❌ (Indian English only)",
            ["❌ I gave the exam yesterday. → ✅ I took the exam yesterday.",
             "❌ She gave an interview. → ✅ She attended an interview."],
            lambda t: re.sub(r'\bgave?\s+(the\s+)?(exam|test)\b', r'took the \2', t, flags=re.IGNORECASE)
        ))

    if re.search(r'\bi\s+am\s+(agree|disagree)\b', t, re.IGNORECASE):
        errors.append(_err(
            "ind_03", "indian_english",
            "I am agree/disagree", "I agree/disagree",
            "'Agree' and 'disagree' are verbs, NOT adjectives. Don't use 'am/is/are' before them.",
            "Agree/Disagree Are Verbs (Not Adjectives)",
            "I agree with you ✅ | I am agree with you ❌",
            ["❌ I am agree with you. → ✅ I agree with you.",
             "❌ She is disagree. → ✅ She disagrees."],
            lambda t: re.sub(r'\bI am agree\b', 'I agree', re.sub(r'\bI am disagree\b', 'I disagree', t))
        ))

    if re.search(r'\bprepone[sd]?\b', t, re.IGNORECASE):
        errors.append(_err(
            "ind_04", "indian_english",
            "prepone/preponed", "bring forward / move to an earlier time",
            "'Prepone' is not a recognised word in standard English dictionaries. The opposite of 'postpone' is 'bring forward'.",
            "Indian English: Prepone",
            "postpone ✅ (standard). 'Prepone' ❌ → 'bring forward' / 'move up' / 'reschedule earlier'.",
            ["❌ The meeting has been preponed. → ✅ The meeting has been moved to an earlier time.",
             "❌ Can we prepone the call? → ✅ Can we bring forward the call?"],
            lambda t: re.sub(r'\bprepone[sd]?\b', 'move to an earlier time', t, flags=re.IGNORECASE)
        ))

    if re.search(r'\bpass\s*(?:ed\s*)?out\s+from\b', t, re.IGNORECASE):
        errors.append(_err(
            "ind_05", "indian_english",
            "passed out from college", "graduated from college",
            "In standard English, 'pass out' means to faint. 'Graduate from' is the correct expression for finishing college.",
            "Indian English: Passed Out from College",
            "I graduated from IIT ✅ | I passed out from IIT ❌ (pass out = faint in English!)",
            ["❌ I passed out from Delhi University. → ✅ I graduated from Delhi University."],
            lambda t: re.sub(r'\bpass(?:ed)?\s+out\s+from\b', 'graduated from', t, flags=re.IGNORECASE)
        ))

    return errors


def check_modals(text):
    errors = []

    # modal + to + verb
    m = re.search(r'\b(can|could|will|would|shall|should|may|might|must)\s+to\s+(\w+)\b', text, re.IGNORECASE)
    if m:
        modal, verb = m.group(1), m.group(2)
        errors.append(_err(
            "mod_01", "modals",
            f"{modal} to {verb}", f"{modal} {verb} (no 'to')",
            f"Modal verbs (can, could, will, would, shall, should, may, might, must) are ALWAYS followed by the base verb WITHOUT 'to'.",
            "Modal Verbs Never Take 'To'",
            "can DO ✅, should GO ✅, must FINISH ✅ | can to do ❌, should to go ❌",
            ["❌ You should to study more. → ✅ You should study more.",
             "❌ She can to speak French. → ✅ She can speak French.",
             "❌ He must to leave now. → ✅ He must leave now."],
            lambda t: re.sub(r'\b(can|could|will|would|shall|should|may|might|must)\s+to\s+(\w+)\b', r'\1 \2', t, flags=re.IGNORECASE)
        ))

    # would/should/could have + V2
    m = re.search(r'\b(would|should|could|might)\s+have\s+(went|came|did|ran|gave|took|wrote|spoke|ate|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore|made|got|bought|thought|brought|caught|found|kept|sent|told|won)\b', text, re.IGNORECASE)
    if m:
        aux, v2 = m.group(1), m.group(2).lower()
        v3 = IRREGULAR_PAST_PARTICIPLE.get(v2, v2)
        errors.append(_err(
            "mod_02", "modals",
            f"{aux} have + {v2} (V2)", f"{aux} have + {v3} (V3)",
            f"After 'would/should/could have', use the past participle (V3). '{v2}' is simple past (V2) — use '{v3}'.",
            "Perfect Modals Need Past Participle (V3)",
            "would have GONE ✅ | would have WENT ❌. should have DONE ✅ | should have DID ❌.",
            [f"❌ I would have {v2}. → ✅ I would have {v3}.",
             "❌ She should have went. → ✅ She should have gone."],
            lambda t: re.sub(
                r'\b(would|should|could|might)\s+have\s+(went|came|did|ran|gave|took|wrote|spoke|ate|made|got|bought|thought|brought|caught|found|kept|sent|told|won)\b',
                lambda x: x.group(1)+" have "+IRREGULAR_PAST_PARTICIPLE.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))

    return errors


def check_pronouns(text):
    errors = []

    # me and [anyone/anything] + verb — broader pattern
    if re.search(r'\bme\s+and\s+.{1,25}\s+(is|are|was|were|go|went|come|came|have|has|had|will|would|can|could|should|do|did|get|see|want|like|need|am|be)\b', text, re.IGNORECASE):
        errors.append(_err(
            "pro_01", "pronouns",
            "Me and [someone] + verb", "[Someone] and I + verb",
            "When the pronoun is the SUBJECT of the verb, use 'I' (not 'me'). Also always put the other person first.",
            "Subject Pronoun: I (Not Me) as Subject",
            "Test: remove the other person. Would you say 'Me went'? No — so 'I went'. Rule: '[Other person] and I'.",
            ["❌ Me and Rahul went to market. → ✅ Rahul and I went to market.",
             "❌ Me and my friend is going. → ✅ My friend and I are going.",
             "❌ Me and my sister are happy. → ✅ My sister and I are happy."],
        ))

    # between you and I (should be 'me')
    if re.search(r'\bbetween\s+\w+\s+and\s+I\b', text, re.IGNORECASE):
        errors.append(_err(
            "pro_02", "pronouns",
            "between ... and I", "between ... and me",
            "After prepositions (between, with, for, to, from), use OBJECT pronouns: me, him, her, us, them.",
            "Object Pronouns After Prepositions",
            "between us ✅ | between we ❌. with them ✅ | with they ❌.",
            ["❌ This is between you and I. → ✅ This is between you and me."],
            lambda t: re.sub(r'\bbetween\s+(\w+)\s+and\s+I\b', r'between \1 and me', t, flags=re.IGNORECASE)
        ))

    return errors


def check_word_form(text):
    errors = []
    t = text.lower()

    # Wrong irregular plurals
    wrong_plurals = {
        "childrens":"children","mans":"men","womans":"women",
        "peoples":"people","deers":"deer","sheeps":"sheep",
        "mouses":"mice","tooths":"teeth","foots":"feet",
        "gooses":"geese","knifes":"knives","leafs":"leaves",
        "wolfs":"wolves","halfs":"halves","wifes":"wives",
        "lifes":"lives","loafs":"loaves","scarfs":"scarves",
        "shelfs":"shelves","thiefs":"thieves",
    }
    for wrong, correct in wrong_plurals.items():
        if re.search(rf'\b{wrong}\b', t):
            errors.append(_err(
                "wf_01", "word_form",
                f"{wrong} (wrong plural)", f"{correct} (correct plural)",
                f"'{wrong.capitalize()}' is not a valid English word. The correct plural of this noun is irregular: '{correct}'.",
                "Irregular Plural Nouns",
                "child→children | man→men | woman→women | tooth→teeth | foot→feet | mouse→mice",
                [f"❌ The {wrong} are here. → ✅ The {correct} are here.",
                 "❌ The childrens are playing. → ✅ The children are playing."],
                lambda t, w=wrong, c=correct: re.sub(rf'\b{w}\b', c, t, flags=re.IGNORECASE)
            ))
            break

    # Uncountable noun plural (informations, advices, etc.)
    uncountable_plural = {
        "informations":"information","advices":"advice","furnitures":"furniture",
        "luggages":"luggage","equipments":"equipment","knowledges":"knowledge",
        "staffs":"staff","progresses":"progress","researchs":"research",
    }
    for wrong, correct in uncountable_plural.items():
        if re.search(rf'\b{wrong}\b', t):
            errors.append(_err(
                "wf_02", "word_form",
                f"{wrong} (no plural form)", f"{correct} (uncountable — no -s)",
                f"'{correct.capitalize()}' is an uncountable noun — it has NO plural form. Never add -s.",
                "Uncountable Nouns Have No Plural Form",
                "information ✅ informations ❌ | advice ✅ advices ❌ | furniture ✅ furnitures ❌",
                [f"❌ I have many {wrong}. → ✅ I have a lot of {correct}.",
                 "❌ She gave me many advices. → ✅ She gave me a lot of advice."],
                lambda t, w=wrong, c=correct: t.replace(w, c).replace(w.capitalize(), c.capitalize())
            ))
            break

    # very/more + absolute adjective
    if re.search(r'\b(very|more|most)\s+(unique|perfect|impossible|infinite|unanimous|complete|absolute|eternal|simultaneous)\b', t):
        errors.append(_err(
            "wf_03", "word_form",
            "very/more + unique/perfect/impossible",
            "unique/perfect/impossible (no modifier needed)",
            "Absolute adjectives already represent the maximum degree — they cannot be modified with 'very', 'more', or 'most'.",
            "Absolute Adjectives Cannot Be Modified",
            "Something is either unique or not — 'very unique' is incorrect. 'perfect' cannot be 'more perfect'.",
            ["❌ This is very unique. → ✅ This is unique.",
             "❌ She is more perfect. → ✅ She is perfect."],
            lambda t: re.sub(r'\b(very|more|most)\s+(unique|perfect|impossible)\b', r'\2', t, flags=re.IGNORECASE)
        ))

    return errors


def check_double_negative(text):
    errors = []
    if re.search(r"\b(don't|doesn't|didn't|can't|won't|wouldn't|isn't|aren't|wasn't|weren't|never|nobody|nothing|nowhere|neither)\b.{0,50}\b(nothing|nobody|nowhere|never|no\s+one|neither)\b", text, re.IGNORECASE):
        errors.append(_err(
            "dneg_01", "double_negative",
            "two negative words in one clause",
            "one negative + positive word (anything/anybody/anywhere/ever)",
            "In English, two negatives make a positive (or sound incorrect). Use only ONE negative per clause.",
            "Avoid Double Negatives",
            "don't know ANYTHING ✅ | don't know NOTHING ❌. never said ANYTHING ✅ | never said NOTHING ❌.",
            ["❌ I don't know nothing. → ✅ I don't know anything.",
             "❌ She never said nothing. → ✅ She never said anything.",
             "❌ He can't do nothing. → ✅ He can't do anything."],
            lambda t: re.sub(r"\bdon't\s+know\s+nothing\b", "don't know anything",
                        re.sub(r"\bcan't\s+do\s+nothing\b", "can't do anything",
                        re.sub(r"\bnever\s+said?\s+nothing\b", "never said anything", t, flags=re.IGNORECASE),
                        flags=re.IGNORECASE), flags=re.IGNORECASE)
        ))
    return errors


def check_comparative(text):
    errors = []

    # more + -er (double comparative)
    m = re.search(r'\bmore\s+(\w+er)\b', text, re.IGNORECASE)
    if m:
        errors.append(_err(
            "comp_01", "comparative",
            f"more {m.group(1)} (double comparative)",
            f"{m.group(1)} OR more [adjective]",
            "Never use 'more' with -er comparative adjectives. Use one or the other.",
            "No Double Comparatives",
            "taller ✅ | more tall ✅ | more taller ❌. smarter ✅ | more smart ✅ | more smarter ❌.",
            ["❌ She is more taller. → ✅ She is taller.",
             "❌ He is more smarter. → ✅ He is smarter.",
             "❌ This is more easier. → ✅ This is easier."],
            lambda t: re.sub(r'\bmore\s+(\w+er)\b', r'\1', t, flags=re.IGNORECASE)
        ))

    # most + -est (double superlative)
    m = re.search(r'\bmost\s+(\w+est)\b', text, re.IGNORECASE)
    if m:
        errors.append(_err(
            "comp_02", "comparative",
            f"most {m.group(1)} (double superlative)",
            f"the {m.group(1)}",
            "Never use 'most' with -est superlative adjectives.",
            "No Double Superlatives",
            "tallest ✅ | most tallest ❌. fastest ✅ | most fastest ❌.",
            ["❌ She is the most tallest. → ✅ She is the tallest.",
             "❌ It is the most fastest route. → ✅ It is the fastest route."],
            lambda t: re.sub(r'\bmost\s+(\w+est)\b', r'\1', t, flags=re.IGNORECASE)
        ))

    return errors


def check_passive_voice(text):
    errors = []
    # was/were/is/are + V2 (should be V3)
    m = re.search(r'\b(was|were|is|are|been)\s+(wrote|did|went|gave|took|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore|came|ran|made|got|bought|thought|brought|caught|found|kept|sent|told|saw)\b', text, re.IGNORECASE)
    if m:
        v2 = m.group(2).lower()
        v3 = IRREGULAR_PAST_PARTICIPLE.get(v2, v2)
        errors.append(_err(
            "pass_01", "passive_voice",
            f"passive + {v2} (V2)", f"passive + {v3} (V3)",
            f"In passive voice, use the PAST PARTICIPLE (V3). '{v2}' is simple past (V2) — the correct V3 is '{v3}'.",
            "Passive Voice Requires Past Participle (V3)",
            "was WRITTEN ✅ (not 'was wrote'). was TAKEN ✅ (not 'was took'). was GIVEN ✅ (not 'was gave').",
            [f"❌ It was {v2}. → ✅ It was {v3}.",
             "❌ The letter was wrote by him. → ✅ The letter was written by him."],
            lambda t: re.sub(
                r'\b(was|were|is|are|been)\s+(wrote|did|went|gave|took|drove|felt|fell|flew|grew|held|knew|led|rode|rose|sang|swam|threw|wore|came|ran|made|got|bought|thought|brought|caught|found|kept|sent|told|saw)\b',
                lambda x: x.group(1)+" "+IRREGULAR_PAST_PARTICIPLE.get(x.group(2).lower(), x.group(2)),
                t, flags=re.IGNORECASE
            )
        ))
    return errors


def check_capitalization(text):
    errors = []
    # lowercase 'i' as pronoun
    if re.search(r'(?<!\w)i(?!\w)(?!\s*\.)', text):
        errors.append(_err(
            "cap_01", "capitalization",
            "lowercase 'i' as pronoun", "capital 'I'",
            "The first-person singular pronoun 'I' is ALWAYS capitalized in English.",
            "The Pronoun 'I' Is Always Capitalized",
            "I love cricket ✅ | i love cricket ❌. Even mid-sentence 'I' must be capital.",
            ["❌ She and i went to market. → ✅ She and I went to market.",
             "❌ i think you are right. → ✅ I think you are right."],
            lambda t: re.sub(r'(?<!\w)i(?!\w)', 'I', t)
        ))
    return errors


def check_countable(text):
    errors = []
    t = text.lower()

    # much + countable noun
    countable_nouns = r'\b(books?|students?|people|cars?|trees?|boys?|girls?|men|women|children|dogs?|cats?|tables?|chairs?|ideas?|mistakes?|questions?|problems?|words?|sentences?|friends?|teachers?|schools?|colleges?|countries?|cities?|years?|days?|hours?|minutes?|pages?|chapters?|examples?|reasons?|cases?|times?|ways?|things?|points?|parts?|groups?|members?|items?|products?|phones?|laptops?|houses?|rooms?|doors?|windows?|flowers?|birds?|fish|insects?)\b'
    if re.search(r'\bmuch\s+' + countable_nouns, t):
        errors.append(_err(
            "cu_01", "countable_uncountable",
            "much + countable noun", "many + countable noun",
            "'Much' is for uncountable nouns. 'Many' is for countable nouns.",
            "Much vs Many",
            "Can you count it? → MANY. Can't count it? → MUCH. many books ✅ | much books ❌.",
            ["❌ There are much students. → ✅ There are many students.",
             "❌ She has much problems. → ✅ She has many problems.",
             "❌ How much people came? → ✅ How many people came?"],
            lambda t: re.sub(r'\bmuch\s+(' + countable_nouns[3:], r'many \1', t, flags=re.IGNORECASE)
        ))

    # many/few + uncountable noun
    uncountable_pattern = '|'.join(UNCOUNTABLE)
    if re.search(rf'\b(many|few|several)\s+({uncountable_pattern})\b', t):
        errors.append(_err(
            "cu_02", "countable_uncountable",
            "many/few + uncountable noun", "much/little/a lot of + uncountable noun",
            "'Many/few' are for countable nouns. For uncountable nouns use: much/little/a lot of/some.",
            "Few/Many Cannot Be Used with Uncountable Nouns",
            "much water ✅ | many water ❌. little information ✅ | few information ❌.",
            ["❌ I need many informations. → ✅ I need a lot of information.",
             "❌ She has few luggage. → ✅ She has little luggage."],
        ))

    return errors


# ─────────────────────────────────────────────────────────────────
#  TRACKER
# ─────────────────────────────────────────────────────────────────

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "grammar_tracker.json")

def _load_tracker(uid):
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE) as f:
                return json.load(f).get(str(uid), {})
    except Exception:
        pass
    return {}

def _save_tracker(uid, tracker):
    try:
        data = {}
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE) as f:
                data = json.load(f)
        data[str(uid)] = tracker
        with open(TRACKER_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def _record_mistakes(uid, errors):
    if not uid or not errors:
        return
    tracker = _load_tracker(uid)
    for e in errors:
        cat = e.get("category", "general")
        rid = e.get("id", cat)
        if cat not in tracker:
            tracker[cat] = {"count": 0, "rule_ids": {}, "last_seen": ""}
        tracker[cat]["count"] = tracker[cat].get("count", 0) + 1
        tracker[cat]["rule_ids"][rid] = tracker[cat]["rule_ids"].get(rid, 0) + 1
        tracker[cat]["last_seen"] = datetime.now().strftime("%Y-%m-%d")
    _save_tracker(uid, tracker)

def get_weak_topics(uid):
    tracker = _load_tracker(str(uid))
    if not tracker:
        return []
    return [
        {"category": cat, "count": d.get("count", 0), "last_seen": d.get("last_seen", "")}
        for cat, d in sorted(tracker.items(), key=lambda x: x[1].get("count", 0), reverse=True)
    ]

def get_personalized_tip(uid):
    weak = get_weak_topics(str(uid))
    if not weak:
        return "Keep practicing! Submit more sentences to get personalized feedback."
    tips = {
        "subject_verb_agreement": "You frequently mix up subject-verb agreement. Remember: he/she/it → doesn't/isn't/has. They/we/you → are/were. I → am.",
        "tense": "Tense errors are your weak spot. Key rule: NEVER use 'have/has' with 'yesterday/last year/ago'. Use Simple Past instead.",
        "articles": "Article usage needs work. Remember: 'a' + consonant SOUND, 'an' + vowel SOUND. No article before sports or languages.",
        "prepositions": "Focus on prepositions. Key: on Monday (days), at 5pm (times), in January (months), in Delhi (cities). Never 'discuss about'.",
        "stative_verbs": "Stative verb errors detected. Know/like/want/have/understand — these NEVER use -ing form.",
        "indian_english": "Watch out for Indian English: avoid 'do the needful', 'revert back', 'gave exam', 'passed out from college'.",
        "pronouns": "'Me and Rahul went' is wrong — say 'Rahul and I went'. After prepositions: use me/him/her/them (not I/he/she/they).",
        "modals": "Modal verbs (can/should/must/will) NEVER take 'to'. say 'should study' not 'should to study'.",
        "word_form": "Word form issues found. Remember: information/advice/furniture have NO plural forms. children (not childrens).",
        "double_negative": "Avoid double negatives. Use 'don't know ANYTHING' (not 'nothing'). Only one negative per clause.",
        "comparative": "Comparative errors: never say 'more taller' or 'most tallest'. Choose one: taller OR more tall — not both.",
        "passive_voice": "Passive voice needs V3 (past participle): 'was written' ✅ 'was wrote' ❌. 'was taken' ✅ 'was took' ❌.",
    }
    return tips.get(weak[0]["category"], f"Your most common mistake area is {weak[0]['category'].replace('_',' ')}. Keep practicing!")


# ─────────────────────────────────────────────────────────────────
#  PRACTICE QUESTIONS
# ─────────────────────────────────────────────────────────────────

PRACTICE_QUESTIONS = {
    "error_correction": [
        {"wrong":"She don't like vegetables.","correct":"She doesn't like vegetables.","explanation":"Use 'doesn't' with he/she/it.","category":"subject_verb_agreement"},
        {"wrong":"They is very happy today.","correct":"They are very happy today.","explanation":"they/we/you → 'are', not 'is'.","category":"subject_verb_agreement"},
        {"wrong":"He are a good student.","correct":"He is a good student.","explanation":"he/she/it → 'is', not 'are'.","category":"subject_verb_agreement"},
        {"wrong":"I have seen him yesterday.","correct":"I saw him yesterday.","explanation":"'Yesterday' is a specific past time — use Simple Past, not Present Perfect.","category":"tense"},
        {"wrong":"We discussed about the matter.","correct":"We discussed the matter.","explanation":"'Discuss' never takes 'about'.","category":"prepositions"},
        {"wrong":"She is knowing the answer.","correct":"She knows the answer.","explanation":"Stative verb 'know' doesn't use -ing form.","category":"stative_verbs"},
        {"wrong":"He is a honest person.","correct":"He is an honest person.","explanation":"'h' in 'honest' is silent, so use 'an'.","category":"articles"},
        {"wrong":"I buyed a new phone.","correct":"I bought a new phone.","explanation":"buy → bought (irregular past tense).","category":"tense"},
        {"wrong":"She will coming tomorrow.","correct":"She will come tomorrow.","explanation":"will + base verb (V1), never will + -ing.","category":"tense"},
        {"wrong":"Everyone are invited.","correct":"Everyone is invited.","explanation":"'Everyone' is grammatically singular — use 'is'.","category":"subject_verb_agreement"},
        {"wrong":"I didn't went there.","correct":"I didn't go there.","explanation":"After 'didn't', use base verb (V1).","category":"tense"},
        {"wrong":"She is married with a doctor.","correct":"She is married to a doctor.","explanation":"married TO, not married with.","category":"prepositions"},
        {"wrong":"I am agree with you.","correct":"I agree with you.","explanation":"'Agree' is a verb, not an adjective — no 'am/is/are'.","category":"indian_english"},
        {"wrong":"He gave exam yesterday.","correct":"He took the exam yesterday.","explanation":"In English, you 'take' an exam.","category":"indian_english"},
        {"wrong":"The letter was wrote by him.","correct":"The letter was written by him.","explanation":"Passive voice needs V3 (past participle).","category":"passive_voice"},
        {"wrong":"She has many informations.","correct":"She has a lot of information.","explanation":"'Information' is uncountable — no plural, no 'many'.","category":"word_form"},
        {"wrong":"I don't know nothing about it.","correct":"I don't know anything about it.","explanation":"Never use two negatives in one clause.","category":"double_negative"},
        {"wrong":"He is more taller than me.","correct":"He is taller than me.","explanation":"Never use 'more' before -er comparative adjectives.","category":"comparative"},
        {"wrong":"You should to study more.","correct":"You should study more.","explanation":"Modal verbs never take 'to'.","category":"modals"},
        {"wrong":"I am doing this job since 5 years.","correct":"I have been doing this job for 5 years.","explanation":"Ongoing actions with 'for/since' need Present Perfect Continuous.","category":"tense"},
        {"wrong":"The news are very shocking.","correct":"The news is very shocking.","explanation":"'News' is uncountable and always singular.","category":"subject_verb_agreement"},
        {"wrong":"Me and Rahul went to the market.","correct":"Rahul and I went to the market.","explanation":"Use 'I' as subject, not 'me'. Put other person first.","category":"pronouns"},
        {"wrong":"My father has went to the market.","correct":"My father has gone to the market.","explanation":"After 'has/have', use past participle (V3): went → gone.","category":"tense"},
        {"wrong":"She play cricket every day.","correct":"She plays cricket every day.","explanation":"he/she/it + verb+s in Simple Present.","category":"subject_verb_agreement"},
        {"wrong":"Please do the needful.","correct":"Please do what is necessary.","explanation":"'Do the needful' is Indian English — not used globally.","category":"indian_english"},
    ],
    "fill_blank": [
        {"sentence":"She _____ not like coffee.","answer":"does","options":["do","does","did","is"],"rule":"he/she/it + does","category":"subject_verb_agreement"},
        {"sentence":"They _____ playing cricket when I arrived.","answer":"were","options":["was","were","are","be"],"rule":"they/we/you → were (past)","category":"subject_verb_agreement"},
        {"sentence":"I _____ in this company since 2018.","answer":"have been working","options":["am working","work","have been working","worked"],"rule":"since + ongoing → Present Perfect Continuous","category":"tense"},
        {"sentence":"He is _____ honest man.","answer":"an","options":["a","an","the","no article"],"rule":"an + silent-h word","category":"articles"},
        {"sentence":"She _____ the exam last year.","answer":"took","options":["gave","given","took","takes"],"rule":"'take' an exam (not give)","category":"indian_english"},
        {"sentence":"Nobody _____ home when I called.","answer":"was","options":["were","was","are","is"],"rule":"nobody is singular → was","category":"subject_verb_agreement"},
        {"sentence":"She _____ the answer already.","answer":"knows","options":["is knowing","knows","has known","know"],"rule":"Stative verb: know (no -ing)","category":"stative_verbs"},
        {"sentence":"I will _____ you tomorrow.","answer":"meet","options":["met","meeting","to meet","meet"],"rule":"will + V1 (no 'to')","category":"modals"},
        {"sentence":"The news _____ very shocking.","answer":"is","options":["were","was","are","is"],"rule":"News is uncountable-singular","category":"subject_verb_agreement"},
        {"sentence":"I _____ him yesterday at the market.","answer":"saw","options":["have seen","see","saw","seen"],"rule":"yesterday → Simple Past","category":"tense"},
        {"sentence":"She is _____ university student.","answer":"a","options":["a","an","the","some"],"rule":"a university (yoo sound = consonant)","category":"articles"},
        {"sentence":"I met him _____ Monday.","answer":"on","options":["at","in","on","by"],"rule":"on + day of week","category":"prepositions"},
        {"sentence":"There are _____ students in the class.","answer":"many","options":["much","many","a lot","few amount of"],"rule":"many + countable noun","category":"countable_uncountable"},
        {"sentence":"My brother _____ to school every day.","answer":"goes","options":["go","goes","going","gone"],"rule":"he/she/it + verb+s","category":"subject_verb_agreement"},
        {"sentence":"She _____ here for 10 years now.","answer":"has been living","options":["is living","lives","has been living","lived"],"rule":"for + duration + ongoing → Present Perfect Continuous","category":"tense"},
    ],
    "rearrange": [
        {"words":["studying","have","I","been","hours","for","3"],"answer":"I have been studying for 3 hours.","category":"tense","rule":"Present Perfect Continuous"},
        {"words":["she","the","yesterday","market","went","to"],"answer":"She went to the market yesterday.","category":"tense","rule":"Simple Past word order"},
        {"words":["neither","Ram","nor","Shyam","is","coming"],"answer":"Neither Ram nor Shyam is coming.","category":"subject_verb_agreement","rule":"Neither...nor + singular verb"},
        {"words":["discussed","project","we","the"],"answer":"We discussed the project.","category":"prepositions","rule":"Discuss takes no 'about'"},
        {"words":["agree","not","I","do","you","with"],"answer":"I do not agree with you.","category":"indian_english","rule":"Agree is a verb, not adjective"},
        {"words":["taller","is","she","than","him"],"answer":"She is taller than him.","category":"comparative","rule":"No double comparative"},
        {"words":["should","more","you","study","harder"],"answer":"You should study harder.","category":"modals","rule":"Modal + base verb (no 'to')"},
    ],
}


# ─────────────────────────────────────────────────────────────────
#  RULE LIBRARY (for the Rule Library tab)
# ─────────────────────────────────────────────────────────────────

RULE_LIBRARY = {
    "subject_verb_agreement": [
        {"id":"sva_01","rule":"They/We/You + ARE (not is)","explanation":"With they, we, you — always use 'are'. Never 'is'.","examples":["❌ They is good. → ✅ They are good.","❌ We is ready. → ✅ We are ready."]},
        {"id":"sva_02","rule":"He/She/It + IS (not are)","explanation":"With he, she, it — always use 'is'. Never 'are'.","examples":["❌ She are happy. → ✅ She is happy.","❌ He are a doctor. → ✅ He is a doctor."]},
        {"id":"sva_03","rule":"I + AM (not is/are)","explanation":"With 'I' — always use 'am'. Never 'is' or 'are'.","examples":["❌ I is fine. → ✅ I am fine.","❌ I are ready. → ✅ I am ready."]},
        {"id":"sva_04","rule":"He/She/It + DOESN'T (not don't)","explanation":"With third-person singular, use 'doesn't', not 'don't'.","examples":["❌ She don't like tea. → ✅ She doesn't like tea.","❌ He don't know. → ✅ He doesn't know."]},
        {"id":"sva_05","rule":"He/She/It + HAS (not have)","explanation":"With he/she/it, use 'has' in present tense.","examples":["❌ She have a car. → ✅ She has a car."]},
        {"id":"sva_06","rule":"They/We/You + WERE (not was)","explanation":"Past tense: they/we/you → were. I/he/she/it → was.","examples":["❌ They was playing. → ✅ They were playing."]},
        {"id":"sva_07","rule":"Everyone/Nobody + IS/WAS (singular)","explanation":"Indefinite pronouns are grammatically singular.","examples":["❌ Everyone are ready. → ✅ Everyone is ready.","❌ Nobody were home. → ✅ Nobody was home."]},
        {"id":"sva_08","rule":"He/She/It + Verb+S in Simple Present","explanation":"In Simple Present, add -s/-es to the verb for he/she/it.","examples":["❌ She play cricket. → ✅ She plays cricket.","❌ He go to school. → ✅ He goes to school."]},
    ],
    "tense": [
        {"id":"t_01","rule":"No Present Perfect with 'yesterday/ago/last year'","explanation":"Specific past time words require Simple Past, never Present Perfect.","examples":["❌ I have seen him yesterday. → ✅ I saw him yesterday.","❌ She has gone last week. → ✅ She went last week."]},
        {"id":"t_02","rule":"have/has + V3 (not V2)","explanation":"After have/has, use past participle (V3), not simple past (V2).","examples":["❌ He has went. → ✅ He has gone.","❌ She has did it. → ✅ She has done it."]},
        {"id":"t_03","rule":"Since/For + Ongoing Action → Present Perfect Continuous","explanation":"Use have/has been + V-ing for actions that started in the past and are still continuing.","examples":["❌ I am living here since 5 years. → ✅ I have been living here for 5 years."]},
        {"id":"t_04","rule":"Will + Base Verb (V1), never Will + -ing","explanation":"After 'will', use the base form of the verb.","examples":["❌ She will coming tomorrow. → ✅ She will come tomorrow."]},
        {"id":"t_05","rule":"Didn't + Base Verb (V1), never Didn't + V2","explanation":"After 'didn't', use base form. 'did' already carries the past.","examples":["❌ I didn't went. → ✅ I didn't go.","❌ She didn't came. → ✅ She didn't come."]},
        {"id":"t_06","rule":"Irregular Past Tense Verbs","explanation":"Many common verbs have irregular past forms — they don't just add -ed.","examples":["go→went, buy→bought, think→thought, take→took, write→wrote, speak→spoke"]},
    ],
    "articles": [
        {"id":"a_01","rule":"A vs An — Based on SOUND, not Spelling","explanation":"Use 'an' before vowel SOUNDS, 'a' before consonant SOUNDS.","examples":["an hour ✅ (silent h)","a university ✅ (yoo-sound)","an honest man ✅","a useful tip ✅"]},
        {"id":"a_02","rule":"No Article Before Sports/Games","explanation":"Never use 'the' before sports: cricket, football, tennis, chess.","examples":["❌ He plays the cricket. → ✅ He plays cricket."]},
        {"id":"a_03","rule":"The + Superlatives","explanation":"Always use 'the' before superlative adjectives.","examples":["❌ She is best student. → ✅ She is the best student."]},
    ],
    "prepositions": [
        {"id":"p_01","rule":"Discuss (never 'discuss about')","explanation":"'Discuss' is transitive — takes direct object without 'about'.","examples":["❌ We discussed about the plan. → ✅ We discussed the plan."]},
        {"id":"p_02","rule":"Married TO (not with)","explanation":"You are married TO someone.","examples":["❌ She is married with a doctor. → ✅ She is married to a doctor."]},
        {"id":"p_03","rule":"On + Day of Week","explanation":"Use 'on' with days. 'at' for times. 'in' for months/years.","examples":["❌ I'll meet you at Monday. → ✅ I'll meet you on Monday."]},
        {"id":"p_04","rule":"Revert Back is Redundant","explanation":"'Revert' already means 'go back'. Never add 'back'.","examples":["❌ I will revert back to you. → ✅ I will revert to you."]},
    ],
    "stative_verbs": [
        {"id":"sv_01","rule":"Stative Verbs Never Use -ing Form","explanation":"Know, like, love, want, need, understand, believe, have (possession), seem — never use -ing.","examples":["❌ I am knowing the answer. → ✅ I know the answer.","❌ She is liking cricket. → ✅ She likes cricket.","❌ He is wanting to go. → ✅ He wants to go."]},
    ],
    "indian_english": [
        {"id":"ie_01","rule":"'Do the needful' — Not Global English","explanation":"Replace with: 'do what is necessary' / 'take the required action'.","examples":["❌ Please do the needful. → ✅ Please do what is necessary."]},
        {"id":"ie_02","rule":"'Gave exam' — Indians Say, World Says 'Took'","explanation":"A student TAKES an exam. The teacher GIVES the exam.","examples":["❌ I gave the exam. → ✅ I took the exam."]},
        {"id":"ie_03","rule":"'I am agree' — Wrong","explanation":"Agree/disagree are verbs, not adjectives. Never use 'am/is/are' before them.","examples":["❌ I am agree with you. → ✅ I agree with you."]},
        {"id":"ie_04","rule":"'Prepone' — Not a Real Word","explanation":"The opposite of postpone is 'bring forward' or 'move up', not 'prepone'.","examples":["❌ Can we prepone the meeting? → ✅ Can we bring forward the meeting?"]},
        {"id":"ie_05","rule":"'Passed out from college' — Means Fainted!","explanation":"'Pass out' in English means to faint. Use 'graduated from' instead.","examples":["❌ I passed out from Delhi University. → ✅ I graduated from Delhi University."]},
        {"id":"ie_06","rule":"'Revert back' — Redundant","explanation":"'Revert' already means go back. Drop 'back'.","examples":["❌ I will revert back to you. → ✅ I will revert to you."]},
    ],
    "modals": [
        {"id":"m_01","rule":"Modal + Base Verb (No 'To')","explanation":"Can/could/will/would/shall/should/may/might/must are followed directly by the base verb — never 'to'.","examples":["❌ You should to study. → ✅ You should study.","❌ She can to swim. → ✅ She can swim."]},
        {"id":"m_02","rule":"Would/Should/Could Have + V3","explanation":"Perfect modals need past participle (V3), not simple past (V2).","examples":["❌ I would have went. → ✅ I would have gone.","❌ She should have did it. → ✅ She should have done it."]},
    ],
    "comparative": [
        {"id":"c_01","rule":"No Double Comparatives (more + -er)","explanation":"Never use 'more' with -er adjectives. Choose one form.","examples":["❌ She is more taller. → ✅ She is taller.","❌ He is more smarter. → ✅ He is smarter."]},
        {"id":"c_02","rule":"No Double Superlatives (most + -est)","explanation":"Never use 'most' with -est adjectives.","examples":["❌ She is the most tallest. → ✅ She is the tallest."]},
    ],
    "word_form": [
        {"id":"wf_01","rule":"Irregular Plurals","explanation":"child→children, man→men, woman→women, tooth→teeth, foot→feet, mouse→mice.","examples":["❌ The childrens are here. → ✅ The children are here."]},
        {"id":"wf_02","rule":"Uncountable Nouns Have No Plural","explanation":"information, advice, furniture, luggage, equipment, knowledge — never add -s.","examples":["❌ He gave me many informations. → ✅ He gave me a lot of information."]},
    ],
    "pronouns": [
        {"id":"pr_01","rule":"'X and I' as Subject (Not 'Me and X')","explanation":"Use 'I' as subject pronoun. Put the other person first.","examples":["❌ Me and Rahul went. → ✅ Rahul and I went."]},
        {"id":"pr_02","rule":"Object Pronouns After Prepositions","explanation":"After between/with/for/to/from: use me/him/her/us/them (not I/he/she/we/they).","examples":["❌ Between you and I. → ✅ Between you and me."]},
    ],
    "passive_voice": [
        {"id":"pv_01","rule":"Passive Voice Needs V3 (Past Participle)","explanation":"was/were/is/are + past participle (V3), never simple past (V2).","examples":["❌ The letter was wrote. → ✅ The letter was written.","❌ The work was did. → ✅ The work was done."]},
    ],
    "double_negative": [
        {"id":"dn_01","rule":"Only One Negative Per Clause","explanation":"Two negatives cancel each other or sound wrong. Use one negative + positive word.","examples":["❌ I don't know nothing. → ✅ I don't know anything.","❌ She never said nothing. → ✅ She never said anything."]},
    ],
    "countable_uncountable": [
        {"id":"cu_01","rule":"Much (uncountable) vs Many (countable)","explanation":"Many books ✅ | much books ❌. Much water ✅ | many water ❌.","examples":["❌ How much people came? → ✅ How many people came?","❌ There is much students. → ✅ There are many students."]},
    ],
}


# ─────────────────────────────────────────────────────────────────
#  MAIN check() FUNCTION
# ─────────────────────────────────────────────────────────────────

def check(text: str, user_id: str = None) -> dict:
    if not text or not text.strip():
        return {"error": "No text provided"}

    original = text.strip()
    errors = []

    # Run all checkers
    checkers = [
        check_sva, check_tense, check_stative, check_articles,
        check_prepositions, check_indian_english, check_modals,
        check_pronouns, check_word_form, check_double_negative,
        check_comparative, check_passive_voice, check_capitalization,
        check_countable,
    ]
    for checker in checkers:
        try:
            errors.extend(checker(text))
        except Exception:
            continue

    # Deduplicate by id
    seen, unique = set(), []
    for e in errors:
        if e["id"] not in seen:
            seen.add(e["id"])
            unique.append(e)

    # Apply fixes to build corrected text
    corrected = original
    for e in unique:
        if e.get("fix"):
            try:
                corrected = e["fix"](corrected)
            except Exception:
                pass

    # Score
    n = len(unique)
    score = max(0, 100 - n * 15)

    # Categories affected
    cats = list(dict.fromkeys(e["category_label"] for e in unique))

    # Track & personalise
    if user_id:
        _record_mistakes(str(user_id), unique)
    personal_tip = get_personalized_tip(str(user_id)) if user_id else ""

    summary = (
        "✅ No grammar errors detected! Your English is looking great." if not unique
        else f"🔍 Found {n} grammar issue{'s' if n > 1 else ''}. Review each one carefully!"
    )

    # Strip fix lambdas before JSON serialisation
    clean_errors = [{k: v for k, v in e.items() if k != "fix"} for e in unique]

    return {
        "original": original,
        "corrected": corrected if corrected != original else None,
        "errors": clean_errors,
        "error_count": n,
        "score": score,
        "grade": _grade(score),
        "summary": summary,
        "categories_affected": cats,
        "personal_tip": personal_tip,
    }


def _grade(s):
    if s == 100: return "🏆 Perfect"
    if s >= 85:  return "⭐ Excellent"
    if s >= 70:  return "👍 Good"
    if s >= 50:  return "📚 Needs Work"
    return "💪 Keep Practicing"


def get_practice(mode="error_correction", category=None, n=5):
    import random
    pool = PRACTICE_QUESTIONS.get(mode, PRACTICE_QUESTIONS["error_correction"])
    if category:
        filtered = [q for q in pool if q.get("category") == category]
        pool = filtered if filtered else pool
    random.shuffle(pool)
    return pool[:n]


def get_rule_library(category=None):
    if category and category in RULE_LIBRARY:
        return {category: RULE_LIBRARY[category]}
    return RULE_LIBRARY
