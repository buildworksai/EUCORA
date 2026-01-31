# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AWS S3 storage backend implementation.
"""
import time
from typing import BinaryIO, Optional

import boto3
from botocore.exceptions import ClientError

from .base import HealthCheckResult, StorageBackend, StorageObject, StorageResult

try:
    from ..models import AWSS3Config
except ImportError:
    # For type hints
    pass


class AWSS3Backend(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self, config: "AWSS3Config"):
        """
        Initialize AWS S3 backend.

        Args:
            config: AWSS3Config instance
        """
        self.config = config
        self.client = self._create_client()
        self.bucket_name = config.bucket_name

    def _create_client(self):
        """Create boto3 S3 client based on auth method."""
        if self.config.auth_method == self.config.AuthMethod.IAM_ROLE:
            # Use default credential chain (EC2/ECS/EKS instance role)
            return boto3.client("s3", region_name=self.config.region)
        elif self.config.auth_method == self.config.AuthMethod.ASSUME_ROLE:
            # Assume role via STS
            sts = boto3.client("sts")
            credentials = sts.assume_role(
                RoleArn=self.config.role_arn,
                ExternalId=self.config.external_id,
                RoleSessionName="eucora-storage",
            )["Credentials"]
            return boto3.client(
                "s3",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=self.config.region,
            )
        else:
            # Access key + secret
            return boto3.client(
                "s3",
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region,
                endpoint_url=self.config.endpoint_url if self.config.endpoint_url else None,
            )

    def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StorageResult:
        """Upload file to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = {str(k): str(v) for k, v in metadata.items()}
            if self.config.kms_key_id:
                extra_args["ServerSideEncryption"] = "aws:kms"
                extra_args["SSEKMSKeyId"] = self.config.kms_key_id

            file.seek(0)
            result = self.client.upload_fileobj(  # noqa: F841
                file,
                self.bucket_name,
                path,
                ExtraArgs=extra_args,
            )

            # Get object metadata
            head = self.client.head_object(Bucket=self.bucket_name, Key=path)
            return StorageResult(
                path=path,
                size=head.get("ContentLength", 0),
                etag=head.get("ETag", "").strip('"'),
                metadata=metadata,
            )
        except ClientError as e:
            raise Exception(f"AWS S3 upload failed: {e}") from e

    def download(self, path: str) -> bytes:
        """Download file from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=path)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {path}") from e
            raise Exception(f"AWS S3 download failed: {e}") from e

    def delete(self, path: str) -> bool:
        """Delete file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                return False
            raise Exception(f"AWS S3 delete failed: {e}") from e

    def exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                return False
            raise Exception(f"AWS S3 exists check failed: {e}") from e

    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """Generate presigned URL for S3."""
        try:
            if method == "GET":
                return self.client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": path},
                    ExpiresIn=expires_in,
                )
            elif method == "PUT":
                return self.client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": self.bucket_name, "Key": path},
                    ExpiresIn=expires_in,
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
        except ClientError as e:
            raise Exception(f"AWS S3 presigned URL failed: {e}") from e

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[StorageObject]:
        """List objects in S3."""
        try:
            objects = []
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=min(max_keys, 1000),  # S3 max is 1000 per page
            )

            for page in pages:
                for obj in page.get("Contents", []):
                    if len(objects) >= max_keys:
                        break
                    objects.append(
                        StorageObject(
                            path=obj["Key"],
                            size=obj["Size"],
                            last_modified=obj["LastModified"].isoformat() if obj.get("LastModified") else None,
                            etag=obj.get("ETag", "").strip('"'),
                        )
                    )
                if len(objects) >= max_keys:
                    break

            return objects
        except ClientError as e:
            raise Exception(f"AWS S3 list objects failed: {e}") from e

    def health_check(self) -> HealthCheckResult:
        """Check S3 health."""
        start_time = time.time()
        try:
            # Try to head bucket (lightweight operation)
            self.client.head_bucket(Bucket=self.bucket_name)
            latency_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                is_healthy=True,
                message="AWS S3 is healthy",
                latency_ms=latency_ms,
            )
        except ClientError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_code = e.response.get("Error", {}).get("Code", "")
            return HealthCheckResult(
                is_healthy=False,
                message=f"Health check failed: {error_code}",
                latency_ms=latency_ms,
                error=str(e),
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                is_healthy=False,
                message=f"Health check failed: {str(e)}",
                latency_ms=latency_ms,
                error=str(e),
            )
