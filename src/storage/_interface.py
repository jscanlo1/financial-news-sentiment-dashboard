# src/storage/storage.py
from abc import ABC, abstractmethod
from collections.abc import Iterable

from data_models import Headline, RunningAggregate


class StorageInterface(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def append_headlines(self, date: str, headlines: Iterable[Headline]) -> None:
        """Append new headlines to existing records."""

    @abstractmethod
    def load_headlines(self, date: str | None = None) -> Iterable[Headline]:
        """Load headlines for a given date or all if none provided."""

    @abstractmethod
    def save_daily_aggregate(
        self, date: str, aggregate_score: RunningAggregate
    ) -> None:
        """Save or update a daily sentiment aggregate."""

    @abstractmethod
    def save_current_aggregate(self, current_score: RunningAggregate) -> None:
        """Overwrite current day's aggregate sentiment."""

    @abstractmethod
    def load_current_aggregate(self) -> RunningAggregate:
        """Load current aggregate aggregate."""

    @abstractmethod
    def clear_current_aggregate(self) -> None:
        """Delete the file representing current aggregate."""
