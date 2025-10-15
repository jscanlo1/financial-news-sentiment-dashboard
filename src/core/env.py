from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class StorageMode(StrEnum):
    LOCAL = auto()
    S3 = auto()


@dataclass(frozen=True)
class EnvConfig:
    """Strongly-typed environment configuration for the app."""

    storage_mode: StorageMode
    aws_region: Optional[str]
    s3_bucket: Optional[str]
    local_data_path: str

    @staticmethod
    def load() -> EnvConfig:
        """Load environment variables and ensure paths exist."""
        raw_mode = os.getenv("STORAGE_MODE", StorageMode.LOCAL.value).lower()
        storage_mode = StorageMode(raw_mode)

        # Project root (two levels up from this file)
        project_root = Path(__file__).resolve().parent.parent
        default_data_path = project_root / "data"

        # Use env override or fallback
        local_data_path = Path(
            os.getenv("LOCAL_DATA_PATH", str(default_data_path))
        ).resolve()

        # 🔒 Ensure the directory exists
        if storage_mode == StorageMode.LOCAL:
            local_data_path.mkdir(parents=True, exist_ok=True)

        aws_region = os.getenv("AWS_REGION")
        s3_bucket = os.getenv("S3_BUCKET")

        if storage_mode == StorageMode.S3 and not s3_bucket:
            raise EnvironmentError("S3_BUCKET is required when STORAGE_MODE=s3")

        return EnvConfig(
            storage_mode=storage_mode,
            aws_region=aws_region,
            s3_bucket=s3_bucket,
            local_data_path=str(local_data_path),
        )


# Global singleton config
ENV = EnvConfig.load()
