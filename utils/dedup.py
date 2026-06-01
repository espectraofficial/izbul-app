def deduplicate_jobs(jobs):

    unique = []

    seen = set()

    for job in jobs:

        try:

            # 🔥 SADECE TITLE + COMPANY
            # 🔥 LINK KULLANMA
            key = (
                job.title.strip().lower(),
                job.company.strip().lower()
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(job)

        except:
            continue

    return unique