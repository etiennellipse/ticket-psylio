from playwright.sync_api import sync_playwright, Playwright
from bs4 import BeautifulSoup
import json

BASE_DOMAIN = "https://support.psylio.com"


class KnowledgeBaseScraper:
    def __init__(self, start_url: str, url_part: str, url_leaves: str, language: str):
        self._start_url = start_url
        self._url_part = url_part
        self._url_leaves = url_leaves
        self._language = language

        self._parsed_links = []
        self._articles = []

    def recursive_visit(self, page, url: str):
        page.goto(BASE_DOMAIN + url)
        #page.wait_for_selector("div[class=ModuleItem__moduleItem]")
        # This is bad, but I don't have a stable selector through all pages content
        page.wait_for_timeout(1000)

        soup = BeautifulSoup(page.content(), "html.parser")

        #if "/portal/fr/kb/articles/" in url:
        if self._url_leaves in url:
            # This is a leaf (article)! Let's extract content
            content = soup.find("div", class_="ArticleDetailLeftContainer__box")
            self._articles.append({
                "url": BASE_DOMAIN + url,
                "content": content.text,
                "html": content.prettify(),
                "title": content.find_next("h1").text,
                "language": self._language,
            })

        links_to_visit = [x for x in soup.find_all("a", href=True) if x["href"].startswith(self._url_part)]

        for a in links_to_visit:
            if a["href"] not in self._parsed_links:
                print("visiting " + a["href"])
                self._parsed_links.append(a["href"])
                self.recursive_visit(page, a["href"])

    def run(self, playwright: Playwright):
        chromium = playwright.chromium # or "firefox" or "webkit".
        browser = chromium.launch()
        page = browser.new_page()

        #page.goto("https://support.psylio.com/portal/fr/kb")
        page.goto(self._start_url)
        page.wait_for_selector("div[class=Layout__layout1]")

        # other actions
        soup = BeautifulSoup(page.content(), "html.parser")

        #links_to_visit = [x for x in soup.find_all("a", href=True) if x["href"].startswith("/portal/fr/kb/")]
        links_to_visit = [x for x in soup.find_all("a", href=True) if x["href"].startswith(self._url_part)]

        for a in links_to_visit:
            if a["href"] not in self._parsed_links:
                print("visiting " + a["href"])
                self._parsed_links.append(a["href"])
                self.recursive_visit(page, a["href"])

        browser.close()

        return self._articles


with sync_playwright() as playwright:
    scraper_fr = KnowledgeBaseScraper("https://support.psylio.com/portal/fr/kb", "/portal/fr/kb/", "/portal/fr/kb/articles/", "fr")
    articles_fr = scraper_fr.run(playwright)

    scraper_en = KnowledgeBaseScraper("https://support.psylio.com/portal/en/kb", "/portal/en/kb/", "/portal/en/kb/articles/", "en")
    articles_en = scraper_en.run(playwright)

    # Save all articles to JSON file
    with open("psylio.json", "w") as f:
        json.dump(articles_fr + articles_en, f, indent=4)
