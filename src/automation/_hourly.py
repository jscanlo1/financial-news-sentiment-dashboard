"""
automation.hourly
-----------------
This module defines the hourly pipeline that:
- Fetches new financial headlines
- Performs sentiment analysis
- Updates and persists daily running aggregates to S3 (or another backend)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from core.env import ENV
from data_models import Headline
from scraping import scrape_headlines
from sentiment.analyzer import analyze_headlines
from storage import get_storage

from ._helpers import update_running_aggregate


def run_hourly_pipeline() -> None:
    """
    Runs every hour via cron or AWS EventBridge:
    1. Scrapes new headlines from Yahoo + Google
    2. Runs sentiment analysis
    3. Updates running daily aggregates in storage

    Args:
        tickers (List[str]): List of ticker symbols to analyze.
    """

    storage = get_storage(ENV.storage_mode)  # returns your S3 or local storage backend
    today = datetime.now(timezone.utc).date().isoformat()

    all_headlines: List[Headline] = []

    # 1️⃣ Scrape both Yahoo and Google
    # for ticker in tickers:
    #    yahoo_news = _fetch_yahoo_news_headlines([ticker])
    #    google_news = _fetch_google_news_headlines(ticker)
    #    all_headlines.extend(yahoo_news + google_news)

    all_headlines = scrape_headlines()

    if not all_headlines:
        print(f"[{datetime.now(timezone.utc)}] No new headlines found.")
        return

    # 2️⃣ Analyze sentiment
    analyzed_headlines = analyze_headlines(all_headlines)

    # 3️⃣ Persist raw headlines
    storage.append_headlines(today, analyzed_headlines)

    # 4️⃣ Update and persist running aggregate
    current_aggregate = storage.load_current_aggregate()

    if current_aggregate.date != today:
        storage.save_daily_aggregate(
            date=current_aggregate.date, aggregate_score=current_aggregate
        )
        storage.clear_current_aggregate()

    updated_aggregate = update_running_aggregate(current_aggregate, analyzed_headlines)
    storage.save_current_aggregate(updated_aggregate)

    print(
        f"[{datetime.now(timezone.utc)}] Processed {len(analyzed_headlines)} headlines."
    )
