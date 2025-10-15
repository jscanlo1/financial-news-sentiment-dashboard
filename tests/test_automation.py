from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from data_models import Headline


@pytest.fixture
def sample_headlines() -> List[Headline]:
    return [
        Headline(
            headline="Apple rises on strong earnings",
            link="https://...",
            pub_date="2025-10-08T10:00:00Z",
            topic="AAPL",
            sentiment_label="POSITIVE",
            sentiment_score=0.91,
        ),
        Headline(
            headline="Tech sector struggles as market dips",
            link="https://...",
            pub_date="2025-10-08T11:00:00Z",
            topic="TECH",
            sentiment_label="NEGATIVE",
            sentiment_score=0.42,
        ),
    ]


@pytest.fixture
def mock_storage(mocker) -> MagicMock:  # type: ignore
    """Mock storage backend with expected methods."""
    storage = MagicMock()
    storage.load_current_day.return_value = {
        "date": "2025-10-08",
        "tickers": {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    mocker.patch("automation.hourly.get_storage", return_value=storage)
    return storage


@pytest.fixture
def mock_scrapers(mocker, sample_headlines: List[Headline]) -> None:  # type: ignore
    """Mock both Yahoo and Google scraping functions."""
    mocker.patch(
        "automation.hourly._fetch_yahoo_news_headlines", return_value=sample_headlines
    )
    mocker.patch(
        "automation.hourly._fetch_google_news_headlines", return_value=sample_headlines
    )


@pytest.fixture
def mock_analyzer(
    mocker, sample_headlines: List[Headline]  # type: ignore
) -> MagicMock:
    """Mock sentiment analyzer."""
    mock_analyze = mocker.patch(
        "automation.hourly.analyze_headlines", return_value=sample_headlines
    )
    return mock_analyze


def test_run_hourly_pipeline(
    mock_storage: MagicMock,
    mock_scrapers: None,
    mock_analyzer: MagicMock,
    sample_headlines: List[Headline],
) -> None:
    """Test that the hourly pipeline runs end-to-end with mocks."""
    from automation._hourly import run_hourly_pipeline

    run_hourly_pipeline(["AAPL", "MSFT"])

    # Scrapers called for each ticker
    mock_analyzer.assert_called_once_with(sample_headlines * 2)
    assert mock_storage.append_headlines.called
    assert mock_storage.load_current_day.called
    assert mock_storage.save_current_day.called

    # Ensure updated aggregate contains expected tickers
    args, _ = mock_storage.save_current_day.call_args
    saved_data: Dict[str, Any] = args[0]
    assert "tickers" in saved_data
    assert "AAPL" in saved_data["tickers"] or "TECH" in saved_data["tickers"]
    assert "last_updated" in saved_data


def test_update_running_aggregate(
    monkeypatch: pytest.MonkeyPatch, sample_headlines: List[Headline]
) -> None:
    """Unit test for helper that computes aggregates correctly."""
    from automation._helpers import update_running_aggregate

    current_day_data: Dict[str, Any] = {
        "date": "2025-10-08",
        "tickers": {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    updated = update_running_aggregate(current_day_data, sample_headlines)

    aapl = updated["tickers"].get("AAPL")
    tech = updated["tickers"].get("TECH")

    assert aapl is not None
    assert tech is not None
    assert isinstance(aapl["average"], float)
    assert aapl["sum_sentiment"] > 0.0
    assert tech["count"] == 1
