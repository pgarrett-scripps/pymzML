from typing import Iterator
from dataclasses import dataclass

from .metadata import MzMLMetadata
from .file_interface import FileInterface
from .spec import Spectrum
from .chromatogram import Chromatogram

import xml.etree.ElementTree as ElementTree

@dataclass
class SpectrumLookup:
    file_object: FileInterface
    file_info: MzMLMetadata

    def get_by_index(self, index: int | str) -> Spectrum:
        if isinstance(index, str):
            index = int(index)
        return self.file_object.get_spectrum_by_index(index)

    def get_by_id(self, identifier: str) -> Spectrum:
        return self.file_object.get_spectrum_by_id(identifier)

    @property
    def count(self) -> int | None:
        return self.file_info.spectrum_count

    def __iter__(self) -> Iterator[Spectrum]:
        """Iterate over all spectra in the file."""
        # Get a fresh file handle for iteration
        file_handle = self.file_object.file_handler.get_file_handler(self.file_info.encoding)
        file_handle.seek(0)
        mzml_iter: Iterator[tuple[str, ElementTree.Element]] = iter(
            ElementTree.iterparse(file_handle, events=("end",))
        )
        for event, element in mzml_iter:
            if event == "end":
                # Extract tag suffix for matching
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

                if tag == "spectrum":
                    spectrum = Spectrum(element)
                    yield spectrum
                    element.clear()  # Clear element to free memory

        file_handle.close()

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
    file_info: MzMLMetadata

    def get_by_index(self, index: int | str) -> Chromatogram:
        if isinstance(index, str):
            index = int(index)
        return self.file_object.get_chromatogram_by_index(index)

    def get_by_id(self, identifier: str) -> Chromatogram:
        return self.file_object.get_chromatogram_by_id(identifier)

    @property
    def TIC(self) -> Chromatogram:
        return self.get_by_id("TIC")

    @property
    def count(self) -> int | None:
        return self.file_info.chromatogram_count

    def __iter__(self) -> Iterator[Chromatogram]:
        """Iterate over all chromatograms in the file."""
        # Get a fresh file handle for iteration
        file_handle = self.file_object.file_handler.get_file_handler(self.file_info.encoding)
        file_handle.seek(0)
        mzml_iter: Iterator[tuple[str, ElementTree.Element]] = iter(
            ElementTree.iterparse(file_handle, events=("end",))
        )

        for event, element in mzml_iter:
            if event == "end":
                # Extract tag suffix for matching
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

                if tag == "chromatogram":
                    chrom = Chromatogram(element)
                    yield chrom
                    element.clear()  # Clear element to free memory

        file_handle.close()

    
    def __getitem__(self, index: int | str) -> Chromatogram:
        """Access chromatogram by index or ID."""
        if isinstance(index, int):
            return self.get_by_index(index)
        return self.get_by_id(index)