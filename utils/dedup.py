import unicodedata


def normalize_text(value):

    text = str(value or "").strip().lower()

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )


def deduplicate_jobs(jobs):

    unique = []

    seen = set()

    for job in jobs:

        try:

            key = (
                normalize_text(
                    getattr(
                        job,
                        "title",
                        ""
                    )
                ),
                normalize_text(
                    getattr(
                        job,
                        "company",
                        ""
                    )
                ),
                normalize_text(
                    getattr(
                        job,
                        "location",
                        ""
                    )
                )
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(job)

        except:
            continue

    return unique
