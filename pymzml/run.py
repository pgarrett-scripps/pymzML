"""
The class :py:class:`Reader` parses mzML files.
"""

import os
import xml.etree.ElementTree as ElementTree
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from re import Match
from typing import Any

from .chromatogram import Chromatogram
from .constants import MzMLElement, XMLNamespace
from .file_interface import FileInterface
from .lookup import ChromatogramLookup, SpectrumLookup
from .metadata import MzMLMetadata
from .regex_patterns import FILE_ENCODING_PATTERN, MZML_VERSION_PATTERN


class Reader:
    """
    Initialize Reader object for a given mzML file.
    """

    def __init__(
        self,
        path_or_file: str | Path | Any,
        build_index_from_scratch: bool = False,
        extract_gzip: bool = True,
        in_memory: bool = False,
    ) -> None:
        """Initialize and set required attributes."""
        self.build_index_from_scratch: bool = build_index_from_scratch

        # Normalize path_or_file and set encoding
        match path_or_file:
            case Path():
                self.path_or_file: str | Any = str(path_or_file)
                file_name = self.path_or_file
                encoding = self._determine_file_encoding(self.path_or_file)
            case str():
                self.path_or_file = path_or_file
                file_name = path_or_file
                encoding = self._determine_file_encoding(path_or_file)
            case _:
                self.path_or_file = path_or_file
                file_name = str(path_or_file)
                encoding = self._guess_encoding(path_or_file)  # type: ignore[arg-type]

        self.file_object: FileInterface = self._open_file(
            self.path_or_file,
            build_index_from_scratch=self.build_index_from_scratch,
            encoding=encoding,
            extract_gzip=extract_gzip,
            in_memory=in_memory,
        )

        # File info
        self.info: MzMLMetadata = MzMLMetadata(
            file_name=file_name,
            encoding=encoding,
            file_object=self.file_object,
        )

        self.iter: Iterator[tuple[str, ElementTree.Element]] = self._init_iter()
        self.root: ElementTree.Element
        self._iteration_count: int = 0  # Track how many items we've yielded

    @property
    def spectra(self) -> SpectrumLookup:
        """Access spectra lookup."""
        return SpectrumLookup(file_object=self.info.file_object)

    @property
    def chromatograms(self) -> ChromatogramLookup:
        """Access chromatograms lookup."""
        return ChromatogramLookup(file_object=self.info.file_object)

    def __enter__(self) -> "Reader":
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    @property
    def file_class(self) -> type:
        file = self.info.file_object
        if hasattr(file, "file_handler"):
            return type(file.file_handler)  # type: ignore
        raise AttributeError("The file object does not have a 'file_handler' attribute.")

    def _open_file(
        self,
        path_or_file: str | Path | Any,
        build_index_from_scratch: bool = False,
        encoding: str = "utf-8",
        extract_gzip: bool = True,
        in_memory: bool = False,
    ) -> FileInterface:
        """
        Open the path using the FileInterface class as a wrapper.
        """
        # Type assertion: path_or_file should be str or BytesIO at this point
        if not isinstance(path_or_file, (str, Path, BytesIO)):
            raise TypeError(f"Expected str or BytesIO, got {type(path_or_file)}")

        return FileInterface(
            path=path_or_file,
            encoding=encoding,
            build_index_from_scratch=build_index_from_scratch,
            extract_gzip=extract_gzip,
            in_memory=in_memory,
        )

    def _guess_encoding(self, mzml_file: Any) -> str:
        """
        Determine the encoding used for the file.
        """
        match: Match[bytes] | None = FILE_ENCODING_PATTERN.search(mzml_file.readline())
        if match:
            return bytes.decode(match.group("encoding"))
        else:
            return "utf-8"

    def _determine_file_encoding(self, path: str) -> str:
        """
        Determine the encoding used for the file in path.
        """
        if not os.path.exists(path):
            return "utf-8"

        match path:
            case _ if path.endswith(".gz") or path.endswith(".igz"):
                import gzip

                with gzip.open(path, "rb") as sniffer:
                    return self._guess_encoding(sniffer)
            case _:
                with open(path, "rb") as sniffer:
                    return self._guess_encoding(sniffer)

    def _init_iter(self) -> Iterator[tuple[str, ElementTree.Element]]:
        """
        Initialize the iterator for the spectra and sets it to the start
        of the spectrumList element.
        """
        # Pass the FileInterface's underlying file handler directly
        # Use get_file_handler from the interface to ensure we have a valid text stream
        file_handle = self.info.file_object.file_handler.get_file_handler(self.info.encoding)

        # We need to make sure we close this handle later or it might leak if not fully consumed
        # For now, relying on Python's GC for this temporary handle used for metadata parsing

        mzml_iter: Iterator[tuple[str, ElementTree.Element]] = iter(
            ElementTree.iterparse(file_handle, events=("end", "start"))  # type: ignore[arg-type]
        )  # NOTE: end might be sufficient
        _, self.root = next(mzml_iter)
        self.info.chromatogram_count = None
        self.info.spectrum_count = None
        while True:
            _, element = next(mzml_iter, ("END", "END"))

            if isinstance(element, str):
                break

            # Extract tag suffix for matching
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            match tag:
                case MzMLElement.MZML:
                    if "version" in element.attrib and element.attrib["version"]:
                        self.info.mzml_version = element.attrib["version"]
                    else:
                        schema_location = element.attrib.get(XMLNamespace.SCHEMA_LOCATION, "")
                        if match_result := MZML_VERSION_PATTERN.search(schema_location):
                            self.info.mzml_version = match_result.group()

                case MzMLElement.CV:
                    if element.attrib.get("id") == "MS":
                        try:
                            obo_version = element.attrib["version"]  # type: ignore[call-arg]
                            self.info.obo_version = obo_version
                        except KeyError:
                            pass

                case MzMLElement.FILE_DESCRIPTION:
                    self.info.file_description_element = element

                case MzMLElement.SAMPLE_LIST:
                    self.info.sample_list_element = element

                case MzMLElement.REFERENCEABLE_PARAM_GROUP_LIST:
                    self.info.referenceable_param_group_list_element = element

                case MzMLElement.SOFTWARE_LIST:
                    self.info.software_list_element = element

                case MzMLElement.INSTRUMENT_CONFIG_LIST:
                    self.info.instrument_configuration_list_element = element

                case MzMLElement.DATA_PROCESSING_LIST:
                    self.info.data_processing_list_element = element

                case MzMLElement.CV_PARAM:
                    # if self.term_is_a_member(element.attrib.get("accession"), "MS:1000494"):
                    #    self.info.instrument_name = element.attrib.get("name")
                    pass

                case MzMLElement.SPECTRUM_LIST:
                    spec_cnt: str | None = element.attrib.get("count")
                    self.info.spectrum_count = int(spec_cnt) if spec_cnt else None
                    break

                case MzMLElement.CHROMATOGRAM_LIST:
                    chrom_cnt: str | None = element.attrib.get("count")
                    if chrom_cnt:
                        self.info.chromatogram_count = int(chrom_cnt)
                    break

                case MzMLElement.RUN:
                    self.info.run_element = element
                    self.info.run_id = element.attrib.get("id")
                    self.info.start_time = element.attrib.get("startTimeStamp")

                case _:
                    pass

        self.root.clear()
        return mzml_iter

    @property
    def TIC(self) -> Chromatogram | None:
        """Access the Total Ion Chromatogram (TIC)."""
        try:
            return self.file_object.TIC
        except KeyError:
            return None

    def close(self) -> None:
        self.info.file_object.close()


if __name__ == "__main__":
    print(__doc__)
