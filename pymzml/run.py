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
from .file_interface import FileInterface
from .lookup import ChromatogramLookup, SpectrumLookup
from .regex_patterns import FILE_ENCODING_PATTERN
from .versions.parser import ParserResult, parse_mzml


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
        path_or_file: str,
    ) -> None:
        """Initialize Reader and parse metadata."""

        # if gz load with gzip
        file_path_obj = Path(path_or_file)
        if file_path_obj.suffix in {".gz", ".gz"}:
            import gzip

            # open gzip and pass to parse_mzml
            with gzip.open(file_path_obj, "rt", encoding=_determine_file_encoding(path_or_file)) as gz_file:
                self.parser_result: ParserResult = parse_mzml(gz_file)
        else:
            self.parser_result: ParserResult = parse_mzml(file_path_obj)


    @property
    def spectra(self) -> SpectrumLookup:
        """Access spectra lookup."""
        return SpectrumLookup(file_object=self.parser_result)

    @property
    def chromatograms(self) -> ChromatogramLookup:
        """Access chromatograms lookup."""
        return ChromatogramLookup(file_object=self.parser_result)

    @property
    def TIC(self) -> Chromatogram | None:
        """Access the Total Ion Chromatogram (TIC)."""
        try:
            return self.chromatograms.TIC
        except KeyError:
            return None


