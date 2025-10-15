"""
automation.helpers
------------------
Utility functions for computing and updating sentiment aggregates.
"""

from __future__ import annotations

import datetime
from typing import List

from data_models import Headline, RunningAggregate


def update_running_aggregate(
    current_day_data: RunningAggregate, headlines: List[Headline]
) -> RunningAggregate:
    """
    Update running daily aggregate from a new batch of analyzed headlines.

    Args:
        current_day_data (Dict[str, Any]): Current day’s aggregate state loaded from storage.
        headlines (List[Headline]): New analyzed headlines to incorporate.

    Returns:
        Dict[str, Any]: Updated aggregate ready to be saved back to storage.
    """
    if not current_day_data.date:
        current_day_data.date = datetime.date.today().isoformat()

    for h in headlines:
        if h.sentiment_score is None or h.sentiment_label is None:
            continue

        # Sentiment labels can be Positive, Negative, or Neutral
        if h.sentiment_label == "Negative":
            current_day_data.sum_sentiment += -1 * h.sentiment_score
        if h.sentiment_label == "Positive":
            current_day_data.sum_sentiment += 1 * h.sentiment_score

        current_day_data.count += 1
        current_day_data.average = (
            current_day_data.sum_sentiment / current_day_data.count
        )

    current_day_data.last_updated = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()
    return current_day_data
