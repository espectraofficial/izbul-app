from scrapers.kariyer import search_kariyer

jobs = search_kariyer("data analyst")

for job in jobs:
    print(job.company)
    print(job.title)
    print(job.url)
    print("------")