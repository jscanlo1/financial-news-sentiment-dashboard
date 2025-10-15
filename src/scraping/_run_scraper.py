from data_models import Headline

from ._scrape_google import scrape_google_news_headlines
from ._scrape_yahoo import scrape_yahoo_headlines


def scrape_headlines() -> list[Headline]:
    """_summary_

    Returns:
        list[Headline]: _description_
    """

    google_headlines = scrape_google_news_headlines()
    yahoo_headlines = scrape_yahoo_headlines()
    return google_headlines + yahoo_headlines


if __name__ == "__main__":
    scrape_headlines()
