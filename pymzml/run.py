"""
The class :py:class:`Reader` has been designed to selectively extract data
from a mzML file and to expose the data as a python object.
Necessary information are read in and stored in a fast
accessible format.
The reader itself is an iterator, thus looping over all spectra
follows the classical pythonian syntax.
Additionally one can random access spectra by their nativeID
if the file if not truncated by a conversion Program.

Note:
    The class :py:class:`Writer` is still in development.

"""

import re
import os
import xml.etree.ElementTree as ElementTree
from collections import defaultdict as ddict
from pathlib import Path
from typing import Any
from collections.abc import Iterator
from re import Pattern, Match
from io import BytesIO

from . import spec
from . import chromatogram
from . import obo
from . import regex_patterns
from .file_interface import FileInterface
from .constants import MzMLElement, XMLNamespace


class Reader:
    """
    Initialize Reader object for a given mzML file.

    Arguments:
        path (str): path to the mzml file to parse.

    Keyword Arguments:
        MS_precisions (dict): measured precisions for the different MS levels.
            e.g.::

                {
                    1 : 5e-6,
                    2 : 20e-6
                }

        obo_version (str, optional): obo version number as string. If not
            specified the version will be extracted from the mzML file

    Note:
        Setting the precision for MS1 and MSn spectra has changed in version 1.2.
        However, the old syntax as kwargs is still compatible ( e.g. 'MS1_Precision=5e-6').
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
            if "MS1_Precision" in kwargs.keys():
                MS_precisions[1] = kwargs["MS1_Precision"]
            if "MSn_Precision" in kwargs.keys():
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
        self.info: dict[str, Any] = ddict()
        
        # Normalize path_or_file and set encoding
        match path_or_file:
            case Path():
                self.path_or_file: str | Any = str(path_or_file)
                self.info["file_name"] = self.path_or_file
                self.info["encoding"] = self._determine_file_encoding(self.path_or_file)
            case str():
                self.path_or_file = path_or_file
                self.info["file_name"] = path_or_file
                self.info["encoding"] = self._determine_file_encoding(path_or_file)
            case _:
                self.path_or_file = path_or_file
                self.info["encoding"] = self._guess_encoding(path_or_file)  # type: ignore[arg-type]

        self.info["file_object"] = self._open_file(
            self.path_or_file, build_index_from_scratch=self.build_index_from_scratch
        )
        self.info["offset_dict"] = self.info["file_object"].offset_dict
        if obo_version:
            self.info["obo_version"] = self._obo_version_validator(obo_version)
        else:
            # obo version not specified -> try to identify from mzML by self._init_iter
            self.info["obo_version"] = None

        self.OT: obo.OboTranslator = self._init_obo_translator()
        self.iter: Iterator[tuple[str, ElementTree.Element]] = self._init_iter()
        self.root: ElementTree.Element

    def __next__(self) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Iterator for the class :py:class:`Run`.

        Iterates all of the spectra in the file.

        Returns:
            Spectrum (:py:class:`Spectrum`): a spectrum object with interface
                to the original spectrum element.

        Example:

        >>> for spectrum in Reader:
        ...     print(spectrum.mz, end='\\r')

        """
        has_ref_group: bool = self.info.get("referenceable_param_group_list", False)
        
        while True:
            event, element = next(self.iter, ("END", "END"))
            
            match event:
                case "end":
                    if isinstance(element, str):
                        continue
                        
                    if element.tag.endswith(f"}}{MzMLElement.SPECTRUM}"):
                        spectrum: spec.Spectrum = spec.Spectrum(element, obo_version=self.OT.version)
                        if has_ref_group:
                            spectrum.set_params_from_reference_group(
                                self.info["referenceable_param_group_list_element"]
                            )
                        ms_level: int | None = spectrum.ms_level
                        spectrum.measured_precision = self.ms_precisions[ms_level]
                        return spectrum
                        
                    if element.tag.endswith(f"}}{MzMLElement.CHROMATOGRAM}"):
                        if self.skip_chromatogram:
                            continue
                        chrom: chromatogram.Chromatogram = chromatogram.Chromatogram(
                            element, obo_version=self.OT.version
                        )
                        return chrom
                        
                case "END":
                    # Reinitialize iterator
                    self.info["file_object"].close()
                    self.info["file_object"] = self._open_file(
                        self.path_or_file, build_index_from_scratch=False
                    )
                    self.iter = self._init_iter()
                    raise StopIteration
                
                case _:
                    continue

    def __getitem__(
        self, identifier: str | int
    ) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Access spectrum or chromatogram with native id 'identifier'.

        Arguments:
            identifier (str or int): last number in the id tag of the spectrum
                element or a chromatogram identifier like 'TIC'

        Returns:
            spectrum (Spectrum or Chromatogram): spectrum/chromatogram object
            with native id 'identifier'
        """
        try:
            spec_count = self.get_spectrum_count()
            if isinstance(identifier, int) and spec_count is not None and identifier > spec_count:
                raise Exception("Requested identifier is out of range")
        except:
            pass

        element: spec.Spectrum | chromatogram.Chromatogram = self.info["file_object"][
            identifier
        ]
        element.obo_translator = self.OT

        if isinstance(element, spec.Spectrum):
            element.measured_precision = self.ms_precisions[element.ms_level]

        return element

    def __enter__(self) -> "Reader":
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.close()

    @property
    def file_class(self) -> type:
        """Return file object in use."""
        file = self.info["file_object"]
        if hasattr(file, "file_handler"):
            return type(file.file_handler) # type: ignore
        raise AttributeError("The file object does not have a 'file_handler' attribute.")

    def _open_file(
        self, path_or_file: str | Path | Any, build_index_from_scratch: bool = False
    ) -> FileInterface:
        """
        Open the path using the FileInterface class as a wrapper.

        Arguments:
            path (str): path to the file to parse

        Returns:
            (FileInterface): Wrapper class for compressed and uncompressed
                mzml files
        """
        # Type assertion: path_or_file should be str or BytesIO at this point
        if not isinstance(path_or_file, (str, Path, BytesIO)):
            raise TypeError(f"Expected str or BytesIO, got {type(path_or_file)}")
        return FileInterface(
            path_or_file,
            self.info["encoding"],
            build_index_from_scratch=build_index_from_scratch,
            index_regex=self.index_regex,
        )

    def _guess_encoding(self, mzml_file: Any) -> str:
        """
        Determine the encoding used for the file.

        Arguments:
            mzml_file: an mzML file opened in binary mode

        Returns:
            mzml_encoding (str): encoding type of the file
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

        Arguments:
            path (str): path to the mzml files

        Returns:
            mzml_encoding (str): encoding type of the file
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

        Arguments:
            version (str): The original version to check.

        Returns:
            version_fixed (str): The checked obo version.
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

        Returns:
            obo_translator (OboTranslator): translator class to translate
                accessions to names
        """
        # parse obo, check MS tags and if they are ok in minimum.py (minimum
        # required) ...
        if self.info.get("obo_version", None) is None:
            self.info["obo_version"] = "4.1.79"
        obo_translator: obo.OboTranslator = obo.OboTranslator.from_cache(
            version=self.info["obo_version"]
        )

        return obo_translator

    def _init_iter(self) -> Iterator[tuple[str, ElementTree.Element]]:
        """
        Initalize the iterator for the spectra and sets it to the start
        of the spectrumList element.

        Returns:
            mzml_iter (xml.etree.ElementTree._IterParseIterator): Iterator over
                all element in the file starting with the first spectrum
        """
        mzml_iter: Iterator[tuple[str, ElementTree.Element]] = iter(
            ElementTree.iterparse(self.info["file_object"], events=("end", "start"))
        )  # NOTE: end might be sufficient
        _, self.root = next(mzml_iter)
        self.info["chromatogram_count"] = None
        self.info["spectrum_count"] = None
        while True:
            _, element = next(mzml_iter, ("END", "END"))
            
            if isinstance(element, str):
                break
            
            # Extract tag suffix for matching
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            
            match tag:
                case MzMLElement.MZML:
                    if "version" in element.attrib and element.attrib["version"]:
                        self.info["mzml_version"] = element.attrib["version"]
                    else:
                        schema_location = element.attrib.get(XMLNamespace.SCHEMA_LOCATION, "")
                        if match_result := regex_patterns.MZML_VERSION_PATTERN.search(schema_location):
                            self.info["mzml_version"] = match_result.group()
                            
                case MzMLElement.CV:
                    if not self.info["obo_version"] and element.attrib.get("id") == "MS":
                        obo_version = element.attrib.get("version", "1.1.0")
                        self.info["obo_version"] = self._obo_version_validator(obo_version)
                        
                case MzMLElement.FILE_DESCRIPTION:
                    self.info["file_description"] = True
                    self.info["file_description_element"] = element
                    
                case MzMLElement.SAMPLE_LIST:
                    self.info["sample_list"] = True
                    self.info["sample_list_element"] = element
                    
                case MzMLElement.REFERENCEABLE_PARAM_GROUP_LIST:
                    self.info["referenceable_param_group_list"] = True
                    self.info["referenceable_param_group_list_element"] = element
                    
                case MzMLElement.SOFTWARE_LIST:
                    self.info["software_list"] = True
                    self.info["software_list_element"] = element
                    
                case MzMLElement.INSTRUMENT_CONFIG_LIST:
                    self.info["instrument_configuration_list"] = True
                    self.info["instrument_configuration_list_element"] = element
                    
                case MzMLElement.DATA_PROCESSING_LIST:
                    self.info["data_processing_list"] = True
                    self.info["data_processing_list_element"] = element
                    
                case MzMLElement.CV_PARAM:
                    if self.term_is_a_member(element.attrib.get("accession"), "MS:1000494"):
                        self.info["instrument_name"] = element.attrib.get("name")
                        
                case MzMLElement.SPECTRUM_LIST:
                    spec_cnt: str | None = element.attrib.get("count")
                    self.info["spectrum_count"] = int(spec_cnt) if spec_cnt else None
                    break
                    
                case MzMLElement.CHROMATOGRAM_LIST:
                    chrom_cnt: str | None = element.attrib.get("count")
                    if chrom_cnt:
                        self.info["chromatogram_count"] = int(chrom_cnt)
                    break
                    
                case MzMLElement.RUN:
                    self.info["run_element"] = element
                    self.info["run_id"] = element.attrib.get("id")
                    self.info["start_time"] = element.attrib.get("startTimeStamp")

                case _:
                    pass
                
        self.root.clear()
        return mzml_iter

    def __iter__(self) -> "Reader":
        """Return self."""
        return self

    def next(self) -> spec.Spectrum | chromatogram.Chromatogram:
        """Function to return the next Spectrum element."""
        return self.__next__()

    def get_spectrum_count(self) -> int | None:
        """
        Number of spectra in file.

        Returns:
            spectrum count (int): Number of spectra in file.
        """
        val: Any = self.info["spectrum_count"]
        match val:
            case int():
                return val
            case None:
                return None
            case str():
                return int(val)
            case _:
                raise TypeError("spectrum_count is not of type int or None")

    def get_chromatogram_count(self) -> int | None:
        """
        Number of chromatograms in file.

        Returns:
            chromatogram count (int): Number of chromatograms in file.
        """
        val: Any = self.info["chromatogram_count"]
        match val:
            case int():
                return val
            case None:
                return None
            case str():
                return int(val)
            case _:
                raise TypeError("chromatogram_count is not of type int or None")

    def get_spectrum(self, identifier: str | int) -> spec.Spectrum:
        """
        Access spectrum with the given identifier.

        Arguments:
            identifier (str or int): Either a string identifier or an index (0-based)
                to access spectra in order.

        Returns:
            spectrum (Spectrum): spectrum object with the given identifier

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

        Arguments:
            identifier (str or int): Either a string identifier like 'TIC' or
                an index (0-based) to access chromatograms in order.

        Returns:
            chromatogram (Chromatogram): chromatogram object with the given identifier

        Note:
            This method is only useful when skip_chromatogram is set to False
            if you want to access chromatograms by index. If skip_chromatogram is True,
            you can still access chromatograms by string identifiers (e.g., 'TIC').
        """
        match identifier:
            case str():
                result = self[identifier]
                if not isinstance(result, chromatogram.Chromatogram):
                    raise ValueError(f"Identifier {identifier} refers to a spectrum, not a chromatogram")
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

                self.info["file_object"].close()
                self.info["file_object"] = self._open_file(
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

    def close(self) -> None:
        self.info["file_object"].close()

    def term_is_a_member(self, tested_term: str | None, member_of_term: str) -> bool:
        """
        Use translated obo file to check if given term is_a member of the

        Returns:
            is_member (bool) whether given term is a member of member_of_term

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
