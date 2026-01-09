"""Base class for mass spectrometry data with common functionality for Spectrum and Chromatogram."""

import re
import xml.etree.ElementTree as ElementTree
from base64 import b64decode as b64dec
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .constants import (
    BINARY_DECODE_DTYPES,
    NUMPRESS_COMPRESSIONS,
    BinaryDataTypeAccession,
    CompressionType,
    EncodingFormat,
    MSAccession,
    SpectrumType,
    XMLAttribute,
    XMLElement,
)
from .decoder import MSDecoder


@dataclass(frozen=True)
class MsData:
    """Base class for mass spectrometry data with common functionality for Spectrum and Chromatogram."""

    element: ElementTree.Element

    @cached_property
    def accessions(self) -> dict[str, str]:
        accessions: dict[str, str] = {}

        for element in self.element.iter():
            accession = element.get(XMLAttribute.ACCESSION)
            name = element.get(XMLAttribute.NAME)
            if accession is not None and name is not None:
                accessions[name] = accession

        return accessions

    @cached_property
    def is_profile(self) -> bool:
        return SpectrumType.PROFILE in self.accessions

    def get_element_by_name(self, name: str) -> ElementTree.Element | None:
        """Get XML element by name from the tree."""
        for ele in self.element.iter():
            if ele.get(XMLAttribute.NAME) == name:
                return ele
        return None

    @cached_property
    def ns(self) -> str:
        """Get XML namespace from the element tag."""
        match = re.match(r"\{.*\}", self.element.tag)
        return match.group(0) if match else ""

    def _get_element_by_path(self, hooks: tuple[str, ...]) -> tuple[ElementTree.Element, ...]:
        """Cachable helper"""
        path_parts = ["."] + [f"{self.ns}{hook}" for hook in hooks]
        path = "/".join(path_parts)
        return tuple(self.element.findall(path))

    def get_element_by_path(self, hooks: list[str]) -> list[ElementTree.Element] | None:
        """Find XML elements by hierarchical path of parent elements."""
        return list(self._get_element_by_path(tuple(hooks)))

    def binary_data_array(self, array_type: str) -> bytes:
        # Try to find binary data array by name first, then by value
        b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.NAME}='{array_type}']/.."
        b_data_array = self.element.find(b_data_string)

        if b_data_array is None:
            # Try non-standard data array with value attribute
            b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@value='{array_type}']/.."
            b_data_array = self.element.find(b_data_string)

        if b_data_array is None:
            return b""

        return b_data_array.find(f"./{self.ns}{XMLElement.BINARY}").text.encode(EncodingFormat.UTF8)  # type: ignore

    def _get_encoding_parameters(
        self, array_type: str
    ) -> tuple[bytes, str, BinaryDataTypeAccession, tuple[str, ...]]:
        """Extract encoding parameters (data, length, type, compression) for array decoding."""

        # Try to find binary data array by name first, then by value
        b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.NAME}='{array_type}']/.."
        b_data_array = self.element.find(b_data_string)

        if b_data_array is None:
            # Try non-standard data array with value attribute
            b_data_string = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}[@value='{array_type}']/.."
            b_data_array = self.element.find(b_data_string)

        # Handle case where no binary data array is found
        if b_data_array is None:
            return (b"", "0", BinaryDataTypeAccession.FLOAT_64, ())

        # Extract compression methods
        comp: list[str] = []
        numpress_encoding = False
        for cvParam in b_data_array.iterfind(f"./{self.ns}{XMLElement.CV_PARAM}"):
            param_name = cvParam.get(XMLAttribute.NAME, "")
            if "compression" in param_name:
                comp.append(param_name)
                if "numpress" in param_name.lower():
                    numpress_encoding = True
        comp_tup: tuple[str, ...] = tuple(comp)

        # Get array length
        d_array_length = self.element.get(XMLAttribute.DEFAULT_ARRAY_LENGTH, "0")

        # Determine data type
        d_type = (
            self._find_data_type(b_data_array)
            if not numpress_encoding
            else BinaryDataTypeAccession.FLOAT_64
        )

        # Extract binary data
        data_element = b_data_array.find(f"./{self.ns}{XMLElement.BINARY}")
        data = b""
        if data_element is not None and data_element.text:
            data = data_element.text.encode(EncodingFormat.UTF8)

        return (data, d_array_length, d_type, comp_tup)

    def get_encoding_data(self, array_type: str) -> bytes:
        """Get binary data for specified array type."""
        data, _, _, _ = self._get_encoding_parameters(array_type)
        return data

    def get_encoding_length(self, array_type: str) -> str:
        """Get data array length for specified array type."""
        _, d_array_length, _, _ = self._get_encoding_parameters(array_type)
        return d_array_length

    def get_encoding_type(self, array_type: str) -> str:
        """Get data type for specified array type."""
        _, _, d_type, _ = self._get_encoding_parameters(array_type)
        return d_type

    def get_encoding_compression(self, array_type: str) -> tuple[str, ...]:
        """Get compression methods for specified array type."""
        _, _, _, comp_tup = self._get_encoding_parameters(array_type)
        return comp_tup

    def get_encoding_parameters(self, array_type: str) -> tuple[bytes, str, str, tuple[str, ...]]:
        """Get all encoding parameters for specified array type."""
        return self._get_encoding_parameters(array_type)

    def _find_data_type(self, b_data_array: ElementTree.Element) -> BinaryDataTypeAccession:
        """Find data type from binary data array element."""
        # List of data types to check, in order of preference

        for data_type in BinaryDataTypeAccession:
            try:
                element = b_data_array.find(
                    f"./{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.ACCESSION}='{data_type}']"
                )
                if element is not None:
                    return data_type
            except (KeyError, TypeError):
                continue

        # Default to 64-bit float if nothing found
        return BinaryDataTypeAccession.FLOAT_64

    def _decode(
        self,
        data: bytes,
        d_array_length: str,
        data_type: BinaryDataTypeAccession,
        comp: tuple[str, ...],
    ) -> NDArray[np.float64]:
        """Decode base64 encoded and compressed binary data to numpy array."""
        out_data: bytes = b64dec(data)

        if len(out_data) == 0:
            return np.array([], dtype=np.float64)

        # Decompress if needed
        if CompressionType.ZLIB in comp or CompressionType.ZLIB_COMPRESSION in comp:
            out_data: bytes = MSDecoder.decode_zlib(out_data)

        # Handle numpress compression
        if any(c in comp for c in NUMPRESS_COMPRESSIONS):
            compression_type: MSAccession | None = self.get_numpress_compression_type(comp)
            if compression_type is None:
                raise ValueError(f"Unsupported numpress compression types: {comp}")
            return MSDecoder.decode_numpress(out_data, compression_type)

        # Decode based on data type
        if data_type not in BINARY_DECODE_DTYPES:
            raise ValueError(f"Unsupported data type for decoding: {data_type}")

        return np.frombuffer(out_data, dtype=BINARY_DECODE_DTYPES[data_type]).astype(np.float64)

    def get_ms_compression_tags(self, compression: tuple[str, ...]) -> tuple[str, ...]:
        """Get MS ontology tags for compression methods."""
        comp_ms_tags: list[str] = []
        for comp in compression:
            obo_entry = self.obo_translator[comp]
            if isinstance(obo_entry, dict) and (entry_id := obo_entry.get("id")):  # type: ignore
                comp_ms_tags.append(entry_id)  # type: ignore
        return tuple(comp_ms_tags)

    def get_numpress_compression_type(self, compression: tuple[str, ...]) -> MSAccession | None:
        """Get MSAccession for numpress compression type."""
        comp_ms_tags = self.get_ms_compression_tags(compression)

        if MSAccession.NUMPRESS_LINEAR in comp_ms_tags:
            return MSAccession.NUMPRESS_LINEAR
        elif MSAccession.NUMPRESS_PIC in comp_ms_tags:
            return MSAccession.NUMPRESS_PIC
        elif MSAccession.NUMPRESS_SLOF in comp_ms_tags:
            return MSAccession.NUMPRESS_SLOF
        return None

    def to_string(
        self, encoding: str = EncodingFormat.LATIN1, method: str = EncodingFormat.XML
    ) -> Any:
        """Return string representation of the XML element in specified encoding and format."""
        return ElementTree.tostring(self.element, encoding=encoding, method=method)  # type: ignore[call-overload]
