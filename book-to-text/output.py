from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from fs import FileInput, FileSystem

import yaml
from logger import get_logger


class Page:
    def __init__(self, number: int, header: str, content: List[str], footer: str) -> None:
        self.number = number
        self.header = header
        self.content = content
        self.footer = footer

    @classmethod
    def from_dict(cls, data: Dict) -> "Page":
        return cls(
            number=data["number"],
            header=data["header"],
            content=data["content"],
            footer=data["footer"],
        )

    def to_dict(self) -> Dict:
        return {
            "number": self.number,
            "header": self.header,
            "content": self.content,
            "footer": self.footer,
        }


class Output(ABC):
    def __init__(self, fs: FileSystem) -> None:
        self.fs = fs
        super().__init__()

    @abstractmethod
    def add(self, page: Page) -> None:
        pass


class LogOutput(Output):
    def __init__(self) -> None:
        pass

    def add(self, page: Page) -> None:
        print(f"Page {page.number}: {page.header} {page.content} {page.footer}")

    def save(self, fs: FileSystem, name: str) -> None:
        pass


class YAMLOutput(Output):
    def __init__(self, fs: FileSystem) -> None:
        super().__init__(fs)
        self._logger = get_logger(__name__)

    def add(self, page: Page) -> None:
        str_data = yaml.dump(page.to_dict())
        self.fs.put(FileInput(f"yaml/{page.number}.yaml", str_data.encode()))
