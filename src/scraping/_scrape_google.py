"""
Module to hold code for scraping Google headlines.
"""

import requests
from bs4 import BeautifulSoup

from data_models import Headline


def _fetch_google_news_headlines(topic: str) -> list[Headline]:
    """
    Function to pull google headlines for a given topic.
    Takes a topic as a parameter and returns a list of `Headline` options.

    Args:
        topic (str): Topic

    Returns:
        list[Headline]: Headlines
    """
    url = f"https://news.google.com/rss/search?q={topic}+when:1h&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.content, features="xml")

    items = soup.find_all("item")
    headlines: list[Headline] = []
    for item in items:
        if item.title is None or item.link is None:
            continue
        title = item.title.text
        link = item.link.text
        pub_date = item.pubDate.text if item.pubDate else None

        headlines.append(
            Headline(headline=title, link=link, pub_date=pub_date, topic=topic)
        )

    return headlines


def scrape_google_news_headlines() -> list[Headline]:
    # Fetch a few finance-related topics
    topics = ["stock market", "nasdaq", "interest rates", "inflation"]
    all_headlines: list[Headline] = []

    for topic in topics:
        headlines = _fetch_google_news_headlines(topic)
        all_headlines.extend(headlines)

    return all_headlines
