"""
The class :py:class:`Reader` parses mzML files.
"""

import contextlib
import os
import re
import xml.etree.ElementTree as ElementTree
from collections.abc import Iterator
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from re import Match, Pattern
from typing import Any

from . import chromatogram, obo, regex_patterns, spec
from .constants import MzMLElement, XMLNamespace
from .file_interface import FileInterface


@dataclass
class MzMLMetadata:
    """Metadata about an mzML file."""

    file_name: str | None = None
    encoding: str = "utf-8"
    file_object: FileInterface | None = None
    offset_dict: dict[str, int] = field(default_factory=dict)  # type: ignore
    obo_version: str | None = None
    mzml_version: str | None = None
    spectrum_count: int | None = None
    chromatogram_count: int | None = None

    # XML Elements
    file_description: bool = False
    file_description_element: ElementTree.Element | None = None
    sample_list: bool = False
    sample_list_element: ElementTree.Element | None = None
    referenceable_param_group_list: bool = False
    referenceable_param_group_list_element: ElementTree.Element | None = None
    software_list: bool = False
    software_list_element: ElementTree.Element | None = None
    instrument_configuration_list: bool = False
    instrument_configuration_list_element: ElementTree.Element | None = None
    data_processing_list: bool = False
    data_processing_list_element: ElementTree.Element | None = None
    run_element: ElementTree.Element | None = None

    # Run info
    run_id: str | None = None
    start_time: str | None = None
    instrument_name: str | None = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def keys(self) -> list[str]:
        return [f.name for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def values(self) -> list[Any]:
        return [getattr(self, f.name) for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def items(self) -> list[tuple[str, Any]]:
        return [(f.name, getattr(self, f.name)) for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())


class Reader:
    """
    Initialize Reader object for a given mzML file.
    """

    def __init__(
        self,
        path_or_file: str | Path | Any,
        MS_precisions: dict[int, float] | None = None,
        obo_version: str | None = None,
        build_index_from_scratch: bool = False,
        skip_chromatogram: bool = True,
        index_regex: Pattern[bytes] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize and set required attributes."""
        self.index_regex: Pattern[bytes] | None = index_regex
        self.build_index_from_scratch: bool = build_index_from_scratch
        self.skip_chromatogram: bool = skip_chromatogram
        if MS_precisions is None:
            MS_precisions = {}
            if "MS1_Precision" in kwargs:
                MS_precisions[1] = kwargs["MS1_Precision"]
            if "MSn_Precision" in kwargs:
                MS_precisions[2] = kwargs["MSn_Precision"]
                MS_precisions[3] = kwargs["MSn_Precision"]

        # Parameters
        self.ms_precisions: dict[int | None, float] = {
            None: 0.0001,  # if spectra does not contain ms_level information
            # e.g. UV-chromatograms (thanks pyeguy) then ms_level is
            # returned as None
            0: 0.0001,
            1: 5e-6,
            2: 20e-6,
            3: 20e-6,
        }
        if MS_precisions:
            for key, value in MS_precisions.items():
                self.ms_precisions[key] = value

        # File info
        self.info: MzMLMetadata = MzMLMetadata()

        # Normalize path_or_file and set encoding
        match path_or_file:
            case Path():
                self.path_or_file: str | Any = str(path_or_file)
                self.info.file_name = self.path_or_file
                self.info.encoding = self._determine_file_encoding(self.path_or_file)
            case str():
                self.path_or_file = path_or_file
                self.info.file_name = path_or_file
                self.info.encoding = self._determine_file_encoding(path_or_file)
            case _:
                self.path_or_file = path_or_file
                self.info.encoding = self._guess_encoding(path_or_file)  # type: ignore[arg-type]

        self.info.file_object = self._open_file(
            self.path_or_file, build_index_from_scratch=self.build_index_from_scratch
        )
        self.info.offset_dict = self.info.file_object.offset_dict
        if obo_version:
            self.info.obo_version = self._obo_version_validator(obo_version)
        else:
            # obo version not specified -> try to identify from mzML by self._init_iter
            self.info.obo_version = None

        self.OT: obo.OboTranslator = self._init_obo_translator()
        self.iter: Iterator[tuple[str, ElementTree.Element]] = self._init_iter()
        self.root: ElementTree.Element
        self._iteration_count: int = 0  # Track how many items we've yielded

    def __next__(self) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Iterates all of the spectra and chromatograms in the file.
        """
        has_ref_group: bool = self.info.referenceable_param_group_list
        event = None
        element = None
        items_to_skip = 0

        while True:
            prev_event, prev_element = event, element
            try:
                event, element = next(self.iter, ("END", "END"))
            except ElementTree.ParseError:
                # XML parse error - likely due to file position corruption from random access
                # Reinitialize the iterator and skip items we've already yielded
                items_to_skip = self._iteration_count
                self.info.file_object.close()  # type: ignore[union-attr]
                self.info.file_object = self._open_file(
                    self.path_or_file, build_index_from_scratch=False
                )
                self.iter = self._init_iter()
                # Try again with fresh iterator
                event, element = next(self.iter, ("END", "END"))
            except Exception as e:
                raise Exception(
                    f"Error during iteration. Previous event: {prev_event}, Previous element: {prev_element}"
                ) from e

            match event:
                case "end":
                    if isinstance(element, str):
                        continue

                    if element.tag.endswith(f"}}{MzMLElement.SPECTRUM}"):
                        # Skip items we've already yielded after reinitialization
                        if items_to_skip > 0:
                            items_to_skip -= 1
                            continue

                        spectrum: spec.Spectrum = spec.Spectrum(
                            element, 
                            
                            obo_version=self.OT.version
                        )
                        if has_ref_group:
                            elem = self.info.referenceable_param_group_list_element
                            if elem is None:
                                raise ValueError(
                                    "Referenceable param group list element is missing."
                                )
                            spectrum.set_params_from_reference_group(
                                elem,
                            )
                        self._iteration_count += 1
                        return spectrum

                    if element.tag.endswith(f"}}{MzMLElement.CHROMATOGRAM}"):
                        if self.skip_chromatogram:
                            continue

                        # Skip items we've already yielded after reinitialization
                        if items_to_skip > 0:
                            items_to_skip -= 1
                            continue

                        chrom: chromatogram.Chromatogram = chromatogram.Chromatogram(
                            element, obo_version=self.OT.version
                        )
                        self._iteration_count += 1
                        return chrom

                case "END":
                    # Reinitialize iterator
                    self.info.file_object.close()  # type: ignore[union-attr]
                    self.info.file_object = self._open_file(
                        self.path_or_file, build_index_from_scratch=False
                    )
                    self.iter = self._init_iter()
                    self._iteration_count = 0  # Reset counter for fresh iteration
                    raise StopIteration

                case _:
                    continue

    def __getitem__(self, identifier: str | int) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Access spectrum or chromatogram with native id 'identifier'.
        """
        with contextlib.suppress(Exception):
            spec_count = self.get_spectrum_count()
            if isinstance(identifier, int) and spec_count is not None and identifier > spec_count:
                raise Exception("Requested identifier is out of range")

        element = self.info.file_object[identifier]  # type: ignore
        if element is None:
            raise KeyError(f"Identifier {identifier} not found in the file.")
        element.obo_translator = self.OT

        return element  # type: ignore

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
        self, path_or_file: str | Path | Any, build_index_from_scratch: bool = False
    ) -> FileInterface:
        """
        Open the path using the FileInterface class as a wrapper.
        """
        # Type assertion: path_or_file should be str or BytesIO at this point
        if not isinstance(path_or_file, (str, Path, BytesIO)):
            raise TypeError(f"Expected str or BytesIO, got {type(path_or_file)}")
        return FileInterface(
            path_or_file,
            self.info.encoding,
            build_index_from_scratch=build_index_from_scratch,
            index_regex=self.index_regex,
        )

    def _guess_encoding(self, mzml_file: Any) -> str:
        """
        Determine the encoding used for the file.
        """
        match: Match[bytes] | None = regex_patterns.FILE_ENCODING_PATTERN.search(
            mzml_file.readline()
        )
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

    @staticmethod
    def _obo_version_validator(version: str) -> str:
        """
        The obo version should fit file names in the obo folder.
        However, some software generate mzML with built in obo version string like:
        '23:06:2017' or even newer version that not in obo folder yet.
        This is to check obo version and try to fit the best obo version
        to the obo version in the mzML file.
        """
        obo_rgx: Pattern[str] = re.compile(r"(\d\.\d{1,2}\.\d{1,2})(_[rR][cC]\d{0,2})?")
        obo_years_rgx: Pattern[str] = re.compile(r"20\d\d")
        obo_year_version_dct: dict[int, str] = {
            2012: "3.40.0",
            2013: "3.50.0",
            2014: "3.60.0",
            2015: "3.75.0",
            2016: "4.0.1",
            2017: "4.1.0",
            2018: "4.1.10",
            2019: "4.1.22",
            2024: "4.1.79",
            2025: "4.1.188",
        }
        version_fixed: str | None = None
        if obo_rgx.match(version):
            version_fixed = version
        else:
            years_found: Match[str] | None = obo_years_rgx.search(version)
            if years_found:
                try:
                    year: int = int(years_found.group(0))
                except ValueError:
                    year = 2000

                if year in obo_year_version_dct:
                    version_fixed = obo_year_version_dct[year]
                else:
                    if year > 2019:
                        version_fixed = "4.1.0"

        if version_fixed:
            # Check if the corresponding obo file existed in obo folder
            obo_root: str = os.path.dirname(__file__)
            obo_file: str = os.path.join(
                obo_root,
                "obo",
                "psi-ms{}.obo".format("-" + version_fixed if version_fixed else ""),
            )
            if os.path.exists(obo_file) or os.path.exists(obo_file + ".gz"):
                pass
            else:
                version_fixed = "1.1.0"
        else:
            version_fixed = "1.1.0"

        return version_fixed

    def _init_obo_translator(self) -> obo.OboTranslator:
        """
        Initialize the obo translator with the minimum requirement
        and extra Accessions.
        """
        # parse obo, check MS tags and if they are ok in minimum.py (minimum
        # required) ...
        if self.info.obo_version is None:
            self.info.obo_version = "4.1.79"
        obo_translator: obo.OboTranslator = obo.OboTranslator.from_cache(
            version=self.info.obo_version
        )

        return obo_translator

    def _init_iter(self) -> Iterator[tuple[str, ElementTree.Element]]:
        """
        Initialize the iterator for the spectra and sets it to the start
        of the spectrumList element.
        """
        if self.info.file_object is None:
            raise ValueError("File object is not initialized.")

        # Pass the FileInterface's underlying file handler directly
        file_handle = self.info.file_object.file_handler.file_handler
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
                        if match_result := regex_patterns.MZML_VERSION_PATTERN.search(
                            schema_location
                        ):
                            self.info.mzml_version = match_result.group()

                case MzMLElement.CV:
                    if not self.info.obo_version and element.attrib.get("id") == "MS":
                        obo_version = element.attrib.get("version", "1.1.0")
                        self.info.obo_version = self._obo_version_validator(obo_version)

                case MzMLElement.FILE_DESCRIPTION:
                    self.info.file_description = True
                    self.info.file_description_element = element

                case MzMLElement.SAMPLE_LIST:
                    self.info.sample_list = True
                    self.info.sample_list_element = element

                case MzMLElement.REFERENCEABLE_PARAM_GROUP_LIST:
                    self.info.referenceable_param_group_list = True
                    self.info.referenceable_param_group_list_element = element

                case MzMLElement.SOFTWARE_LIST:
                    self.info.software_list = True
                    self.info.software_list_element = element

                case MzMLElement.INSTRUMENT_CONFIG_LIST:
                    self.info.instrument_configuration_list = True
                    self.info.instrument_configuration_list_element = element

                case MzMLElement.DATA_PROCESSING_LIST:
                    self.info.data_processing_list = True
                    self.info.data_processing_list_element = element

                case MzMLElement.CV_PARAM:
                    if self.term_is_a_member(element.attrib.get("accession"), "MS:1000494"):
                        self.info.instrument_name = element.attrib.get("name")

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

    def __iter__(self) -> "Reader":
        """Return self."""
        return self

    def next(self) -> spec.Spectrum | chromatogram.Chromatogram:
        """Return the next Spectrum element."""
        return self.__next__()

    def get_spectrum_count(self) -> int | None:
        """
        Number of spectra in file.
        """
        return self.info.spectrum_count

    def get_chromatogram_count(self) -> int | None:
        """
        Number of chromatograms in file.
        """
        return self.info.chromatogram_count

    def get_spectrum(self, identifier: str | int) -> spec.Spectrum:
        """
        Access spectrum with the given identifier.

        Note:
            This method provides the same functionality as using the indexing syntax
            (e.g., run[0]), but with a more explicit method name.
        """
        result = self[identifier]
        if not isinstance(result, spec.Spectrum):
            raise ValueError(f"Identifier {identifier} refers to a chromatogram, not a spectrum")
        return result

    def get_chromatogram(self, identifier: str | int) -> chromatogram.Chromatogram:
        """
        Access chromatogram with the given identifier.

        Note:
            This method is only useful when skip_chromatogram is set to False
            if you want to access chromatograms by index. If skip_chromatogram is True,
            you can still access chromatograms by string identifiers (e.g., 'TIC').
        """
        match identifier:
            case str():
                result = self[identifier]
                if not isinstance(result, chromatogram.Chromatogram):
                    raise ValueError(
                        f"Identifier {identifier} refers to a spectrum, not a chromatogram"
                    )
                return result

            case int():
                _chrom_count = self.get_chromatogram_count()
                if _chrom_count is None:
                    raise Exception("No chromatograms found in the file")

                if identifier >= _chrom_count:
                    raise Exception(
                        f"Chromatogram index {identifier} is out of range (0-{_chrom_count - 1})"
                    )

                # Reset the file pointer and iterate to find the chromatogram
                temp_skip_chromatogram = self.skip_chromatogram
                self.skip_chromatogram = False

                self.info.file_object.close()  # type: ignore[union-attr]
                self.info.file_object = self._open_file(
                    self.path_or_file, build_index_from_scratch=False
                )
                self.iter = self._init_iter()

                chrom_count = 0
                try:
                    for element in self:
                        if isinstance(element, chromatogram.Chromatogram):
                            if chrom_count == identifier:
                                return element
                            chrom_count += 1
                finally:
                    # Restore original skip_chromatogram setting
                    self.skip_chromatogram = temp_skip_chromatogram

                raise Exception(f"Chromatogram with index {identifier} not found")

            case _:
                raise ValueError("Identifier must be a string or an integer")

    def get_spectrum_by_id(self, spectrum_id: int | str) -> spec.Spectrum:
        """Access spectrum with the given native ID."""
        if self.info.file_object is None:
            raise ValueError("File object is not initialized.")
        element = self.info.file_object.get_spectrum_by_id(spectrum_id)
        element.obo_translator = self.OT
        element.measured_precision = self.ms_precisions[element.ms_level]
        return element  # type: ignore

    def get_spectrum_by_index(self, index: int) -> spec.Spectrum:
        """Access spectrum with the given 0-based index."""
        if self.info.file_object is None:
            raise ValueError("File object is not initialized.")
        element = self.info.file_object.get_spectrum_by_index(index)
        element.obo_translator = self.OT
        element.measured_precision = self.ms_precisions[element.ms_level]
        return element  # type: ignore

    def get_chromatogram_by_id(self, chromatogram_id: str) -> chromatogram.Chromatogram:
        """Access chromatogram with the given native ID."""
        if self.info.file_object is None:
            raise ValueError("File object is not initialized.")
        element = self.info.file_object.get_chromatogram_by_id(chromatogram_id)
        element.obo_translator = self.OT
        return element  # type: ignore

    def get_chromatogram_by_index(self, index: int) -> chromatogram.Chromatogram:
        """Access chromatogram with the given 0-based index."""
        if self.info.file_object is None:
            raise ValueError("File object is not initialized.")
        element = self.info.file_object.get_chromatogram_by_index(index)
        element.obo_translator = self.OT
        return element  # type: ignore

    @property
    def TIC(self) -> chromatogram.Chromatogram:
        """Access the Total Ion Chromatogram (TIC)."""
        return self.get_chromatogram_by_id("TIC")

    def close(self) -> None:
        self.info.file_object.close()  # type: ignore[union-attr]

    def term_is_a_member(self, tested_term: str | None, member_of_term: str) -> bool:
        """
        Use translated obo file to check if given term is_a member of the other term.
        """
        is_member: bool = False
        if tested_term is None:
            return False
        try:
            term_in: Any = self.OT[tested_term]
            if term_in:
                is_member = self.OT.id[tested_term]["is_a"].startswith(member_of_term)
        except KeyError:
            print(f"term not found ({tested_term})")
        return is_member


if __name__ == "__main__":
    print(__doc__)
