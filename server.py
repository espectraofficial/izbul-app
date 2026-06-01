from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from urllib.parse import quote
import time

app = Flask(__name__)


@app.route("/search")
def search():
    keyword = request.args.get("q")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.kariyer.net/is-ilanlari/istanbul?ct=34,82&kw={quote(keyword)}"

        page.goto(url)
        page.wait_for_timeout(5000)

        cards = page.query_selector_all('[data-test="ad-card-title"]')

        for card in cards[:50]:
            try:
                title = card.inner_text().strip()
                parent = card.query_selector("xpath=ancestor::a")

                link = parent.get_attribute("href")

                if link and not link.startswith("http"):
                    link = "https://www.kariyer.net" + link

                company_el = parent.query_selector('[data-test="subtitle"]')
                company = company_el.inner_text().strip() if company_el else "Unknown"

                results.append({
                    "company": company,
                    "title": title,
                    "url": link
                })

            except:
                continue

        browser.close()

    return jsonify(results)


if __name__ == "__main__":
    app.run(port=5000)