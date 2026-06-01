class Job:
    def __init__(
        self,
        site,
        company,
        title,
        description,
        url,
        apply_url,
        posted_date="",
        job_date_text="",
        remote="Belirtilmemiş",
        experience="Belirtilmemiş",
        location="Belirtilmemiş",
        logo_url=""
    ):
        self.site = site
        self.company = company
        self.title = title
        self.description = description
        self.posted_date = posted_date
        self.job_date_text = job_date_text
        self.url = url
        self.apply_url = apply_url
        self.remote = remote
        self.experience = experience
        self.location = location
        self.logo_url = logo_url
