"""image context — ports."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pdf_toolkit.pdf_context.domain import ResampleFilter
from pdf_toolkit.shared_kernel import PerceptualScore


class ImageCodec(ABC):
    @abstractmethod
    def decode(self, data: bytes):
        ...

    @abstractmethod
    def resize(self, img, width: int, height: int, resample: ResampleFilter):
        ...

    @abstractmethod
    def encode(self, img, fmt: str, quality: int) -> bytes:
        ...


class QualityMeter(ABC):
    @abstractmethod
    def score(self, original: bytes, candidate: bytes) -> PerceptualScore:
        ...
