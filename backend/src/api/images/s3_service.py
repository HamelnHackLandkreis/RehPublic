import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from src.api.config import (
    S3_ENDPOINT_URL,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET_NAME,
    S3_REGION_NAME,
)

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        # Only initialize if S3 config is present/valid, but for now assuming it is
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION_NAME,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = S3_BUCKET_NAME

        try:
            self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"Could not verify/create S3 bucket on startup: {e}")

    def _ensure_bucket_exists(self):
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            # Error Code can be an int (404) or a string ("404" or "NoSuchBucket")
            error_code = e.response.get("Error", {}).get("Code")

            # Convert to string for consistent comparison
            error_code_str = str(error_code)

            if error_code_str == "404" or error_code_str == "NoSuchBucket":
                try:
                    # Some S3-compatible servers (and AWS) require a LocationConstraint
                    # when creating a bucket outside of us-east-1. For us-east-1 the
                    # CreateBucketConfiguration must be omitted.
                    if S3_REGION_NAME and S3_REGION_NAME != "us-east-1":
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={"LocationConstraint": S3_REGION_NAME},
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except Exception as create_e:
                    logger.error(
                        f"Failed to create bucket {self.bucket_name}: {create_e}"
                    )
            else:
                logger.error(f"Error checking bucket {self.bucket_name}: {e}")

    def upload_file(
        self, file_bytes: bytes, object_name: str, content_type: str | None = None
    ) -> bool:
        """Upload a file to an S3 bucket"""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.put_object(
                Body=file_bytes, Bucket=self.bucket_name, Key=object_name, **extra_args
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {object_name} to S3: {e}")
            return False

    def get_file(self, object_name: str) -> bytes:
        """Download a file from an S3 bucket"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_name
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to download {object_name} from S3: {e}")
            raise

    def generate_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL to share an S3 object"""
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            return ""

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from an S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {object_name} from S3: {e}")
            return False
