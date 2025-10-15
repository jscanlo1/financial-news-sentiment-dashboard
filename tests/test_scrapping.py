# tests/test_scraping.py
from unittest.mock import MagicMock

import pytest

from data_models import Headline  # type: ignore
from scraping._scrape_google import \
    _fetch_google_news_headlines  # type: ignore
from scraping._scrape_yahoo import _fetch_yahoo_news_headlines  # type: ignore

# Realistic mock news data
mock_yahoo_news = [
    {
        "title": "Apple stock rises on strong earnings",
        "link": "https://finance.yahoo.com/news/apple-earnings-123",
        "publisher": "CNBC",
        "providerPublishTime": 1696645200,
        "summary": "Apple reported quarterly revenue higher than expected.",
        "type": "STORY",
        "uuid": "1111-aaaa-2222-bbbb",
    },
    {
        "title": "Microsoft hits new all-time high",
        "link": "https://finance.yahoo.com/news/microsoft-high-456",
        "publisher": "Reuters",
        "providerPublishTime": 1696648800,
        "summary": "Microsoft shares reach record value amid strong demand.",
        "type": "STORY",
        "uuid": "3333-cccc-4444-dddd",
    },
    {
        "title": "Tech sector struggles as market falls",
        "link": "https://finance.yahoo.com/news/tech-falls-789",
        "publisher": "Bloomberg",
        "providerPublishTime": 1696652400,
        "summary": "Major tech companies see stock prices drop.",
        "type": "STORY",
        "uuid": "5555-eeee-6666-ffff",
    },
    {
        "title": "Google announces new AI tool",
        "link": "https://finance.yahoo.com/news/google-ai-101",
        "publisher": "TechCrunch",
        "providerPublishTime": 1696656000,
        "summary": "Google releases AI tool to streamline workflows.",
        "type": "STORY",
        "uuid": "7777-gggg-8888-hhhh",
    },
]  # type: ignore

# Fake XML content
mock_rss_content = """
<rss version="2.0">
<channel>
    <title>Google News - Test Topic</title>
    <item>
        <title>Apple stock rises on strong earnings</title>
        <link>https://news.google.com/news/apple-earnings-123</link>
        <pubDate>Mon, 07 Oct 2025 12:00:00 GMT</pubDate>
    </item>
    <item>
        <title>Microsoft hits new all-time high</title>
        <link>https://news.google.com/news/microsoft-high-456</link>
        <pubDate>Mon, 07 Oct 2025 13:00:00 GMT</pubDate>
    </item>
    <item>
        <title>Tech sector struggles as market falls</title>
        <link>https://news.google.com/news/tech-falls-789</link>
        <pubDate>Mon, 07 Oct 2025 14:00:00 GMT</pubDate>
    </item>
</channel>
</rss>
"""


@pytest.fixture
def mock_requests_get(mocker):  # type: ignore
    mock_resp = MagicMock()
    mock_resp.content = mock_rss_content.encode("utf-8")
    return mocker.patch("scraping._scrape_google.requests.get", return_value=mock_resp)  # type: ignore


@pytest.fixture
def mock_yahoo_fin_news(mocker):  # type: ignore
    return mocker.patch("scraping._scrape_yahoo.news.get_yf_rss", return_value=mock_yahoo_news)  # type: ignore


class TestScraping:

    def test_yahoo_scraping(self, mock_yahoo_fin_news: list[dict[str, str | int]]):
        headlines = _fetch_yahoo_news_headlines(["AAPL"])
        assert isinstance(headlines, list)
        # assert all(isinstance(headline, Headline) for headline in headlines)
        assert len(headlines) == 4

    def test_fetch_google_news(self, mock_requests_get):
        topic = "finance"
        headlines = _fetch_google_news_headlines(topic)

        assert isinstance(headlines, list)
        assert all(isinstance(h, Headline) for h in headlines)
        assert len(headlines) == 3

        # Check first headline content
        first = headlines[0]
        assert first.headline == "Apple stock rises on strong earnings"
        assert first.link == "https://news.google.com/news/apple-earnings-123"
        assert first.pub_date == "Mon, 07 Oct 2025 12:00:00 GMT"
        assert first.topic == topic
