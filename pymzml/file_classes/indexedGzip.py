import codecs
import gzip
from collections import OrderedDict
from xml.etree.ElementTree import XML

from ..utils.gzip_reader import GzipReader
from .xml_tuple import ElementType, MzmlXMLElement


class IndexedGzip:
    """mzML reader with pre-built index for efficient random access to gzipped files."""

    def __init__(self, path: str, encoding: str) -> None:
        self.path: str = path
        self.file_handler = codecs.getreader(encoding)(gzip.open(path))  # noqa: SIM115
        #self._offset_dict: OrderedDict[int | str, int] = OrderedDict()
                
        self.spectrum_offsets: OrderedDict[str, int] = OrderedDict()
        self.chromatogram_offsets: OrderedDict[str, int] = OrderedDict()
        self._spectrum_keys: list[str] = []  # For fast O(1) index access
        self._chromatogram_keys: list[str] = []  # For fast O(1) index access

        self._build_index()

    def __del__(self) -> None:
        self.Reader.close()
        self.file_handler.close()

    def _build_index(self) -> None:
        self.Reader: GzipReader = GzipReader(self.path)
        self._offset_dict: OrderedDict[int | str, int] = self.Reader.index
        # Populate offset dictionaries and key lists - separate spectra and chromatograms
        for key, offset in self._offset_dict.items():
            # Chromatograms typically have string IDs like "TIC"
            # Spectra typically have numeric IDs
            if isinstance(key, str) and not key.isdigit():
                self.chromatogram_offsets[key] = offset
                self._chromatogram_keys.append(key)
            else:
                # Store string version in offsets dict, but keep original key for lookups
                key_str = str(key)
                self.spectrum_offsets[key_str] = offset
                self._spectrum_keys.append(key)  # Keep original key type for read_block

    @property
    def offset_dict(self) -> dict[str | int, int]:
        """Return offset dictionary (for backward compatibility)."""
        return dict(self._offset_dict)
    
    @property
    def combined_offsets(self) -> dict[str | int, int]:
        """Return combined offset dictionary."""
        return dict(self._offset_dict)

    def read(self, size: int = -1) -> str:
        return self.file_handler.read(size)

    def get_file_handler(self, encoding: str) -> codecs.StreamReader:
        """Return a fresh decompressed text file handler."""
        return codecs.getreader(encoding)(gzip.open(self.path))  # noqa: SIM115

    def _get_element_by_key(
        self, key: str | int, expected_type: ElementType | None = None
    ) -> MzmlXMLElement:
        """Internal method to retrieve element by key from indexed gzip."""
        ns_prefix = (
            '<mzML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation='
            '"http://psi.hupo.org/ms/mzml http://psidev.info/files/ms/mzML/xsd/mzML1.1.0.xsd" id="test_Creinhardtii_QE_pH8" '
            'version="1.1.0" xmlns="http://psi.hupo.org/ms/mzml">'
        )
        ns_suffix = "</mzML>"
        data = self.Reader.read_block(key)
        root = XML(ns_prefix + data.decode("utf-8") + ns_suffix)

        # The parsed XML is the root mzML element, find the actual spectrum/chromatogram child
        element = None
        element_type: ElementType | None = None
        for child in root:
            if child.tag.endswith("}spectrum"):
                element = child
                element_type = ElementType.SPECTRUM
                break
            elif child.tag.endswith("}chromatogram"):
                element = child
                element_type = ElementType.CHROMATOGRAM
                break

        if element is None or element_type is None:
            raise ValueError(f"No spectrum or chromatogram found in XML for key {key}")

        if expected_type is not None and element_type != expected_type:
            raise ValueError(f"Expected {expected_type} but found {element_type}")

        return MzmlXMLElement(element=element, element_type=element_type)

    def get_spectrum_by_index(self, index: int) -> MzmlXMLElement:
        """Retrieve spectrum by 0-based index."""
        if not (0 <= index < len(self._spectrum_keys)):
            raise IndexError(f"Spectrum index {index} out of range [0, {len(self._spectrum_keys)})")
        key = self._spectrum_keys[index]
        return self._get_element_by_key(key, expected_type=ElementType.SPECTRUM)

    def get_spectrum_by_id(self, identifier: str | int) -> MzmlXMLElement:
        """Retrieve spectrum by native ID."""
        if isinstance(identifier, int):
            identifier = str(identifier)
        if identifier not in self.spectrum_offsets:
            raise KeyError(f"Spectrum ID {identifier} not found in index")
        return self._get_element_by_key(identifier, expected_type=ElementType.SPECTRUM)

    def get_chromatogram_by_index(self, index: int) -> MzmlXMLElement:
        """Retrieve chromatogram by 0-based index."""
        if not (0 <= index < len(self._chromatogram_keys)):
            raise IndexError(
                f"Chromatogram index {index} out of range [0, {len(self._chromatogram_keys)})"
            )
        key = self._chromatogram_keys[index]
        return self._get_element_by_key(key, expected_type=ElementType.CHROMATOGRAM)

    def get_chromatogram_by_id(self, identifier: str | int) -> MzmlXMLElement:
        """Retrieve chromatogram by native ID."""
        if isinstance(identifier, int):
            identifier = str(identifier)
        if identifier not in self.chromatogram_offsets:
            raise KeyError(f"Chromatogram ID {identifier} not found in index")
        return self._get_element_by_key(identifier, expected_type=ElementType.CHROMATOGRAM)

        
    def close(self) -> None:
        """Close the handlers."""
        self.Reader.close()
        self.file_handler.close()

    @property
    def TIC(self) -> MzmlXMLElement:
        """Retrieve the Total Ion Chromatogram (TIC)."""
        return self.get_chromatogram_by_id("TIC")