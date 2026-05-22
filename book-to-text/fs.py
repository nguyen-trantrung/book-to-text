from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Optional

import boto3


class OutputType(Enum):
    YAML = "yaml"
    SQLITE = "sqlite"


class FileInput:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self.data = data


class FileSystem(ABC):
    def __init__(self, base: str) -> None:
        self.base = base
        super().__init__()

    @abstractmethod
    def put(self, input: FileInput) -> None:
        pass

    @abstractmethod
    def ls(self, prefix: Optional[str] = None) -> List[str]:
        pass

    @abstractmethod
    def remove(self, name: str) -> None:
        pass

    @abstractmethod
    def read(self, name: str) -> bytes:
        pass


class LocalFileSystem(FileSystem):
    def __init__(self, base: str) -> None:
        super().__init__(base)
        self._base_path = Path(base)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def put(self, input: FileInput) -> None:
        file_path = self._base_path / input.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(input.data)

    def ls(self, prefix: Optional[str] = None) -> List[str]:
        if not self._base_path.exists():
            return []
        if prefix is None:
            return [str(p.relative_to(self._base_path)) for p in self._base_path.rglob("*") if p.is_file()]
        return [str(p.relative_to(self._base_path)) for p in self._base_path.rglob("*") if p.is_file() and str(p.relative_to(self._base_path)).startswith(prefix)]

    def remove(self, name: str) -> None:
        file_path = self._base_path / name
        if file_path.exists():
            file_path.unlink()

    def read(self, name: str) -> bytes:
        file_path = self._base_path / name
        if not file_path.exists():
            raise FileNotFoundError(f"File {name} not found")
        with open(file_path, "rb") as f:
            return f.read()


class ObjectStorageFileSystem(FileSystem):
    def __init__(self,
                 base: str,
                 api_key: str,
                 api_secret: str,
                 region: str,
                 endpoint: str) -> None:

        base = base.rstrip("/").split("/")
        self._bucket = base[0]
        self._prefix = "/".join(base[1:])
        self._client = boto3.client(
            "s3",
            aws_access_key_id=api_key,
            aws_secret_access_key=api_secret,
            region_name=region,
            endpoint_url=endpoint,
        )
        super().__init__(base)

    def put(self, input: FileInput) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=f"{self._prefix}/{input.name}",
            Body=input.data,
            ContentType="application/octet-stream",
        )

    def ls(self, prefix: Optional[str] = None) -> List[str]:
        if prefix is None:
            response = self._client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=self._prefix,
            )
            return [obj["Key"] for obj in response["Contents"]]
        response = self._client.list_objects_v2(
            Bucket=self._bucket,
            Prefix=f"{self._prefix}/{prefix}",
        )
        return [obj["Key"] for obj in response["Contents"]]

    def remove(self, name: str) -> None:
        self._client.delete_object(
            Bucket=self._bucket,
            Key=f"{self._prefix}/{name}",
        )

    def read(self, name: str) -> bytes:
        response = self._client.get_object(
            Bucket=self._bucket,
            Key=f"{self._prefix}/{name}",
        )
        return response["Body"].read()
