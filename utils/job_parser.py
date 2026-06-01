import re


# =========================
# EXPERIENCE PARSER
# =========================

def parse_experience(

    title="",

    description="",

    position_level=None
):

    text = f"""
    {title}
    {description}
    """.lower()

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

    # =========================
    # DIRECTOR
    # =========================

    director_keywords = [

        "director",
        "direktör",
        "head of",
        "chief",
        "vp",
        "vice president",
        "genel müdür",
        "executive"
    ]

    # =========================
    # MANAGER
    # =========================

    manager_keywords = [

        "manager",
        "müdür",
        "lead",
        "lider",
        "supervisor",
        "yönetici",
        "team lead",
        "head"
    ]

    # =========================
    # SENIOR
    # =========================

    senior_keywords = [

        "senior",
        "sr.",
        "kıdemli",
        "uzman",
        "specialist",
        "expert",
        "principal"
    ]

    # =========================
    # INTERN
    # =========================

    intern_keywords = [

        "intern",
        "internship",
        "staj",
        "stajyer",
        "trainee"
    ]

    # =========================
    # JUNIOR
    # =========================

    junior_keywords = [

        "junior",
        "jr.",
        "entry level",
        "associate",
        "assistant specialist",
        "uzman yardımcısı",
        "assistant"
    ]

    # =========================
    # PRIORITY CHECK
    # =========================

    # DIRECTOR
    for keyword in director_keywords:

        if keyword in text:

            return "Director"

    # MANAGER
    for keyword in manager_keywords:

        if keyword in text:

            return "Manager"

    # SENIOR
    for keyword in senior_keywords:

        if keyword in text:

            return "Senior"

    # INTERN
    for keyword in intern_keywords:

        if keyword in text:

            return "Stajyer"

    # JUNIOR
    for keyword in junior_keywords:

        if keyword in text:

            return "Junior"

    # =========================
    # EXPERIENCE YEARS
    # =========================

    year_patterns = [

        r"([0-9]+)\+?\s*yıl",

        r"([0-9]+)\+?\s*years",

        r"minimum\s*([0-9]+)",

        r"en az\s*([0-9]+)"
    ]

    for pattern in year_patterns:

        match = re.search(
            pattern,
            text
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