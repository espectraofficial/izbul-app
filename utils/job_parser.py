import re


# =========================
# EXPERIENCE PARSER
# =========================

def parse_experience(

    title="",

    description="",

    position_level=None
):

    def normalize(value):

        return " ".join(
            str(value or "")
            .lower()
            .replace("ı̇", "i")
            .split()
        )

    title_text = normalize(title)
    description_text = normalize(description)
    combined_text = " ".join(
        part
        for part in [
            title_text,
            description_text
        ]
        if part
    )

    def has_phrase(text, phrases):

        return any(
            phrase in text
            for phrase in phrases
        )

    def has_pattern(text, patterns):

        return any(
            re.search(
                pattern,
                text
            )
            for pattern in patterns
        )

    # Title signals are intentionally checked before marketplace metadata.
    # Some sources report internships and assistants as generic entry levels.
    intern_patterns = [

        r"\bstajyer[a-zçğıöşü]*\b",
        r"\bstaj\b",
        r"\bintern\b",
        r"\binternship\b",
        r"\btrainee\b"
    ]

    junior_phrases = [

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

    junior_patterns = [

        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\bassociate\b",
        r"\basistan[a-zçğıöşü]*\b",
        r"\bassistant\b",
        r"\byardımcı[a-zçğıöşü]*\b"
    ]

    director_phrases = [

        "director",
        "direktör",
        "head of",
        "chief",
        "vice president",
        "genel müdür",
        "executive"
    ]

    manager_phrases = [

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

    senior_phrases = [

        "senior",
        "sr.",
        "kıdemli",
        "expert",
        "principal",
        "baş uzman",
        "yetkili uzman",
        "lead specialist"
    ]

    specialist_phrases = [

        "uzman",
        "specialist"
    ]

    # Most explicit title-level labels win over metadata and description text.
    if has_pattern(title_text, intern_patterns):

        return "Stajyer"

    if has_phrase(title_text, director_phrases) or has_pattern(
        title_text,
        [r"\bvp\b"]
    ):

        return "Director"

    if has_phrase(title_text, manager_phrases):

        return "Manager"

    if has_phrase(title_text, senior_phrases):

        return "Senior"

    if has_phrase(title_text, junior_phrases) or has_pattern(
        title_text,
        junior_patterns
    ):

        return "Junior"

    if has_phrase(title_text, specialist_phrases):

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

    except:
        pass

    # Description-only signals are weaker, but still useful when the title is
    # generic or missing.
    if has_pattern(combined_text, intern_patterns):

        return "Stajyer"

    # =========================
    # PRIORITY CHECK
    # =========================

    if has_phrase(combined_text, director_phrases) or has_pattern(
        combined_text,
        [r"\bvp\b"]
    ):

        return "Director"

    if has_phrase(combined_text, manager_phrases):

        return "Manager"

    if has_phrase(combined_text, senior_phrases):

        return "Senior"

    if has_phrase(combined_text, junior_phrases) or has_pattern(
        combined_text,
        junior_patterns
    ):

        return "Junior"

    # =========================
    # EXPERIENCE YEARS
    # =========================

    year_patterns = [

        r"([0-9]+)\s*[-–]\s*[0-9]+\s*yıl",
        r"([0-9]+)\s*[-–]\s*[0-9]+\s*years",
        r"([0-9]+)\+?\s*yıl",
        r"([0-9]+)\+?\s*years",
        r"minimum\s*([0-9]+)",
        r"en az\s*([0-9]+)"
    ]

    for pattern in year_patterns:

        match = re.search(
            pattern,
            combined_text
        )

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

    if has_phrase(
        combined_text,
        [
            "uzman",
            "specialist"
        ]
    ):

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
    # HYBRID
    # =========================

    hybrid_keywords = [

        "hybrid",
        "hibrit",
        "remote + office",
        "office + remote",
        "mixed"
    ]

    # =========================
    # REMOTE
    # =========================

    remote_keywords = [

        "remote",
        "uzaktan",
        "work from home",
        "home office",
        "fully remote",
        "evden çalışma"
    ]

    # =========================
    # OFFICE
    # =========================

    office_keywords = [

        "office",
        "onsite",
        "on-site",
        "ofis",
        "yerinde"
    ]

    # =========================
    # PRIORITY
    # =========================

    # HYBRID FIRST
    for keyword in hybrid_keywords:

        if keyword in text:

            return "Hibrit"

    # REMOTE
    for keyword in remote_keywords:

        if keyword in text:

            return "Remote"

    # OFFICE
    for keyword in office_keywords:

        if keyword in text:

            return "Ofis"

    # =========================
    # DEFAULT
    # =========================

    return "Belirtilmemiş"
