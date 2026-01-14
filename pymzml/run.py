"""
The class :py:class:`Reader` parses mzML files.
"""

import os
import xml.etree.ElementTree as ElementTree
from collections.abc import Iterator
from pathlib import Path
from re import Match
from typing import Any

from .chromatogram import Chromatogram
from .content import MzMLContentBuilder
from .file_interface import FileInterface
from .lookup import ChromatogramLookup, SpectrumLookup
from .regex_patterns import FILE_ENCODING_PATTERN


# Keep encoding detection methods
def _guess_encoding(mzml_file: Any) -> str:
    """Determine the encoding used for the file."""
    match: Match[bytes] | None = FILE_ENCODING_PATTERN.search(mzml_file.readline())
    return bytes.decode(match.group("encoding")) if match else "utf-8"


def _determine_file_encoding(path: str) -> str:
    """Determine the encoding used for the file in path."""
    if not os.path.exists(path):
        return "utf-8"

    if path.endswith(".gz") or path.endswith(".igz"):
        import gzip

        with gzip.open(path, "rb") as sniffer:
            return _guess_encoding(sniffer)
    else:
        with open(path, "rb") as sniffer:
            return _guess_encoding(sniffer)


class Reader:
    """Reader for mzML files."""

    def __init__(
        self,
        path_or_file: str | Path | Any,
        build_index_from_scratch: bool = False,
        extract_gzip: bool = True,
        in_memory: bool = False,
    ) -> None:
        """Initialize Reader and parse metadata."""
        # Normalize to string if Path
        self.path_or_file = str(path_or_file) if isinstance(path_or_file, Path) else path_or_file
        self.file_name = str(path_or_file)

        # Determine encoding
        self.encoding = (
            _determine_file_encoding(self.path_or_file)
            if isinstance(self.path_or_file, str)
            else _guess_encoding(self.path_or_file)
        )

        # Open file
        self.file_object: FileInterface = FileInterface(
            path=path_or_file,
            encoding=self.encoding,
            build_index_from_scratch=build_index_from_scratch,
            extract_gzip=extract_gzip,
            in_memory=in_memory,
        )

        # Parse metadata
        self.root, self.iter, builder = self._parse_metadata()

        # Extract parsed content
        self.content = builder.build()
        self.obo_version = builder.obo_version
        self.run_id = builder.run_id
        self.start_time = builder.start_time
        self.spectrum_count = builder.spectrum_count
        self.chromatogram_count = builder.chromatogram_count

    def _parse_metadata(
        self,
    ) -> tuple[ElementTree.Element, Iterator[tuple[str, ElementTree.Element]], MzMLContentBuilder]:
        """Parse metadata and return root, iterator, and builder."""
        file_handle = self.file_object.file_handler.get_file_handler(self.encoding)

        mzml_iter: Iterator[tuple[str, ElementTree.Element]] = iter(  # type: ignore
            ElementTree.iterparse(file_handle, events=("end", "start"))  # type: ignore
        )

        _, root = next(mzml_iter)

        # Build metadata
        builder = MzMLContentBuilder()
        builder.parse_from_iterator(mzml_iter)

        root.clear()
        return root, mzml_iter, builder

    @property
    def spectra(self) -> SpectrumLookup:
        """Access spectra lookup."""
        return SpectrumLookup(file_object=self.file_object)

    @property
    def chromatograms(self) -> ChromatogramLookup:
        """Access chromatograms lookup."""
        return ChromatogramLookup(file_object=self.file_object)

    @property
    def TIC(self) -> Chromatogram | None:
        """Access the Total Ion Chromatogram (TIC)."""
        try:
            return self.file_object.TIC
        except KeyError:
            return None

    def __enter__(self) -> "Reader":
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.file_object.close()
