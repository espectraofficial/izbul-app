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

HYBRID_KEYWORDS = [
    "hybrid",
    "hibrit",
    "remote + office",
    "office + remote",
    "mixed"
]

REMOTE_KEYWORDS = [
    "remote",
    "uzaktan",
    "work from home",
    "home office",
    "fully remote",
    "evden çalışma"
]

OFFICE_KEYWORDS = [
    "office",
    "onsite",
    "on-site",
    "ofis",
    "yerinde"
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

    text = f"""
    {work_model}
    {title}
    {description}
    """.lower()

    # =========================
    # PRIORITY
    # =========================

    # HYBRID FIRST
    for keyword in HYBRID_KEYWORDS:

        if keyword in text:

            return "Hibrit"

    # REMOTE
    for keyword in REMOTE_KEYWORDS:

        if keyword in text:

            return "Remote"

    # OFFICE
    for keyword in OFFICE_KEYWORDS:

        if keyword in text:

            return "Ofis"

    # =========================
    # DEFAULT
    # =========================

    return "Belirtilmemiş"
