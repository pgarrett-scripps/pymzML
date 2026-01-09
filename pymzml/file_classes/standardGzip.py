import codecs
import gzip
from typing import TextIO
from xml.etree.ElementTree import iterparse

from .. import regex_patterns
from .xml_tuple import ElementType, MzmlXMLElement


class StandardGzip:
    def __init__(self, path: str, encoding: str) -> None:
        self.path: str = path
        self.file_handler = codecs.getreader(encoding)(gzip.open(path))  # noqa: SIM115
        self.spectrum_offsets: dict[str, int] = {}
        self.chromatogram_offsets: dict[str, int] = {}
        self._spectrum_keys: list[str] = []
        self._chromatogram_keys: list[str] = []
        self._build_index()

    def close(self) -> None:
        self.file_handler.close()

    def get_file_handler(self, encoding: str) -> TextIO:
        """Return a fresh decompressed text file handler."""
        return codecs.getreader(encoding)(gzip.open(self.path))  # noqa: SIM115

    def _build_index(self) -> None:
        """No index available for standard gzip files (random access not supported)."""
        pass

    def read(self, size: int = -1) -> str:
        """Read data from file. Default (-1) reads entire file."""
        return self.file_handler.read(size)

    def get_spectrum_by_id(self, identifier: str | int) -> MzmlXMLElement:
        """Retrieve spectrum by native ID.

        Args:
            identifier: Spectrum ID (string) or integer.

        Raises:
            KeyError: If ID is not found.
        """
        if isinstance(identifier, int):
            identifier = str(identifier)

        # Can't seek in gzip, so need fresh handle
        fh = self.get_file_handler("utf-8")
        mzml_iter = iterparse(fh, events=["end"])

        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}spectrum"):
                elem_id = element.get("id")
                if elem_id:
                    # Direct string match
                    if elem_id == identifier:
                        fh.close()
                        return MzmlXMLElement(element=element, element_type=ElementType.SPECTRUM)
                    # Try numeric ID extraction (pattern works on strings)
                    match = regex_patterns.SPECTRUM_ID_PATTERN.search(elem_id)
                    if match and match.group(1) == identifier:
                        fh.close()
                        return MzmlXMLElement(element=element, element_type=ElementType.SPECTRUM)

        fh.close()
        raise KeyError(f"Spectrum ID {identifier} not found in file")

    def get_spectrum_by_index(self, index: int) -> MzmlXMLElement:
        """Retrieve spectrum by 0-based index.

        Args:
            index: 0-based index in spectrum list.

        Raises:
            IndexError: If index is out of range.
        """
        # Can't seek in gzip, so need fresh handle
        fh = self.get_file_handler("utf-8")
        mzml_iter = iterparse(fh, events=["end"])

        current_index = 0

        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}spectrum"):
                if current_index == index:
                    fh.close()
                    return MzmlXMLElement(element=element, element_type=ElementType.SPECTRUM)
                current_index += 1

        fh.close()
        raise IndexError(f"Spectrum index {index} out of range [0, {current_index})")

    def get_chromatogram_by_id(self, identifier: str | int) -> MzmlXMLElement:
        """Retrieve chromatogram by native ID.

        Args:
            identifier: Chromatogram ID (string) or integer.

        Raises:
            KeyError: If ID is not found.
        """
        if isinstance(identifier, int):
            identifier = str(identifier)

        # Can't seek in gzip, so need fresh handle
        fh = self.get_file_handler("utf-8")
        mzml_iter = iterparse(fh, events=["end"])

        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}chromatogram"):
                elem_id = element.get("id")
                if elem_id and elem_id == identifier:
                    fh.close()
                    return MzmlXMLElement(element=element, element_type=ElementType.CHROMATOGRAM)

        fh.close()
        raise KeyError(f"Chromatogram ID {identifier} not found in file")

    def get_chromatogram_by_index(self, index: int) -> MzmlXMLElement:
        """Retrieve chromatogram by 0-based index.

        Args:
            index: 0-based index in chromatogram list.

        Raises:
            IndexError: If index is out of range.
        """
        # Can't seek in gzip, so need fresh handle
        fh = self.get_file_handler("utf-8")
        mzml_iter = iterparse(fh, events=["end"])

        current_index = 0

        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}chromatogram"):
                if current_index == index:
                    fh.close()
                    return MzmlXMLElement(element=element, element_type=ElementType.CHROMATOGRAM)
                current_index += 1

        fh.close()
        raise IndexError(f"Chromatogram index {index} out of range [0, {current_index})")


    @property
    def TIC(self) -> MzmlXMLElement:
        """Retrieve the Total Ion Chromatogram (TIC)."""
        return self.get_chromatogram_by_id("TIC")