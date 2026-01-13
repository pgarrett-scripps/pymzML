from dataclasses import dataclass
from typing import Iterator

from .chromatogram import Chromatogram
from .file_interface import FileInterface
from .spectrum import Spectrum


@dataclass
class SpectrumLookup:
    file_object: FileInterface
    _count: int | None = None  # can be preset (from file info) or computed on demand

    def get_by_index(self, index: int | str) -> Spectrum:
        if isinstance(index, str):
            index = int(index)
        return self.file_object.get_spectrum_by_index(index)

    def get_by_id(self, identifier: str) -> Spectrum:
        return self.file_object.get_spectrum_by_id(identifier)

    @property
    def count(self) -> int | None:
        if self._count is not None:
            return self._count
        return self.file_object.spectrum_count

    def __iter__(self) -> Iterator[Spectrum]:
        """Iterate over all spectra in the file."""
        return self.file_object.iter_spectra()

    def __getitem__(self, index: int | str) -> Spectrum:
        """Access spectrum by index or ID."""
        if isinstance(index, int):
            return self.get_by_index(index)
        return self.get_by_id(index)

    def next(self) -> Spectrum:
        """Get next spectrum using iterator."""
        return next(iter(self))


@dataclass
class ChromatogramLookup:
    file_object: FileInterface
    _count: int | None = None

    def get_by_index(self, index: int | str) -> Chromatogram:
        if isinstance(index, str):
            index = int(index)
        return self.file_object.get_chromatogram_by_index(index)

    def get_by_id(self, identifier: str) -> Chromatogram:
        return self.file_object.get_chromatogram_by_id(identifier)

    @property
    def TIC(self) -> Chromatogram:
        return self.file_object.TIC

    @property
    def count(self) -> int | None:
        if self._count is not None:
            return self._count
        return self.file_object.chromatogram_count

    def __iter__(self) -> Iterator[Chromatogram]:
        """Iterate over all chromatograms in the file."""
        return self.file_object.iter_chromatograms()

    def __getitem__(self, index: int | str) -> Chromatogram:
        """Access chromatogram by index or ID."""
        if isinstance(index, int):
            return self.get_by_index(index)
        return self.get_by_id(index)
