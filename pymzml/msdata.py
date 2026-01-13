"""Base class for mass spectrometry data with common functionality for Spectrum and Chromatogram."""
import re
import xml.etree.ElementTree as ElementTree
from base64 import b64decode as b64dec
from dataclasses import dataclass
from functools import cached_property
from typing import Any, NamedTuple
import logging

import numpy as np
from numpy.typing import NDArray

from .constants import (
    BINARY_DECODE_DTYPES,
    BinaryDataTypeAccession,
    CompressionTypeAccessions,
    EncodingFormat,
    ScanPolarity,
    XMLAttribute,
    XMLElement, BinaryDataArrayAccession,
)
from .decoder import MSDecoder


class EncodingParameters(NamedTuple):
    data: bytes | None
    data_type: BinaryDataTypeAccession | None
    compression: CompressionTypeAccessions | None

    def __str__(self) -> str:
        return f"EncodingParameters(data_length={len(self.data) if self.data else 0}, data_type={self.data_type.name if self.data_type else 'Unknown'}, compression={self.compression.name if self.compression else 'Unknown'})"
    
    def __repr__(self) -> str:
        return str(self)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class MsData:
    """Base class for mass spectrometry data with common functionality for Spectrum and Chromatogram."""

    element: ElementTree.Element

    @cached_property
    def accessions(self) -> set[str]:
        """Get all accessions from direct cvParam children of spectrum element."""
        return {
            acc
            for element in self.element.findall(f"./{self.ns}{XMLElement.CV_PARAM}")
            if (acc := element.get(XMLAttribute.ACCESSION)) is not None
        }

    @cached_property
    def ns(self) -> str:
        """Get XML namespace from the element tag."""
        return match.group(0) if (match := re.match(r"\{.*\}", self.element.tag)) else ""

    def get_element_by_accession(self, accession: str) -> ElementTree.Element | None:
        """Get XML element by accession from the tree."""
        return next(
            (ele for ele in self.element.iter() if ele.get(XMLAttribute.ACCESSION) == accession),
            None,
        )

    def get_element_by_name(self, name: str) -> ElementTree.Element | None:
        """Get XML element by name from the tree."""
        return next(
            (ele for ele in self.element.iter() if ele.get(XMLAttribute.NAME) == name), None
        )

    def _find_binary_data_array_element(self, accession: str) -> ElementTree.Element | None:
        """Helper to find the binary data array element by accession"""
        base_path = f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}/{self.ns}{XMLElement.BINARY_DATA_ARRAY}/{self.ns}{XMLElement.CV_PARAM}"
        result = self.element.find(f"{base_path}[@{XMLAttribute.ACCESSION}='{accession}']/..")
        return result

    def binary_data_array(
        self, accession: str, b_data_array: ElementTree.Element | None = None
    ) -> bytes | None:
        if b_data_array is None:
            b_data_array = self._find_binary_data_array_element(accession)

        if b_data_array is None:
            return None

        binary: ElementTree.Element | None = b_data_array.find(f"./{self.ns}{XMLElement.BINARY}")

        if binary is not None and binary.text:
            return binary.text.encode(EncodingFormat.UTF8)

        return None

    def get_compression_methods(
        self, accession: str, b_data_array: ElementTree.Element | None
    ) -> CompressionTypeAccessions | None:
        """Get compression methods for specified binary data array type."""

        if b_data_array is None:
            b_data_array = self._find_binary_data_array_element(accession)

        if b_data_array is None:
            return None

        for cvParam in b_data_array.iterfind(f"./{self.ns}{XMLElement.CV_PARAM}"):
            cv_accession = cvParam.get(XMLAttribute.ACCESSION, None)
            if cv_accession is None:
                continue
            try:
                return CompressionTypeAccessions(cv_accession)
            except ValueError:
                continue
        return None

    def get_data_array_length(self) -> int | None:
        """Get data array length for specified binary data array type."""
        d_array_length = self.element.get(XMLAttribute.DEFAULT_ARRAY_LENGTH, None)
        return int(d_array_length) if d_array_length is not None else None

    def get_data_array_type(
        self, accession: str, b_data_array: ElementTree.Element | None
    ) -> BinaryDataTypeAccession | None:
        """Get data type for specified binary data array type."""
        if b_data_array is None:
            b_data_array = self._find_binary_data_array_element(accession)
        if b_data_array is None:
            return None
        for data_type in BinaryDataTypeAccession:
            element = b_data_array.find(
                f"./{self.ns}{XMLElement.CV_PARAM}[@{XMLAttribute.ACCESSION}='{data_type}']"
            )
            if element is not None:
                return data_type
        return None

    @cached_property
    def _encoding_parameters_map(self) -> dict[BinaryDataArrayAccession, EncodingParameters]:
        """Cache encoding parameters for all binary data arrays."""
        params_map: dict[BinaryDataArrayAccession, EncodingParameters] = {}
        bdal = self.element.find(f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY_LIST}")
        if bdal is None:
            return params_map
        
        for bda_element in bdal.findall(f"./{self.ns}{XMLElement.BINARY_DATA_ARRAY}"):
            binary_data = self.binary_data_array("", bda_element)
            data_type = self.get_data_array_type("", bda_element)
            compression = self.get_compression_methods("", bda_element)
    
            params = EncodingParameters(binary_data, data_type, compression)
            
            for cv in bda_element.findall(f"./{self.ns}{XMLElement.CV_PARAM}"):
                if acc := cv.get(XMLAttribute.ACCESSION):
                    try:
                        # Validate accession by trying to create BinaryDataArrayAccession
                        bda_acc = BinaryDataArrayAccession(acc)
                    except ValueError:
                        continue
                    params_map[bda_acc] = params

        return params_map

    def get_encoding_parameters(self, array_type: BinaryDataArrayAccession) -> EncodingParameters | None:
        return self._encoding_parameters_map.get(array_type)

    def decode_binary_data_array(self, array_type: BinaryDataArrayAccession) -> NDArray[np.float64] | None:
        """Decode binary data array of specified type to numpy array."""
        encoding_params = self.get_encoding_parameters(array_type)
        logger.debug(f"Decoding binary data array for type {array_type.name} with params {encoding_params}")
    
        if encoding_params is None:
            return None

        if encoding_params.data is None:
            return None

        # Create new params with defaults if needed to suppress warnings/errors in _decode
        # Actually _decode should handle None gracefully or we construct valid params

        # To match previous logic of decode_binary_data_array setting defaults:
        data_type = encoding_params.data_type
        if data_type is None:
            data_type = BinaryDataTypeAccession.FLOAT_64  # Default to float64 if not specified

        comp = encoding_params.compression
        if comp is None:
            comp = CompressionTypeAccessions.NO_COMPRESSION

        return self._decode(EncodingParameters(encoding_params.data, data_type, comp))

    def _decode(
        self,
        encoding_params: EncodingParameters,
    ) -> NDArray[np.float64] | None:
        """Decode base64 encoded and compressed binary data to numpy array."""

        data, data_type, comp = encoding_params

        if data is None:
            raise ValueError("Decoded binary data is None")

        out_data: bytes = b64dec(data)

        if len(out_data) == 0:
            raise ValueError("Decoded binary data is empty.")

        def decode_to_numpy(data: bytes) -> NDArray[np.float64]:
            numpy_dtype = BINARY_DECODE_DTYPES.get(data_type, None)

            if numpy_dtype is None:
                # warning and try to proceed
                logger.warning(f"Unknown data type {data_type}, attempting to decode as float64.")
                numpy_dtype = "float64"
            return np.frombuffer(data, dtype=numpy_dtype).astype(np.float64)

        match comp:
            case CompressionTypeAccessions.BYTE_SHUFFLED_ZSTD:
                raise NotImplementedError("BYTE_SHUFFLED_ZSTD compression is not yet implemented.")
            case CompressionTypeAccessions.MS_NUMPRESS_SHORT_LOGGED_FLOAT:
                return MSDecoder.decode_slof(out_data)
            case CompressionTypeAccessions.TRUNCATION_LINEAR_PREDICTION_ZLIB:
                raise NotImplementedError(
                    "TRUNCATION_LINEAR_PREDICTION_ZLIB compression is not yet implemented."
                )
            case CompressionTypeAccessions.ZLIB_COMPRESSION:
                return decode_to_numpy(MSDecoder.decode_zlib(out_data))
            case CompressionTypeAccessions.NO_COMPRESSION:
                return decode_to_numpy(out_data)
            case CompressionTypeAccessions.DICTIONARY_ENCODED_ZSTD:
                raise NotImplementedError(
                    "DICTIONARY_ENCODED_ZSTD compression is not yet implemented."
                )
            case CompressionTypeAccessions.MS_NUMPRESS_LINEAR_PREDICTION_ZLIB:
                return MSDecoder.decode_linear(MSDecoder.decode_zlib(out_data))
            case CompressionTypeAccessions.TRUNCATION_ZLIB:
                return decode_to_numpy(MSDecoder.decode_zlib(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_SHORT_LOGGED_FLOAT_ZLIB:
                return MSDecoder.decode_slof(MSDecoder.decode_zlib(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_LINEAR_PREDICTION_ZSTD:
                return MSDecoder.decode_linear(MSDecoder.decode_ztsd(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_POSITIVE_INTEGER_ZLIB:
                return MSDecoder.decode_pic(MSDecoder.decode_zlib(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_SHORT_LOGGED_FLOAT_ZSTD:
                return MSDecoder.decode_slof(MSDecoder.decode_ztsd(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_LINEAR_PREDICTION:
                return MSDecoder.decode_linear(out_data)
            case CompressionTypeAccessions.MS_NUMPRESS_POSITIVE_INTEGER:
                return MSDecoder.decode_pic(out_data)
            case CompressionTypeAccessions.TRUNCATION_DELTA_PREDICTION_ZLIB:
                raise NotImplementedError(
                    "TRUNCATION_DELTA_PREDICTION_ZLIB compression is not yet implemented."
                )
            case CompressionTypeAccessions.ZSTD_COMPRESSION:
                return decode_to_numpy(MSDecoder.decode_ztsd(out_data))
            case CompressionTypeAccessions.MS_NUMPRESS_POSITIVE_INTEGER_ZSTD:
                return MSDecoder.decode_pic(MSDecoder.decode_ztsd(out_data))
            case _:
                # try no compression
                logger.warning(f"Unknown compression type: {comp}, attempting no compression decode.")
                try:
                    return decode_to_numpy(out_data)
                except Exception:
                    logger.error(f"Decoding failed for unknown compression type: {comp}")
                    raise ValueError(f"Unsupported compression type: {comp}")
                
        logger.error("Decoding failed for unknown reasons.")
        raise RuntimeError("Decoding failed for unknown reasons. Should not reach here.")

    def to_string(
        self, encoding: str = EncodingFormat.LATIN1, method: str = EncodingFormat.XML
    ) -> Any:
        """Return string representation of the XML element in specified encoding and format."""
        return ElementTree.tostring(self.element, encoding=encoding, method=method)  # type: ignore[call-overload]

    @cached_property
    def polarity(self) -> str:
        """Get polarity (positive / negative / or unknown scan)."""

        if ScanPolarity.POSITIVE_SCAN in self.accessions:
            return "positive"
        elif ScanPolarity.NEGATIVE_SCAN in self.accessions:
            return "negative"
        else:
            return "unknown"

    @property
    def positive_scan(self) -> bool:
        """Check if chromatogram is a positive scan."""
        return self.polarity == "positive"

    @property
    def negative_scan(self) -> bool:
        """Check if chromatogram is a negative scan."""
        return self.polarity == "negative"
