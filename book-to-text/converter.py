from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from pdf2image import convert_from_bytes

from logger import get_logger


class Image:
    def __init__(self, name: str, data: np.ndarray) -> None:
        self.name = name
        self.data = data

    def get_data(self) -> np.ndarray:
        return self.data

    def get_name(self) -> str:
        return self.name


class PDF:
    def __init__(self, name: str, data: bytes) -> None:
        self._name = name
        self._data = data

    def get_data(self) -> bytes:
        return self._data

    def get_name(self) -> str:
        return self._name


class Converter(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def convert(
        self,
        input: PDF,
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> List[Image]:
        """Convert PDF to images.

        Args:
            input: PDF file
            start_page: Start from this page (0-indexed)
            end_page: Stop at this page (0-indexed), None for all pages

        Returns:
            List of Image objects
        """
        pass


class PyvipsConverter(Converter):
    def __init__(self, dpi: int = 300) -> None:
        super().__init__()
        self._logger = get_logger(self.__class__.__name__)
        self._dpi = dpi

    def convert(
        self,
        input: PDF,
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> List[Image]:
        self._logger.info(f"Converting {input.get_name()} to images at {self._dpi} DPI")
        images = []

        # Convert page numbers to 1-indexed for pdf2image
        first_page = start_page + 1
        last_page = end_page + 1 if end_page is not None else None

        pil_images = convert_from_bytes(
            input.get_data(),
            dpi=self._dpi,
            first_page=first_page,
            last_page=last_page,
        )

        for i, pil_img in enumerate(pil_images):
            img_array = np.array(pil_img)
            actual_page = start_page + i
            img_name = f"{input.get_name()}_page_{actual_page}"
            images.append(Image(img_name, img_array))
            self._logger.info(f"Converted page {actual_page} to image")

        self._logger.info(
            f"Converted {input.get_name()} to {len(images)} images")
        return images
