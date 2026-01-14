from scipy.special.tests.test_data import data
from .versions.parser import MzMLVersion, ParserResult
from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar, Any, cast

from .chromatogram import Chromatogram
from .file_interface import FileInterface
from .spectrum import Spectrum
import .versions.dclasses as ver

T = TypeVar("T", Spectrum, Chromatogram)


@dataclass
class BaseLookup(Generic[T]):
    """Base class for spectrum and chromatogram lookups."""

    res: ParserResult

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
class Spectrum2:
    """Wrapper for Spectrum object."""

    id: str
    binary_arrays: dict[str, Any]

@dataclass
class SpectrumLookup(BaseLookup[Spectrum]):
    """Lookup interface for spectra."""

    def _get_by_index_impl(self, index: int) -> Spectrum:


        match self.res.version:
            case MzMLVersion.V1_1_0:
                mzml_obj: ver.V1_1_0_MzMl = cast(ver.V1_1_0_MzMl, self.res.mzml_object)
                if mzml_obj.run == None:
                    raise IndexError("No run information available.")
                if mzml_obj.run.spectrum_list is None:
                    raise IndexError("No spectra list available.")
                spectrum_list = mzml_obj.run.spectrum_list
                spec = spectrum_list.spectrum[index]
                return Spectrum(spec)
            case _:
                raise NotImplementedError(f"Spectrum lookup not implemented for version {self.res.version}")
                

        if self.res.run == None:
            raise IndexError("No run information available.")
        if self.res.run.spectrum_list == None:
            raise IndexError("No spectra list available.")
        spectrum_type = self.res.spectrum_list[index]


    def _get_by_id_impl(self, identifier: str) -> Spectrum:
        if self.res.run == None:
            raise IndexError("No run information available.")
        if self.res.run.spectrum_list == None:
            raise IndexError("No spectra list available.")
        # use index if possible

    def _get_count_impl(self) -> int | None:
        if self.res.run == None:
            raise IndexError("No run information available.")
        if self.res.run.spectrum_list == None:
            raise IndexError("No spectra list available.")
        return self.res.spectrum_list.count

    def _iter_impl(self) -> Iterator[Spectrum]:
        if self.res.run == None:
            raise IndexError("No run information available.")
        if self.res.run.spectrum_list == None:
            raise IndexError("No spectra list available.")
        for spec in self.res.run.spectrum_list:
            pass


@dataclass
class ChromatogramLookup(BaseLookup[Chromatogram]):
    """Lookup interface for chromatograms."""

    def _get_by_index_impl(self, index: int) -> Chromatogram:
        return self.res.get_chromatogram_by_index(index)

    def _get_by_id_impl(self, identifier: str) -> Chromatogram:
        return self.res.get_chromatogram_by_id(identifier)

    def _get_count_impl(self) -> int | None:
        return self.res.chromatogram_count

    def _iter_impl(self) -> Iterator[Chromatogram]:
        return self.res.iter_chromatograms()

    @property
    def TIC(self) -> Chromatogram:
        """Access Total Ion Chromatogram."""
        return self.res.TIC
