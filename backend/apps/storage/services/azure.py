# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Azure Blob Storage backend implementation.
"""
import time
from typing import BinaryIO, Optional

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from .base import HealthCheckResult, StorageBackend, StorageObject, StorageResult

try:
    from ..models import AzureBlobConfig
except ImportError:
    # For type hints
    pass


class AzureBlobBackend(StorageBackend):
    """Azure Blob Storage backend."""

    def __init__(self, config: "AzureBlobConfig"):
        """
        Initialize Azure Blob backend.

        Args:
            config: AzureBlobConfig instance
        """
        self.config = config
        self.client = self._create_client()
        self.container_name = config.container_name

    def _create_client(self) -> BlobServiceClient:
        """Create Azure Blob Service Client based on auth method."""
        account_url = f"https://{self.config.account_name}.blob.core.windows.net"

        if self.config.auth_method == self.config.AuthMethod.CONNECTION_STRING:
            return BlobServiceClient.from_connection_string(self.config.connection_string)
        elif self.config.auth_method == self.config.AuthMethod.MANAGED_IDENTITY:
            credential = DefaultAzureCredential()
            return BlobServiceClient(account_url=account_url, credential=credential)
        elif self.config.auth_method == self.config.AuthMethod.ACCOUNT_KEY:
            return BlobServiceClient(
                account_url=account_url,
                credential=self.config.account_key,
            )
        elif self.config.auth_method == self.config.AuthMethod.SAS_TOKEN:
            account_url_with_sas = f"{account_url}?{self.config.sas_token}"
            return BlobServiceClient(account_url=account_url_with_sas)
        elif self.config.auth_method == self.config.AuthMethod.SERVICE_PRINCIPAL:
            from azure.identity import ClientSecretCredential

            credential = ClientSecretCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
            )
            return BlobServiceClient(account_url=account_url, credential=credential)
        else:
            raise ValueError(f"Unsupported auth method: {self.config.auth_method}")

    def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StorageResult:
        """Upload file to Azure Blob."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=path)

            file.seek(0)
            file_data = file.read()
            file_size = len(file_data)  # noqa: F841

            blob_client.upload_blob(
                data=file_data,
                content_settings={"content_type": content_type} if content_type else None,
                metadata=metadata or {},
                overwrite=True,
            )

            properties = blob_client.get_blob_properties()
            return StorageResult(
                path=path,
                size=properties.size,
                etag=properties.etag,
                metadata=metadata,
            )
        except AzureError as e:
            raise Exception(f"Azure Blob upload failed: {e}") from e

    def download(self, path: str) -> bytes:
        """Download file from Azure Blob."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=path)
            return blob_client.download_blob().readall()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Object not found: {path}")
        except AzureError as e:
            raise Exception(f"Azure Blob download failed: {e}") from e

    def delete(self, path: str) -> bool:
        """Delete file from Azure Blob."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=path)
            blob_client.delete_blob()
            return True
        except ResourceNotFoundError:
            return False
        except AzureError as e:
            raise Exception(f"Azure Blob delete failed: {e}") from e

    def exists(self, path: str) -> bool:
        """Check if file exists in Azure Blob."""
        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=path)
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        except AzureError as e:
            raise Exception(f"Azure Blob exists check failed: {e}") from e

    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """Generate SAS URL for Azure Blob."""
        try:
            from datetime import datetime, timedelta

            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            blob_client = self.client.get_blob_client(container=self.container_name, blob=path)

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.config.account_name,
                container_name=self.container_name,
                blob_name=path,
                account_key=self.config.account_key,
                permission=BlobSasPermissions(read=True) if method == "GET" else BlobSasPermissions(write=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires_in),
            )

            return f"{blob_client.url}?{sas_token}"
        except Exception as e:
            raise Exception(f"Azure Blob SAS URL failed: {e}") from e

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[StorageObject]:
        """List objects in Azure Blob."""
        try:
            container_client = self.client.get_container_client(self.container_name)
            objects = []

            for blob in container_client.list_blobs(name_starts_with=prefix):
                if len(objects) >= max_keys:
                    break
                objects.append(
                    StorageObject(
                        path=blob.name,
                        size=blob.size,
                        last_modified=blob.last_modified.isoformat() if blob.last_modified else None,
                        etag=blob.etag,
                    )
                )

            return objects
        except AzureError as e:
            raise Exception(f"Azure Blob list objects failed: {e}") from e

    def health_check(self) -> HealthCheckResult:
        """Check Azure Blob health."""
        start_time = time.time()
        try:
            # Try to get container properties (lightweight operation)
            container_client = self.client.get_container_client(self.container_name)
            container_client.get_container_properties()
            latency_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                is_healthy=True,
                message="Azure Blob Storage is healthy",
                latency_ms=latency_ms,
            )
        except ResourceNotFoundError:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                is_healthy=False,
                message=f"Container {self.container_name} not found",
                latency_ms=latency_ms,
            )
        except AzureError as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                is_healthy=False,
                message=f"Health check failed: {str(e)}",
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
