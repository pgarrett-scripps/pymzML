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
from typing import Optional, Dict, Any, Union, Iterator, Tuple, IO

from . import spec
from . import chromatogram
from . import obo
from . import regex_patterns
from .file_interface import FileInterface


class Reader(object):
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
        path_or_file: Union[str, Path, IO],
        MS_precisions: Optional[Dict[int, float]] = None,
        obo_version: Optional[str] = None,
        build_index_from_scratch: bool = False,
        skip_chromatogram: bool = True,
        index_regex: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize and set required attributes."""
        self.index_regex: Optional[str] = index_regex
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
        self.ms_precisions: Dict[Optional[int], float] = {
            None: 0.0001,  # if spectra does not contain ms_level information
            # e.g. UV-chromatograms (thanks pyeguy) then ms_level is
            # returned as None
            0: 0.0001,
            1: 5e-6,
            2: 20e-6,
            3: 20e-6,
        }
        self.ms_precisions.update(MS_precisions)

        # File info
        self.info: Dict[str, Any] = ddict()
        self.path_or_file: Union[str, IO] = path_or_file
        if isinstance(self.path_or_file, Path):
            self.path_or_file = str(self.path_or_file)
        if isinstance(self.path_or_file, str):
            self.info["file_name"] = self.path_or_file
            self.info["encoding"] = self._determine_file_encoding(self.path_or_file)
        else:
            self.info["encoding"] = self._guess_encoding(self.path_or_file)

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
        self.iter: Iterator[Tuple[str, ElementTree.Element]] = self._init_iter()
        self.root: ElementTree.Element

    def __next__(self) -> Union[spec.Spectrum, chromatogram.Chromatogram]:
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
            if event == "end":
                if element.tag.endswith("}spectrum"):
                    spectrum: spec.Spectrum = spec.Spectrum(element, obo_version=self.OT.version)
                    if has_ref_group:
                        spectrum._set_params_from_reference_group(
                            self.info["referenceable_param_group_list_element"]
                        )
                    ms_level: Optional[int] = spectrum.ms_level
                    spectrum.measured_precision = self.ms_precisions[ms_level]
                    return spectrum
                if element.tag.endswith("}chromatogram"):
                    if self.skip_chromatogram:
                        continue
                    chrom: chromatogram.Chromatogram = chromatogram.Chromatogram(
                        element, obo_version=self.OT.version
                    )
                    # if has_ref_group:
                    #     spectrum._set_params_from_reference_group(
                    #         self.info['referenceable_param_group_list_element']
                    #     )
                    return chrom
            elif event == "END":
                # reinit iter
                self.info["file_object"].close()
                self.info["file_object"] = self._open_file(
                    self.path_or_file, build_index_from_scratch=False
                )
                self.iter = self._init_iter()
                raise StopIteration

    def __getitem__(
        self, identifier: Union[str, int]
    ) -> Union[spec.Spectrum, chromatogram.Chromatogram]:
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
            if isinstance(identifier, int) and identifier > self.get_spectrum_count():
                raise Exception("Requested identifier is out of range")
        except:
            pass

        element: Union[spec.Spectrum, chromatogram.Chromatogram] = self.info["file_object"][
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
        return type(self.info["file_object"].file_handler)

    def _open_file(
        self, path_or_file: Union[str, IO], build_index_from_scratch: bool = False
    ) -> FileInterface:
        """
        Open the path using the FileInterface class as a wrapper.

        Arguments:
            path (str): path to the file to parse

        Returns:
            (FileInterface): Wrapper class for compressed and uncompressed
                mzml files
        """
        return FileInterface(
            path_or_file,
            self.info["encoding"],
            build_index_from_scratch=build_index_from_scratch,
            index_regex=self.index_regex,
        )

    def _guess_encoding(self, mzml_file: IO) -> str:
        """
        Determine the encoding used for the file.

        Arguments:
            mzml_file (IOBase): an mzml file

        Returns:
            mzml_encoding (str): encoding type of the file
        """
        match: Optional[re.Match] = regex_patterns.FILE_ENCODING_PATTERN.search(
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
        if os.path.exists(path):
            if path.endswith(".gz") or path.endswith(".igz"):
                import gzip

                _open = gzip.open
            else:
                _open = open
            with _open(path, "rb") as sniffer:
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
        obo_rgx: re.Pattern = re.compile(r"(\d\.\d{1,2}\.\d{1,2})(_[rR][cC]\d{0,2})?")
        obo_years_rgx: re.Pattern = re.compile(r"20\d\d")
        obo_year_version_dct: Dict[int, str] = {
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
        version_fixed: Optional[str] = None
        if obo_rgx.match(version):
            version_fixed = version
        else:
            years_found: Optional[re.Match] = obo_years_rgx.search(version)
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
                "psi-ms{0}.obo".format("-" + version_fixed if version_fixed else ""),
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

    def _init_iter(self) -> Iterator[Tuple[str, ElementTree.Element]]:
        """
        Initalize the iterator for the spectra and sets it to the start
        of the spectrumList element.

        Returns:
            mzml_iter (xml.etree.ElementTree._IterParseIterator): Iterator over
                all element in the file starting with the first spectrum
        """
        mzml_iter: Iterator[Tuple[str, ElementTree.Element]] = iter(
            ElementTree.iterparse(self.info["file_object"], events=("end", "start"))
        )  # NOTE: end might be sufficient
        _, self.root = next(mzml_iter)
        self.info["chromatogram_count"] = None
        self.info["spectrum_count"] = None
        while True:
            event, element = next(mzml_iter, ("END", "END"))
            if element.tag.endswith("}mzML"):
                if "version" in element.attrib and len(element.attrib["version"]) > 0:
                    self.info["mzml_version"] = element.attrib["version"]
                else:
                    s: str = element.attrib[
                        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
                    ]
                    self.info["mzml_version"] = re.search(r"[0-9]*\.[0-9]*\.[0-9]*", s).group()
            elif element.tag.endswith("}cv"):
                if not self.info["obo_version"] and element.attrib.get("id", None) == "MS":
                    obo_in_mzml: str = element.attrib.get("version", "1.1.0")
                    self.info["obo_version"] = self._obo_version_validator(obo_in_mzml)

            elif element.tag.endswith("}fileDescription"):
                self.info["file_description"] = True
                self.info["file_description_element"] = element
            elif element.tag.endswith("}sampleList"):
                self.info["sample_list"] = True
                self.info["sample_list_element"] = element

            elif element.tag.endswith("}referenceableParamGroupList"):
                self.info["referenceable_param_group_list"] = True
                self.info["referenceable_param_group_list_element"] = element

            elif element.tag.endswith("}softwareList"):
                self.info["software_list"] = True
                self.info["software_list_element"] = element
            elif element.tag.endswith("}instrumentConfigurationList"):
                self.info["instrument_configuration_list"] = True
                self.info["instrument_configuration_list_element"] = element
            elif element.tag.endswith("}dataProcessingList"):
                self.info["data_processing_list"] = True
                self.info["data_processing_list_element"] = element
            elif element.tag.endswith("}cvParam"):
                if self.term_is_a_member(element.attrib.get("accession"), "MS:1000494"):
                    self.info["instrument_name"] = element.attrib.get("name")

            elif element.tag.endswith("}spectrumList"):
                spec_cnt: Optional[str] = element.attrib.get("count")
                self.info["spectrum_count"] = int(spec_cnt) if spec_cnt else None
                break
            elif element.tag.endswith("}chromatogramList"):
                chrom_cnt: Optional[str] = element.attrib.get("count", None)
                if chrom_cnt:
                    self.info["chromatogram_count"] = int(chrom_cnt)
                break
            elif element.tag.endswith("}run"):
                run_id: Optional[str] = element.attrib.get("id")
                start_time: Optional[str] = element.attrib.get("startTimeStamp")
                self.info["run_element"] = element
                self.info["run_id"] = run_id
                self.info["start_time"] = start_time
            else:
                pass
        self.root.clear()
        return mzml_iter

    def __iter__(self) -> "Reader":
        """Return self."""
        return self

    def next(self) -> Union[spec.Spectrum, chromatogram.Chromatogram]:
        """Function to return the next Spectrum element."""
        return self.__next__()

    def get_spectrum_count(self) -> Optional[int]:
        """
        Number of spectra in file.

        Returns:
            spectrum count (int): Number of spectra in file.
        """
        return self.info["spectrum_count"]

    def get_chromatogram_count(self) -> Optional[int]:
        """
        Number of chromatograms in file.

        Returns:
            chromatogram count (int): Number of chromatograms in file.
        """
        return self.info["chromatogram_count"]

    def get_spectrum(self, identifier: Union[str, int]) -> spec.Spectrum:
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
        return self[identifier]

    def get_chromatogram(self, identifier: Union[str, int]) -> chromatogram.Chromatogram:
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
        if isinstance(identifier, str):
            return self[identifier]

        if isinstance(identifier, int):
            if self.get_chromatogram_count() is None:
                raise Exception("No chromatograms found in the file")

            if identifier >= self.get_chromatogram_count():
                raise Exception(
                    f"Chromatogram index {identifier} is out of range (0-{self.get_chromatogram_count() - 1})"
                )

            # Reset the file pointer and iterate to find the chromatogram
            temp_skip_chromatogram: bool = self.skip_chromatogram
            self.skip_chromatogram = False

            self.info["file_object"].close()
            self.info["file_object"] = self._open_file(
                self.path_or_file, build_index_from_scratch=False
            )
            self.iter = self._init_iter()

            chrom_count: int = 0
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

        raise ValueError("Identifier must be a string or an integer")

    def close(self) -> None:
        self.info["file_object"].close()

    def term_is_a_member(self, tested_term: Optional[str], member_of_term: str) -> bool:
        """
        Use translated obo file to check if given term is_a member of the

        Returns:
            is_member (bool) whether given term is a member of member_of_term

        """
        is_member: bool = False
        try:
            term_in: Any = self.OT[tested_term]
            if term_in:
                is_member = self.OT.id[tested_term]["is_a"].startswith(member_of_term)
        except KeyError:
            print(f"term not found ({tested_term})")
        return is_member


if __name__ == "__main__":
    print(__doc__)
