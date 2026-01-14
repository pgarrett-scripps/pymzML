from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

from .chromatogram import Chromatogram
from .file_interface import FileInterface
from .spectrum import Spectrum

T = TypeVar("T", Spectrum, Chromatogram)


@dataclass
class BaseLookup(Generic[T]):
    """Base class for spectrum and chromatogram lookups."""

    file_object: FileInterface
    _count: int | None = None

    def get_by_index(self, index: int | str) -> T:
        """Get item by index."""
        if isinstance(index, str):
            index = int(index)
        return self._get_by_index_impl(index)

    def get_by_id(self, identifier: str) -> T:
        """Get item by ID."""
        return self._get_by_id_impl(identifier)

    @property
    def count(self) -> int | None:
        """Get count of items."""
        if self._count is not None:
            return self._count
        return self._get_count_impl()

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items in the file."""
        return self._iter_impl()

    def __getitem__(self, index: int | str) -> T:
        """Access item by index or ID."""
        if isinstance(index, int):
            return self.get_by_index(index)
        return self.get_by_id(index)

    def next(self) -> T:
        """Get next item using iterator."""
        return next(iter(self))

    # Abstract methods to be implemented by subclasses
    def _get_by_index_impl(self, index: int) -> T:
        raise NotImplementedError

    def _get_by_id_impl(self, identifier: str) -> T:
        raise NotImplementedError

    def _get_count_impl(self) -> int | None:
        raise NotImplementedError

    def _iter_impl(self) -> Iterator[T]:
        raise NotImplementedError


@dataclass
class SpectrumLookup(BaseLookup[Spectrum]):
    """Lookup interface for spectra."""

    def _get_by_index_impl(self, index: int) -> Spectrum:
        return self.file_object.get_spectrum_by_index(index)

    def _get_by_id_impl(self, identifier: str) -> Spectrum:
        return self.file_object.get_spectrum_by_id(identifier)

    def _get_count_impl(self) -> int | None:
        return self.file_object.spectrum_count

    def _iter_impl(self) -> Iterator[Spectrum]:
        return self.file_object.iter_spectra()


@dataclass
class ChromatogramLookup(BaseLookup[Chromatogram]):
    """Lookup interface for chromatograms."""

    def _get_by_index_impl(self, index: int) -> Chromatogram:
        return self.file_object.get_chromatogram_by_index(index)

    def _get_by_id_impl(self, identifier: str) -> Chromatogram:
        return self.file_object.get_chromatogram_by_id(identifier)

    def _get_count_impl(self) -> int | None:
        return self.file_object.chromatogram_count

    def _iter_impl(self) -> Iterator[Chromatogram]:
        return self.file_object.iter_chromatograms()

    @property
    def TIC(self) -> Chromatogram:
        """Access Total Ion Chromatogram."""
        return self.file_object.TIC
