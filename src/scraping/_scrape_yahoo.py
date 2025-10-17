from datetime import datetime, timedelta, timezone
from typing import Any

from yahoo_fin import news

from data_models import Headline


def _fetch_yahoo_news_headlines(
    tickers: list[str],
) -> list[Headline]:
    """
    Fetch Yahoo Finance headlines for a list of tickers within a time window.

    Args:
        tickers (list[str]): List of stock tickers to scrape.

    Returns:
        list[Headline]: List of recent headlines within the time window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    all_news: list[Headline] = []

    for ticker in tickers:
        articles: list[dict[str, Any]] = news.get_yf_rss(ticker)  # type: ignore
        for art in articles:  # type: ignore
            # Convert timestamp to datetime (Yahoo gives seconds since epoch)
            ts = art.get("providerPublishTime")
            if not ts:
                continue
            pub_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if pub_dt < cutoff:
                continue  # Skip older than cutoff

            all_news.append(
                Headline(
                    headline=art["title"],  # type: ignore
                    link=art["link"],  # type: ignore
                    pub_date=pub_dt.isoformat(),
                    topic=ticker,
                )
            )

    return all_news


def scrape_yahoo_headlines():
    tickers = ["AAPL", "MSFT", "TSLA", "AMZN", "^GSPC"]
    headlines = _fetch_yahoo_news_headlines(tickers)
    return headlines
