# src/storage/factory.py
from core.env import ENV, StorageMode

from ._interface import StorageInterface
from ._local_storage import LocalStorage
from ._s3_storage import S3Storage


def get_storage(backend: StorageMode) -> StorageInterface:
    """
    Factory function to get a storage backend.

    Args:
        backend (str): "local" or "s3"
        kwargs: Additional keyword args for storage init

    Returns:
        Storage: Instance of storage backend
    """
    if backend == StorageMode.LOCAL:
        return LocalStorage(data_dir=ENV.local_data_path)
    if backend == StorageMode.S3:
        assert ENV.s3_bucket is not None
        assert ENV.aws_region is not None
        return S3Storage(bucket_name=ENV.s3_bucket, region_name=ENV.aws_region)

    raise ValueError(f"Unknown storage backend: {backend}")
