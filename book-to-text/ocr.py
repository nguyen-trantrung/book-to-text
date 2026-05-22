from abc import ABC, abstractmethod
from typing import List
import numpy as np

from output import Page


class Image:
    def __init__(self, name: str, data: np.ndarray) -> None:
        self.name = name
        self.data = data

    def get_name(self) -> str:
        return self.name

    def get_data(self) -> np.ndarray:
        return self.data


class OCR(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def ocr(self, image: Image) -> Page:
        pass


class PaddleVietOCR(OCR):
    def __init__(self) -> None:
        super().__init__()

    def ocr(self, image: Image) -> Page:
        return Page(number=0, header="", content=[], footer="")


class PaddleVLM(OCR):
    def __init__(self) -> None:
        super().__init__()

    def ocr(self, image: Image) -> Page:
        return Page(number=0, header="", content=[], footer="")
