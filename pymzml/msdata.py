"""
The MsData class offers a base class for mass spectrometry data.
It provides common functionality for both Spectrum and Chromatogram classes.
"""

from typing import Any

import re
import xml.etree.ElementTree as ElementTree
import zlib
from base64 import b64decode as b64dec

import numpy as np
from numpy.typing import NDArray

from .constants import (
    BINARY_DECODE_DTYPES,
    BinaryDataType,
    CompressionType,
    DataType,
    EncodingFormat,
    MSAccession,
    NUMPRESS_COMPRESSIONS,
    SpectrumType,
    XMLAttribute,
    XMLElement,
)
from .obo import OboTranslator
from .decoder import MSDecoder


class MsData(object):
    """
    General base class for mass spectrometry data handling.
    Provides common functionality for both Spectrum and Chromatogram classes.
    """

    def __init__(
        self,
        element: ElementTree.Element | None = None,
        measured_precision: float = 5e-6,
        *,
        obo_version: str | None = None,
    ) -> None:
        """
        Initialize MsData base class.

        Arguments:
            element: XML ElementTree element containing the data
            measured_precision: Measurement precision in ppm (e.g., 5e-6 for 5 ppm)
            obo_version: OBO version string (optional)
        """
        # Core attributes
        self.element: ElementTree.Element | None = element
        self._measured_precision: float = measured_precision
        self.internal_precision: int = int(round(50000.0 / (measured_precision * 1e6)))
        self.obo_translator: OboTranslator = OboTranslator.from_cache(obo_version)
        self.noise_level_estimate: dict[str, float] = {}

        # XML namespace
        self.ns: str = ""
        if self.element is not None:
            match = re.match(r"\{.*\}", self.element.tag)
            self.ns = match.group(0) if match else ""

        # Data arrays (lazily loaded) - always stored as numpy arrays internally
        self._mz: NDArray[np.float64] | None = None
        self._i: NDArray[np.float64] | None = None
        self._time: NDArray[np.float64] | None = None

        # Other common attributes
        self._profile: NDArray[np.float64] | bool | None = None
        self.accessions: dict[str, str] = {}

    def _read_accessions(self) -> None:
        """Set all required variables for this spectrum."""
        self.accessions = {}
        if self.element is None:
            raise ValueError("ElementTree element is None.")

        for element in self.element.iter():
            accession = element.get(XMLAttribute.ACCESSION)
            name = element.get(XMLAttribute.NAME)
            if accession is not None and name is not None:
                self.accessions[name] = accession

        if SpectrumType.PROFILE in self.accessions:
            self._profile = True

    def get_element_by_name(self, name: str) -> ElementTree.Element | None:
        """
        Get element from the original tree by its unit name.

        Arguments:
            name (str): unit name of the mzml element.

        Returns:
            element: XML element with the given name, or None if not found
        """
        if self.element is None:
            return None

        for ele in self.element.iter():
            if ele.get(XMLAttribute.NAME) == name:
                return ele
        return None

    def get_element_by_path(self, hooks: list[str]) -> list[ElementTree.Element] | None:
        """
        Find elements in spectrum by its path.

        Arguments:
            hooks (list): list of parent elements for the target element.

        Returns:
            elements (list): list of XML objects found in the path

        Example:
            To access cvParam in scanWindow tag:

            >>> spec.get_element_by_path(['scanList', 'scan', 'scanWindowList',
            ...     'scanWindow', 'cvParam'])
        """
        if not hooks or self.element is None:
            return None

        path_parts = ["."] + [f"{self.ns}{hook}" for hook in hooks]
        path = "/".join(path_parts)
        return self.element.findall(path)

    def _register(self, decoded_tuple: tuple[str, NDArray[np.float64]]) -> None:
        """Register decoded array data to appropriate attribute."""
        d_type, array = decoded_tuple
        if d_type == DataType.MZ:
            self._mz = array
        elif d_type == DataType.INTENSITY:
            self._i = array
        elif d_type == DataType.TIME:
            self._time = array
        else:
            raise ValueError(f"Unknown data type: {d_type}")

    def _get_encoding_parameters(self, array_type: str) -> tuple[bytes, str, str, list[str]]:
        """
        Find the correct parameter for decoding and return them as tuple.

        Arguments:
            array_type (str): data type of the array, e.g. m/z, time or intensity

        Returns:
            data (bytes): encoded data
            d_array_length (str): length of the data array
            d_type (str): data type (e.g., "32-bit float")
            comp (List[str]): compression methods
        """
        if self.element is None:
            raise ValueError("ElementTree element is None.")

        # Try to find binary data array by name first, then by value
        b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.NAME}='{array_type}']/.."
        b_data_array = self.element.find(b_data_string)

        if b_data_array is None:
            # Try non-standard data array with value attribute
            b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@value='{array_type}']/.."
            b_data_array = self.element.find(b_data_string)

        # Handle case where no binary data array is found
        if b_data_array is None:
            return (b"", "0", BinaryDataType.FLOAT_64, [])

        # Extract compression methods
        comp: list[str] = []
        numpress_encoding = False
        for cvParam in b_data_array.iterfind(f"./{self.ns}{XMLElement.CV_PARAM}"):
            param_name = cvParam.get(XMLAttribute.NAME, "")
            if "compression" in param_name:
                comp.append(param_name)
                if "numpress" in param_name.lower():
                    numpress_encoding = True

        # Get array length
        d_array_length = self.element.get(XMLAttribute.DEFAULT_ARRAY_LENGTH, "0")

        # Determine data type
        d_type = (
            self._find_data_type(b_data_array) if not numpress_encoding else BinaryDataType.FLOAT_64
        )

        # Extract binary data
        data_element = b_data_array.find(f"./{self.ns}{XMLElement.BINARY}")
        data = b""
        if data_element is not None and data_element.text:
            data = data_element.text.encode(EncodingFormat.UTF8)

        return (data, d_array_length, d_type, comp)

    def _find_data_type(self, b_data_array: ElementTree.Element) -> str:
        """
        Find the data type from the binary data array element.

        Arguments:
            b_data_array: Binary data array XML element

        Returns:
            Data type name (e.g., "32-bit float")
        """
        # List of data types to check, in order of preference

        for data_type in BinaryDataType:
            try:
                obo_entry = self.obo_translator[data_type]
                if obo_entry is None:
                    continue
                accession: Any = obo_entry["id"]
                element = b_data_array.find(
                    f"./{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.ACCESSION}='{accession}']"
                )
                if element is not None:
                    return element.get(XMLAttribute.NAME, BinaryDataType.FLOAT_64)
            except (KeyError, TypeError):
                continue

        # Default to 64-bit float if nothing found
        return BinaryDataType.FLOAT_64

    @property
    def measured_precision(self) -> float:
        """
        Get the measured precision.

        Returns:
            value (float): measured Precision (e.g. 5e-6)
        """
        return self._measured_precision

    @measured_precision.setter
    def measured_precision(self, value: float) -> None:
        """Set the measured and internal precision."""
        self._measured_precision = value
        self.internal_precision = int(round(50000.0 / (value * 1e6)))

    def _decode(
        self, data: bytes, d_array_length: str, data_type: str, comp: list[str]
    ) -> NDArray[np.float64]:
        """
        Decode the b64 encoded and packed strings from data as numpy arrays.

        Arguments:
            data: Base64 encoded binary data
            d_array_length: Length of the data array as string
            data_type: Data type (e.g., "32-bit float")
            comp: List of compression methods

        Returns:
            Decoded numpy array
        """
        out_data: bytes | NDArray[np.float64] = b64dec(data)

        if len(out_data) == 0:
            return np.array([], dtype=np.float64)

        # Decompress if needed
        if CompressionType.ZLIB in comp or CompressionType.ZLIB_COMPRESSION in comp:
            out_data = zlib.decompress(out_data)

        # Handle numpress compression
        if any(c in comp for c in NUMPRESS_COMPRESSIONS):
            return self._decode_numpress(out_data, comp)

        data_type_enum: BinaryDataType = BinaryDataType(data_type)

        # Decode based on data type
        if data_type not in BINARY_DECODE_DTYPES:
            raise ValueError(f"Unsupported data type for decoding: {data_type}")

        return np.frombuffer(out_data, dtype=BINARY_DECODE_DTYPES[data_type_enum]).astype(
            np.float64
        )

    # Legacy compatibility methods for tests
    def _decode_to_numpy(
        self, data: bytes, d_array_length: str, data_type: str, comp: list[str]
    ) -> NDArray[np.float64]:
        """Legacy method for backward compatibility."""
        return self._decode(data, d_array_length, data_type, comp)

    def _decode_to_tuple(
        self, data: bytes, d_array_length: str, data_type: str, comp: list[str]
    ) -> NDArray[np.float64]:
        """Legacy method for backward compatibility."""
        return self._decode(data, d_array_length, data_type, comp)

    def _decode_numpress(self, data: bytes, compression: list[str]) -> NDArray[np.float64]:
        """
        Decode numpress encoded data (golomb-rice encoding).

        Arguments:
            data: Encoded data bytes
            compression: Decompression algorithm to be used
                (valid are 'ms-np-linear', 'ms-np-pic', 'ms-np-slof')

        Returns:
            Decoded numpy array of floats
        """
        comp_ms_tags: list[str] = []
        for comp in compression:
            obo_entry = self.obo_translator[comp]
            if obo_entry is not None and isinstance(obo_entry, dict):
                entry_id: str | None = obo_entry.get("id")
                if entry_id:
                    comp_ms_tags.append(entry_id)
        data_array = np.frombuffer(data, dtype=np.uint8)

        if MSAccession.NUMPRESS_LINEAR in comp_ms_tags:
            return MSDecoder.decode_linear(data_array)
        elif MSAccession.NUMPRESS_PIC in comp_ms_tags:
            return MSDecoder.decode_pic(data_array)
        elif MSAccession.NUMPRESS_SLOF in comp_ms_tags:
            return MSDecoder.decode_slof(data_array)

        return np.array([], dtype=np.float64)

    def _array(self, data: list[Any] | NDArray[Any]) -> NDArray[np.float64]:
        """Convert data to numpy array if needed."""
        if isinstance(data, np.ndarray):
            return data.astype(np.float64) if data.dtype != np.float64 else data
        return np.array(data, dtype=np.float64)

    def _median(self, data: list[float] | NDArray[np.float64]) -> float:
        """
        Compute median.

        Arguments:
            data: list or array of numeric values

        Returns:
            median of the input data
        """
        return float(np.median(data))

    def to_string(
        self, encoding: str = EncodingFormat.LATIN1, method: str = EncodingFormat.XML
    ) -> Any:
        """
        Return string representation of the xml element.

        Keyword Arguments:
            encoding: text encoding of the returned string (default: latin-1)
            method: text format of the returned string (default: xml)
                    alternatives are html and text

        Returns:
            xml string representation of the element
        """
        if self.element is None:
            return b""
        return ElementTree.tostring(self.element, encoding=encoding, method=method)  # type: ignore[call-overload]
