def keyword_match(job, keyword):
    keyword = keyword.lower()

    title = job.title.lower()
    company = job.company.lower()

    return keyword in title