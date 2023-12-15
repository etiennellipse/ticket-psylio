.gitignorefrom playwright.sync_api import sync_playwright, Playwright
from bs4 import BeautifulSoup
import json

BASE_DOMAIN = "https://support.psylio.com"

parsed_links = []
articles = []

def recursive_visit(page, url: str):
    page.goto(BASE_DOMAIN + url)
    #page.wait_for_selector("div[class=ModuleItem__moduleItem]")
    # This is bad, but I don't have a stable selector through all pages content
    page.wait_for_timeout(1000)

    soup = BeautifulSoup(page.content(), "html.parser")

    if "/portal/fr/kb/articles/" in url:
        # This is a leaf (article)! Let's extract content
        content = soup.find("div", class_="ArticleDetailLeftContainer__box")
        articles.append({
            "url": BASE_DOMAIN + url,
            "content": content.text,
            "html": content.prettify(),
            "title": content.find_next("h1").text,
        })

    links_to_visit = [x for x in soup.find_all("a", href=True) if x["href"].startswith("/portal/fr/kb/")]

    for a in links_to_visit:
        if a["href"] not in parsed_links:
            print("visiting " + a["href"])
            parsed_links.append(a["href"])
            recursive_visit(page, a["href"])


def run(playwright: Playwright):
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch()
    page = browser.new_page()

    page.goto("https://support.psylio.com/portal/fr/kb")
    page.wait_for_selector("div[class=Layout__layout1]")

    # other actions
    soup = BeautifulSoup(page.content(), "html.parser")

    links_to_visit = [x for x in soup.find_all("a", href=True) if x["href"].startswith("/portal/fr/kb/")]

    for a in links_to_visit:
        if a["href"] not in parsed_links:
            print("visiting " + a["href"])
            parsed_links.append(a["href"])
            recursive_visit(page, a["href"])

    browser.close()

    # Save articles to JSON file
    with open("psylio.json", "w") as f:
        json.dump(articles, f, indent=4)


with sync_playwright() as playwright:
    run(playwright)
