# tests/test_sentiment.py
from unittest.mock import MagicMock

import pytest

from data_models import Headline
from sentiment.analyzer import analyze_headlines


@pytest.fixture
def sample_headlines() -> list[Headline]:
    return [
        Headline(
            headline="Apple stock rises on strong earnings",
            link="https://...",
            pub_date="2025-10-07",
            topic="AAPL",
        ),
        Headline(
            headline="Microsoft hits new all-time high",
            link="https://...",
            pub_date="2025-10-07",
            topic="MSFT",
        ),
        Headline(
            headline="Tech sector struggles as market falls",
            link="https://...",
            pub_date="2025-10-07",
            topic="TECH",
        ),
    ]


@pytest.fixture
def mock_pipeline(monkeypatch) -> MagicMock:  # type: ignore
    """
    Replace the transformers pipeline with a mock that returns predefined sentiment results.
    """
    fake_results: list[dict[str, str | float]] = [
        {"label": "POSITIVE", "score": 0.95},
        {"label": "POSITIVE", "score": 0.90},
        {"label": "NEGATIVE", "score": 0.85},
    ]

    mock_pipe = MagicMock(return_value=fake_results)
    # Patch the pipeline used in analyzer.py
    monkeypatch.setattr("sentiment.analyzer.classifier", mock_pipe)  # type: ignore
    return mock_pipe


def test_analyze_headlines(sample_headlines: list[Headline], mock_pipeline: MagicMock):
    # Run analysis
    result = analyze_headlines(sample_headlines)

    # Check result is same length
    assert len(result) == len(sample_headlines)

    # Check each Headline has sentiment attributes
    for h in result:
        assert hasattr(h, "sentiment_label")
        assert hasattr(h, "sentiment_score")
        assert h.sentiment_label in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        assert isinstance(h.sentiment_score, float)

    # Check mock pipeline was called once
    mock_pipeline.assert_called_once()
