import json
import logging
from collections.abc import Iterable
from dataclasses import asdict

import boto3
from botocore.exceptions import ClientError

from data_models import Headline, RunningAggregate

from ._interface import StorageInterface

logger = logging.getLogger(__name__)


class S3Storage(StorageInterface):
    """Save and load data from an S3 bucket."""

    def __init__(self, bucket_name: str, prefix: str = "data") -> None:
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self.s3 = boto3.client("s3")  # type: ignore

        # Test connectivity
        try:
            self.s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            logger.error("Could not access S3 bucket '%s': %s", bucket_name, e)
            raise

    # ---------- Internal helpers ----------

    def _object_key(self, *parts: str) -> str:
        """Helper to construct a clean S3 key path."""
        return "/".join([self.prefix, *[p.strip("/") for p in parts]])

    def _get_object_json(
        self, key: str
    ) -> dict[str, str | int | float] | list[str | int | float] | None:
        try:
            resp = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(resp["Body"].read().decode("utf-8"))
        except self.s3.exceptions.NoSuchKey:
            return None
        except ClientError as e:
            if not hasattr(e.response, "Error") or not hasattr(
                e.response["Error"], "Code"
            ):
                logger.warning("Malformed error message: %e", e)
                return None

            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            logger.warning("Error fetching %s: %s", key, e)
            return None
        except json.JSONDecodeError:
            return None

    def _put_object_json(
        self, key: str, data: dict[str, str | int | float] | list[str | int | float]
    ) -> None:
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
        except ClientError as e:
            logger.error("Error writing to %s: %s", key, e)
            raise

    # ---------- Main interface ----------

    def append_headlines(self, date: str, headlines: Iterable[Headline]) -> None:
        """Append new headlines to an S3 JSON object for the given date."""
        key = self._object_key("headlines", f"{date}.json")

        existing: list[dict[str, str | int | float]] = self._get_object_json(key) or []
        new_items = [asdict(h) for h in headlines]

        # Deduplicate by headline + link
        existing_keys = {(item["headline"], item["link"]) for item in existing}
        merged = existing + [
            item
            for item in new_items
            if (item["headline"], item["link"]) not in existing_keys
        ]

        self._put_object_json(key, merged)
        logger.info("Appended %d headlines to %s", len(new_items), key)

    def load_headlines(self, date: str | None = None) -> Iterable[Headline]:
        """Load headlines for a given date or all available."""
        results: list[Headline] = []
        if date:
            key = self._object_key("headlines", f"{date}.json")
            data = self._get_object_json(key)
            if isinstance(data, list):
                results.extend(Headline(**item) for item in data)
            return results

        # If no date provided, list all objects under 'headlines/'
        prefix = self._object_key("headlines")
        resp = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            data = self._get_object_json(key)
            if isinstance(data, list):
                results.extend(Headline(**item) for item in data)
        return results

    def save_daily_aggregate(
        self, date: str, aggregate_score: RunningAggregate
    ) -> None:
        """Save or update a daily sentiment aggregate."""
        key = self._object_key("daily_aggregates.json")
        data: dict[str, float] = self._get_object_json(key) or {}
        data[date] = asdict(aggregate_score)
        self._put_object_json(key, data)
        logger.info("Saved daily aggregate for %s: %.3f", date, aggregate_score)

    def save_current_aggregate(self, current_score: RunningAggregate) -> None:
        """Overwrite the current day's live aggregate sentiment."""
        key = self._object_key("current_aggregate.json")

        self._put_object_json(key, asdict(current_score))

    def load_current_aggregate(self) -> RunningAggregate:
        """Load current day's aggregate."""
        key = self._object_key("current_aggregate.json")
        data = self._get_object_json(key)
        return RunningAggregate(**data) or RunningAggregate()

    def clear_current_aggregate(self) -> None:
        """Delete the S3 object representing current aggregate."""
        key = self._object_key("current_aggregate.json")
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        except self.s3.exceptions.NoSuchKey:
            pass
        except Exception as e:
            logger.error("Error deleting current aggregate from S3: %s", e)
