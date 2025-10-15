import json
import logging
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from data_models import Headline, RunningAggregate

from ._interface import StorageInterface

logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """Save data to local CSV or JSON files."""

    def __init__(self, data_dir: str) -> None:
        data_dir_path = Path(data_dir)
        data_dir_path.mkdir(parents=True, exist_ok=True)

        self.headlines_dir = data_dir_path / "headlines"
        self.aggregates_file = data_dir_path / "daily_aggregates.json"
        self.current_aggregate_file = data_dir_path / "current_aggregate.json"

        self.headlines_dir.mkdir(parents=True, exist_ok=True)
        self.aggregates_file.touch(exist_ok=True)
        self.current_aggregate_file.touch(exist_ok=True)

    def append_headlines(self, date: str, headlines: Iterable[Headline]) -> None:
        """Append new headlines to existing records."""

        file_path = self.headlines_dir / f"{date}.json"

        existing: list[dict[str, str | int | float]] = []
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

        new_items = [asdict(h) for h in headlines]

        # Deduplicate by unique headline/link combination
        existing_keys = {(item["headline"], item["link"]) for item in existing}
        merged = existing + [
            item
            for item in new_items
            if (item["headline"], item["link"]) not in existing_keys
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)

    def load_headlines(self, date: str | None = None) -> Iterable[Headline]:
        """Load headlines for a given date or all if none provided."""
        files = (
            [self.headlines_dir / f"{date}.json"]
            if date
            else sorted(self.headlines_dir.glob("*.json"))
        )

        results: list[Headline] = []
        for file in files:
            if not file.exists():
                continue
            with open(file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    results.extend(Headline(**item) for item in data)
                except json.JSONDecodeError:
                    continue
        return results

    def save_daily_aggregate(
        self, date: str, aggregate_score: RunningAggregate
    ) -> None:
        """Save or update a daily sentiment aggregate to historical aggregate data."""
        data: dict[str, dict[str, str | int | float]] = {}
        if self.aggregates_file.exists():
            with open(self.aggregates_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[date] = asdict(aggregate_score)
        with open(self.aggregates_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_current_aggregate(self, current_score: RunningAggregate) -> None:
        """Overwrite current day's aggregate sentiment."""

        with open(self.current_aggregate_file, "w", encoding="utf-8") as f:
            json.dump(asdict(current_score), f, indent=2)

    def load_current_aggregate(self) -> RunningAggregate:
        """Load current aggregate aggregate."""
        if not self.current_aggregate_file.exists():
            return RunningAggregate()
        with open(self.current_aggregate_file, "r", encoding="utf-8") as f:
            try:
                current_aggregate = json.load(f)
                return RunningAggregate(**current_aggregate)
            except json.JSONDecodeError:
                return RunningAggregate()

    def clear_current_aggregate(self) -> None:
        """Delete the current aggregate file to start a new day."""
        if self.current_aggregate_file.exists():
            self.current_aggregate_file.unlink()
