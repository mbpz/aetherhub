import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional


class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, local_path: str, remote_key: str) -> str:
        pass

    @abstractmethod
    async def download_file(self, remote_key: str, local_path: str) -> None:
        pass

    @abstractmethod
    async def delete_file(self, remote_key: str) -> None:
        pass

    @abstractmethod
    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        pass


class LocalStorage(StorageService):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _resolve(self, remote_key: str) -> str:
        return os.path.join(self.base_dir, remote_key)

    async def upload_file(self, local_path: str, remote_key: str) -> str:
        dest = self._resolve(remote_key)
        await asyncio.to_thread(os.makedirs, os.path.dirname(dest), exist_ok=True)
        await asyncio.to_thread(shutil.copy2, local_path, dest)
        return dest

    async def download_file(self, remote_key: str, local_path: str) -> None:
        src = self._resolve(remote_key)
        await asyncio.to_thread(os.makedirs, os.path.dirname(local_path), exist_ok=True)
        await asyncio.to_thread(shutil.copy2, src, local_path)

    async def delete_file(self, remote_key: str) -> None:
        path = self._resolve(remote_key)
        if os.path.exists(path):
            await asyncio.to_thread(os.remove, path)

    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        return self._resolve(remote_key)


class S3Storage(StorageService):
    def __init__(self, bucket: str, region: str = "us-east-1",
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None):
        if not bucket:
            raise ValueError("AETHERHUB_S3_BUCKET must be set when using S3 backend")
        self.bucket = bucket
        import boto3
        self._client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_file(self, local_path: str, remote_key: str) -> str:
        await asyncio.to_thread(
            self._client.upload_file, local_path, self.bucket, remote_key
        )
        return f"s3://{self.bucket}/{remote_key}"

    async def download_file(self, remote_key: str, local_path: str) -> None:
        await asyncio.to_thread(os.makedirs, os.path.dirname(local_path), exist_ok=True)
        await asyncio.to_thread(
            self._client.download_file, self.bucket, remote_key, local_path
        )

    async def delete_file(self, remote_key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object, Bucket=self.bucket, Key=remote_key
        )

    def get_url(self, remote_key: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": remote_key},
            ExpiresIn=expires,
        )


def get_storage() -> StorageService:
    backend = os.getenv("AETHERHUB_STORAGE_BACKEND", "local")
    if backend == "s3":
        return S3Storage(
            bucket=os.getenv("AETHERHUB_S3_BUCKET", ""),
            region=os.getenv("AWS_REGION", "us-east-1"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    return LocalStorage(base_dir=os.getenv("AETHERHUB_UPLOAD_DIR", "uploads"))


# TODO: Integrate into web/backend/routes/skills.py
# from .services.storage import get_storage
# storage = get_storage()