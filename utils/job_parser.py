import re


INTERN_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bstajyer[a-zçğıöşü]*\b",
        r"\bstaj\b",
        r"\bintern\b",
        r"\binternship\b",
        r"\btrainee\b"
    ]
]

JUNIOR_PHRASES = [
    "uzman yardımcısı",
    "uzman yardımcılığı",
    "assistant specialist",
    "entry level",
    "başlangıç seviyesi",
    "yeni mezun",
    "new graduate",
    "graduate program",
    "management trainee"
]

JUNIOR_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\bassociate\b",
        r"\basistan[a-zçğıöşü]*\b",
        r"\bassistant\b",
        r"\byardımcı[a-zçğıöşü]*\b"
    ]
]

DIRECTOR_PHRASES = [
    "director",
    "direktör",
    "head of",
    "chief",
    "vice president",
    "genel müdür",
    "executive"
]

DIRECTOR_PATTERNS = [
    re.compile(r"\bvp\b")
]

MANAGER_PHRASES = [
    "manager",
    "müdür",
    "müdür yardımcısı",
    "lead",
    "lider",
    "supervisor",
    "süpervizör",
    "yönetici",
    "team lead",
    "head"
]

SENIOR_PHRASES = [
    "senior",
    "sr.",
    "kıdemli",
    "expert",
    "principal",
    "baş uzman",
    "yetkili uzman",
    "lead specialist"
]

SPECIALIST_PHRASES = [
    "uzman",
    "specialist"
]

YEAR_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"([0-9]+)\s*[-–]\s*[0-9]+\s*yıl",
        r"([0-9]+)\s*[-–]\s*[0-9]+\s*years",
        r"([0-9]+)\+?\s*yıl",
        r"([0-9]+)\+?\s*years",
        r"minimum\s*([0-9]+)",
        r"en az\s*([0-9]+)"
    ]
]

TITLE_HYBRID_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"(?:\(|\[)\s*(?:hibrit|hybrid)\s*(?:\)|\])",
        r"\s[-|/]\s*(?:hibrit|hybrid)\s*$",
        r"^(?:hibrit|hybrid)\s*[-|/]\s*"
    ]
]

TITLE_REMOTE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"(?:\(|\[)\s*(?:remote|uzaktan|home[ -]office)\s*(?:\)|\])",
        r"\s[-|/]\s*(?:remote|uzaktan|home[ -]office)\s*$",
        r"^(?:remote|uzaktan|home[ -]office)\s*[-|/]\s*"
    ]
]

TITLE_OFFICE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"(?:\(|\[)\s*(?:ofis|office|on[ -]?site|yerinde)\s*(?:\)|\])",
        r"\s[-|/]\s*(?:ofis|office|on[ -]?site|yerinde)\s*$",
        r"^(?:ofis|office|on[ -]?site|yerinde)\s*[-|/]\s*"
    ]
]

HYBRID_CONTEXT_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bhibrit\s+(?:çalış\w*|iş\s+model\w*|model\w*|pozisyon\w*)",
        r"\b(?:çalışma|iş)\s+model\w*\s*(?::|;|-)?\s*hibrit\b",
        r"\bhybrid\s+(?:work\w*|model\w*|schedule\w*|position\w*|role\w*)",
        r"\b(?:work|working)\s+model\w*\s*(?:is|:|;|-)?\s*hybrid\b",
        r"\bhem\s+(?:ofis\w*|office)\s+hem\s+(?:uzaktan|remote|evden)\b",
        r"\bhem\s+(?:uzaktan|remote|evden)\s+hem\s+(?:ofis\w*|office)\b",
        r"\b(?:ofis\w*|office)\s*(?:ve|ile|\+|/)\s*(?:uzaktan|remote|evden)\s+çalış\w*",
        r"\b(?:uzaktan|remote|evden)\s*(?:ve|ile|\+|/)\s*(?:ofis\w*|office)\s+çalış\w*",
        r"\bhafta(?:da|nın)?\s+\d+\s+gün\s+(?:ofis\w*|iş\s*yer\w*|office).{0,60}\d+\s+gün\s+(?:evden|uzaktan|remote)",
        r"\bhafta(?:da|nın)?\s+\d+\s+gün\s+(?:evden|uzaktan|remote).{0,60}\d+\s+gün\s+(?:ofis\w*|iş\s*yer\w*|office)",
        r"\bhafta(?:da|nın)?\s+(?:bir|iki|üç|dört|beş|altı|yedi)\s+gün\s+(?:ofis\w*|iş\s*yer\w*|office).{0,60}(?:kalan\s+gün\w*|(?:bir|iki|üç|dört|beş|altı|yedi)\s+gün)\s+(?:evden|uzaktan|remote|home[ -]office)",
        r"\bhafta(?:da|nın)?\s+(?:bir|iki|üç|dört|beş|altı|yedi)\s+gün\s+(?:evden|uzaktan|remote|home[ -]office).{0,60}(?:kalan\s+gün\w*|(?:bir|iki|üç|dört|beş|altı|yedi)\s+gün)\s+(?:ofis\w*|iş\s*yer\w*|office)"
    ]
]

REMOTE_CONTEXT_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\buzaktan\s+çalış\w*",
        r"\bevden\s+çalış\w*",
        r"\b(?:tamamen|tümüyle|%?\s*100)\s+(?:uzaktan|remote)\b",
        r"\b(?:çalışma|iş)\s+model\w*\s*(?::|;|-)?\s*uzaktan\b",
        r"\bremote\s+(?:work\w*|working|position\w*|role\w*|job\w*)",
        r"\b(?:remote|uzaktan)\s+(?:çalışma\s+)?(?:imkan\w*|olana\w*|seçenek\w*)",
        r"\b(?:work|working)\s+model\w*\s*(?:is|:|;|-)?\s*remote\b",
        r"\bwork\s+from\s+home\b",
        r"\bhome[ -]office\s+(?:çalış\w*|work\w*|model\w*)?",
        r"\blokasyon(?:dan)?\s+bağımsız\s+çalış\w*"
    ]
]

OFFICE_CONTEXT_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bofis(?:ten|te|imizde|inde)?(?:\s+(?:ortamında|içi))?\s+çalış\w*",
        r"\b(?:çalışma|iş)\s+model\w*\s*(?::|;|-)?\s*(?:ofis|yerinde)\b",
        r"\b(?:tamamen|tam\s+zamanlı)\s+(?:ofis|yerinde|on[ -]?site)\b",
        r"\byerinde\s+çalış\w*",
        r"\biş\s*yer\w*\s+çalış\w*",
        r"\bon[ -]?site\s+(?:work\w*|working|position\w*|role\w*|job\w*)"
    ]
]

NEGATED_WORK_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\b(?:uzaktan|remote|hibrit|hybrid)\s+çalış\w*.{0,30}\b(?:yok|değil|(?:bulun|sunul|uygulan)(?:mamakta(?:dır)?|m[ıiuü]yor|mayacak(?:tır)?|maz))",
        r"\b(?:uzaktan|remote|hibrit|hybrid)\s+(?:model\w*|work\w*).{0,30}\b(?:yok|değil|(?:bulun|sunul|uygulan)(?:mamakta(?:dır)?|m[ıiuü]yor|mayacak(?:tır)?|maz))",
        r"\b(?:no|not)\s+(?:a\s+)?(?:remote|hybrid)(?:\s+work\w*)?\b",
        r"\b(?:remote|hybrid)\s+work\w*.{0,25}\b(?:not\s+available|isn'?t\s+available|unavailable)\b"
    ]
]


def normalize_parser_text(value):

    return " ".join(
        str(value or "")
        .lower()
        .replace("ı̇", "i")
        .split()
    )


def has_phrase(text, phrases):

    return any(
        phrase in text
        for phrase in phrases
    )


def has_pattern(text, patterns):

    return any(
        pattern.search(text)
        for pattern in patterns
    )


def classify_explicit_work_model(value):

    text = normalize_parser_text(value)

    if not text:

        return None

    text = re.sub(
        r"^(?:çalışma|iş|work|working)\s+model\w*\s*(?::|;|=|-)?\s*",
        "",
        text
    )

    if re.search(r"\b(?:hibrit|hybrid)\b", text):

        return "Hibrit"

    if re.search(r"\bhome[ -]office\b", text):

        return "Remote"

    has_remote = bool(
        re.search(r"\b(?:remote|uzaktan|evden)\b", text)
    )
    has_office = bool(
        re.search(r"\b(?:office|ofis|on[ -]?site|yerinde)\b", text)
    )

    if has_remote and has_office:

        return "Hibrit"

    if has_remote:

        return "Remote"

    if has_office:

        return "Ofis"

    return None


def mask_negated_work_phrases(text):

    for pattern in NEGATED_WORK_PATTERNS:

        text = pattern.sub(" ", text)

    return text


# =========================
# EXPERIENCE PARSER
# =========================

def parse_experience(

    title="",

    description="",

    position_level=None
):

    title_text = normalize_parser_text(title)
    description_text = normalize_parser_text(description)
    combined_text = " ".join(
        part
        for part in [
            title_text,
            description_text
        ]
        if part
    )

    # Most explicit title-level labels win over metadata and description text.
    if has_pattern(title_text, INTERN_PATTERNS):

        return "Stajyer"

    if has_phrase(title_text, DIRECTOR_PHRASES) or has_pattern(
        title_text,
        DIRECTOR_PATTERNS
    ):

        return "Director"

    if has_phrase(title_text, MANAGER_PHRASES):

        return "Manager"

    if has_phrase(title_text, SENIOR_PHRASES):

        return "Senior"

    if has_phrase(title_text, JUNIOR_PHRASES) or has_pattern(
        title_text,
        JUNIOR_PATTERNS
    ):

        return "Junior"

    if has_phrase(title_text, SPECIALIST_PHRASES):

        return "Mid-Level"

    # =========================
    # POSITION LEVEL OVERRIDE
    # =========================

    try:

        level = int(position_level)

        # Kariyer.net level mapping

        if level >= 25:
            return "Director"

        elif level >= 20:
            return "Manager"

        elif level >= 10:
            return "Senior"

        elif level >= 5:
            return "Junior"

    except (TypeError, ValueError):
        pass

    # Description-only signals are weaker, but still useful when the title is
    # generic or missing.
    if has_pattern(combined_text, INTERN_PATTERNS):

        return "Stajyer"

    # =========================
    # PRIORITY CHECK
    # =========================

    if has_phrase(combined_text, DIRECTOR_PHRASES) or has_pattern(
        combined_text,
        DIRECTOR_PATTERNS
    ):

        return "Director"

    if has_phrase(combined_text, MANAGER_PHRASES):

        return "Manager"

    if has_phrase(combined_text, SENIOR_PHRASES):

        return "Senior"

    if has_phrase(combined_text, JUNIOR_PHRASES) or has_pattern(
        combined_text,
        JUNIOR_PATTERNS
    ):

        return "Junior"

    # =========================
    # EXPERIENCE YEARS
    # =========================

    for pattern in YEAR_PATTERNS:

        match = pattern.search(combined_text)

        if match:

            years = int(
                match.group(1)
            )

            if years >= 10:

                return "Director"

            elif years >= 6:

                return "Manager"

            elif years >= 3:

                return "Senior"

            else:

                return "Junior"

    # =========================
    # AMBIGUOUS SPECIALIST TITLES
    # =========================

    if has_phrase(combined_text, SPECIALIST_PHRASES):

        return "Mid-Level"

    # =========================
    # DEFAULT
    # =========================

    return "Mid-Level"


# =========================
# REMOTE PARSER
# =========================

def parse_remote(

    work_model="",

    title="",

    description=""
):

    explicit_model = classify_explicit_work_model(
        work_model
    )

    if explicit_model:

        return explicit_model

    title_text = normalize_parser_text(title)

    if has_pattern(title_text, TITLE_HYBRID_PATTERNS):

        return "Hibrit"

    if has_pattern(title_text, TITLE_REMOTE_PATTERNS):

        return "Remote"

    if has_pattern(title_text, TITLE_OFFICE_PATTERNS):

        return "Ofis"

    description_text = mask_negated_work_phrases(
        normalize_parser_text(description)
    )

    if has_pattern(description_text, HYBRID_CONTEXT_PATTERNS):

        return "Hibrit"

    if has_pattern(description_text, REMOTE_CONTEXT_PATTERNS):

        return "Remote"

    if has_pattern(description_text, OFFICE_CONTEXT_PATTERNS):

        return "Ofis"

    return "Belirtilmemiş"
