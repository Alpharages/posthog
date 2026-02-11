import contextlib
from typing import Optional
from urllib.parse import urlparse

from django.conf import settings

import s3fs
import boto3
import botocore
import botocore.exceptions


def get_s3_client():
    # Defaults for localhost dev and test suites
    if settings.USE_LOCAL_SETUP:
        return s3fs.S3FileSystem(
            key=settings.DATAWAREHOUSE_LOCAL_ACCESS_KEY,
            secret=settings.DATAWAREHOUSE_LOCAL_ACCESS_SECRET,
            endpoint_url=settings.OBJECT_STORAGE_ENDPOINT,
            # skip_instance_cache ensures a fresh S3FileSystem instance is created each time,
            # avoiding "Event loop is closed" errors when the event loop changes between async
            # operations (e.g., between test modules with module-scoped event loops).
            skip_instance_cache=True,
        )

    return s3fs.S3FileSystem()


@contextlib.asynccontextmanager
async def aget_s3_client():
    # Defaults for localhost dev and test suites
    if settings.USE_LOCAL_SETUP:
        s3 = s3fs.S3FileSystem(
            key=settings.DATAWAREHOUSE_LOCAL_ACCESS_KEY,
            secret=settings.DATAWAREHOUSE_LOCAL_ACCESS_SECRET,
            endpoint_url=settings.OBJECT_STORAGE_ENDPOINT,
            skip_instance_cache=True,
            asynchronous=True,
        )
    else:
        s3 = s3fs.S3FileSystem(asynchronous=True)

    await s3.set_session()

    yield s3


def get_size_of_folder(path: str) -> float:
    s3 = get_s3_client()

    files = s3.find(path, detail=True)
    file_values = files.values() if isinstance(files, dict) else files

    total_bytes = sum(f["Size"] for f in file_values if f["type"] != "directory")
    total_mib = total_bytes / (1024 * 1024)

    return total_mib


def ensure_bucket_exists(s3_url: str, s3_key: str, s3_secret: str, s3_endpoint: Optional[str] = None) -> None:
    import structlog
    logger = structlog.get_logger(__name__)
    
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
        endpoint_url=s3_endpoint,
        region_name="us-east-1",  # Required for MinIO
    )

    parsed = urlparse(s3_url)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URL: {s3_url}")

    bucket_name = parsed.netloc

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.debug(f"Bucket {bucket_name} already exists")
    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error")
        if not error:
            logger.error(f"Failed to check bucket {bucket_name}, no error details", exc_info=e)
            raise

        error_code = error.get("Code")
        if not error_code:
            logger.error(f"Failed to check bucket {bucket_name}, no error code", exc_info=e)
            raise

        # Error code can be "404", 404, or "NoSuchBucket"
        if error_code == "404" or error_code == 404 or error_code == "NoSuchBucket":
            logger.info(f"Bucket {bucket_name} does not exist, creating it...")
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Successfully created bucket {bucket_name}")
            except Exception as create_error:
                logger.error(f"Failed to create bucket {bucket_name}", exc_info=create_error)
                raise
        else:
            logger.error(f"Failed to check bucket {bucket_name} with error code {error_code}", exc_info=e)
            raise

