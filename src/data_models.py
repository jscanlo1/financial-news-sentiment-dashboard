from dataclasses import dataclass


@dataclass
class Headline:
    """
    Data class to represent headlines
    """

    headline: str
    link: str
    pub_date: str | None
    topic: str
    sentiment_label: str | None = None
    sentiment_score: float | None = None


@dataclass
class RunningAggregate:
    """Data class to represent a running aggregate"""

    date: str = ""
    last_updated: str = ""
    sum_sentiment: float = 0.0
    count: int = 0
    average: float = 0.0
