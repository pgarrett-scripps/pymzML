#!/usr/bin/env python3
"""Interface for different mzML file formats."""

from io import BytesIO
from pathlib import Path
from re import Pattern

from .chromatogram import Chromatogram
from .file_classes import (
    BytesMzml,
    ElementType,
    IndexedGzip,
    MzmlXMLElement,
    StandardGzip,
    StandardMzml,
)
from .spec import Spectrum
from .utils import gzip_reader


def convert_mzml_element_to_object(
    mzml_element: MzmlXMLElement,
) -> Spectrum | Chromatogram:
    """Convert MzmlXMLElement to Spectrum or Chromatogram object."""
    if mzml_element.element_type == ElementType.SPECTRUM:
        return Spectrum(mzml_element.element)
    elif mzml_element.element_type == ElementType.CHROMATOGRAM:
        return Chromatogram(mzml_element.element)
    else:
        raise ValueError("Unknown MzmlXMLElement type.")


class FileInterface:
    """Interface to different mzML formats."""

    def __init__(
        self,
        path: str | Path | BytesIO,
        encoding: str,
        build_index_from_scratch: bool = False,
        index_regex: Pattern[bytes] | None = None,
        obo_version: str | None = None,
    ) -> None:
        """Initialize FileInterface with path and encoding options."""
        self.build_index_from_scratch: bool = build_index_from_scratch
        self.encoding: str = encoding
        self.index_regex: Pattern[bytes] | None = index_regex
        self.file_handler: StandardMzml | StandardGzip | IndexedGzip | BytesMzml = self._open(path)
        self.obo_version: str | None = obo_version

    def close(self) -> None:
        """Close the internal file handler."""
        self.file_handler.close()

    def _open(
        self, path_or_file: str | Path | BytesIO
    ) -> StandardMzml | StandardGzip | IndexedGzip | BytesMzml:
        """Open appropriate file handler based on file type and format."""
        if isinstance(path_or_file, BytesIO):
            return BytesMzml(path_or_file, self.encoding, self.build_index_from_scratch)
        if isinstance(path_or_file, Path):
            path_or_file = str(path_or_file)
        if path_or_file.endswith(".gz"):
            if self._indexed_gzip(path_or_file):
                return IndexedGzip(path_or_file, self.encoding)
            else:
                return StandardGzip(path_or_file, self.encoding)
        return StandardMzml(
            path_or_file,
            self.encoding,
            self.build_index_from_scratch,
            index_regex=self.index_regex,
        )

    def _indexed_gzip(self, path: str) -> bool:
        """Check if file is an indexed gzip file."""
        indexed = False
        indexed = gzip_reader.GzipReader(path).indexed
        return indexed

    def read(self, size: int = -1) -> bytes | str:
        """Read binary data from file handler (size=-1 reads to end)."""
        return self.file_handler.read(size)

    def get_chromatogram_by_id(self, identifier: str) -> Chromatogram:
        chromatogram = convert_mzml_element_to_object(
            self.file_handler.get_chromatogram_by_id(identifier),
        )
        if not isinstance(chromatogram, Chromatogram):
            raise ValueError("Retrieved object is not a Chromatogram")
        return chromatogram

    def get_chromatogram_by_index(self, index: int) -> Chromatogram:
        chromatogram = convert_mzml_element_to_object(
            self.file_handler.get_chromatogram_by_index(index),
        )
        if not isinstance(chromatogram, Chromatogram):
            raise ValueError("Retrieved object is not a Chromatogram")
        
        return chromatogram

    def get_spectrum_by_id(self, identifier: str) -> Spectrum:
        spectrum = convert_mzml_element_to_object(
            self.file_handler.get_spectrum_by_id(identifier),
        )
        if not isinstance(spectrum, Spectrum):
            raise ValueError("Retrieved object is not a Spectrum")
        return spectrum

    def get_spectrum_by_index(self, index: int) -> Spectrum:
        spectrum = convert_mzml_element_to_object(
            self.file_handler.get_spectrum_by_index(index),
        )
        if not isinstance(spectrum, Spectrum):
            raise ValueError("Retrieved object is not a Spectrum")
        return spectrum
