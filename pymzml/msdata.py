#!/usr/bin/env python3
# -*- coding: latin-1 -*-
"""
The MsData class offers a base class for mass spectrometry data.
It provides common functionality for both Spectrum and Chromatogram classes.
"""

# Python mzML module - pymzml
# Copyright (C) 2010-2019 M. Kösters, C. Fufezan
#     The MIT License (MIT)

#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction, including without limitation the rights
#     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#     copies of the Software, and to permit persons to whom the Software is
#     furnished to do so, subject to the following conditions:

#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.

#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.


import re
import xml.etree.ElementTree as ElementTree
import zlib
from base64 import b64decode as b64dec
from struct import unpack
from typing import Optional, List, Tuple, Dict, Union, Callable, Any

try:
    import numpy as np
    from numpy.typing import NDArray
    _HAS_NUMPY = True
except (ImportError, ModuleNotFoundError):
    _HAS_NUMPY = False
    np = None  # type: ignore
    NDArray = None  # type: ignore

from .obo import OboTranslator


class MsData(object):
    """
    General base class for mass spectrometry data handling.
    Provides common functionality for both Spectrum and Chromatogram classes.
    """

    def __init__(
        self,
        element: Optional[ElementTree.Element] = None,
        measured_precision: float = 5e-6,
        *,
        obo_version: Optional[str] = None,
    ) -> None:
        """
        Initialize MsData base class.

        Arguments:
            element: XML ElementTree element containing the data
            measured_precision: Measurement precision in ppm (e.g., 5e-6 for 5 ppm)
            obo_version: OBO version string (optional)
        """
        # Core attributes
        self.element: Optional[ElementTree.Element] = element
        self._measured_precision: float = measured_precision
        self.internal_precision: int = int(round(50000.0 / (measured_precision * 1e6)))
        self.obo_translator: OboTranslator = OboTranslator.from_cache(obo_version)
        self.noise_level_estimate: Dict[str, float] = {}
        
        # XML namespace
        self.ns: str = ""
        if self.element is not None:
            match = re.match(r"\{.*\}", element.tag)
            self.ns = match.group(0) if match else ""
        
        # Data arrays (lazily loaded)
        self._mz: Optional[Union['NDArray', Tuple]] = None
        self._i: Optional[Union['NDArray', Tuple]] = None
        self._time: Optional[Union['NDArray', Tuple]] = None
        
        # Other common attributes
        self._profile: Optional[Union[List, 'NDArray', bool]] = None
        self.accessions: Dict[str, str] = {}
        
        # Set up decode and array functions based on numpy availability
        if _HAS_NUMPY:
            self._decode: Callable = self._decode_to_numpy
            self._array: Callable = np.array
        else:
            self._decode: Callable = self._decode_to_tuple
            self._array: Callable = list

    def _read_accessions(self) -> None:
        """Set all required variables for this spectrum."""
        self.accessions: Dict[str, str] = {}
        if self.element is None:
            raise ValueError("ElementTree element is None.")
        for element in self.element.iter():
            accession: Optional[str] = element.get("accession")
            name: Optional[str] = element.get("name")
            if accession is not None:
                self.accessions[name] = accession
        if "profile spectrum" in self.accessions.keys():
            self._profile: bool = True

    def get_element_by_name(self, name: str) -> Optional[ElementTree.Element]:
        """
        Get element from the original tree by it's unit name.

        Arguments:
            name (str): unit name of the mzml element.

        Keyword Arguments:
            obo_version (str, optional): obo version number.

        """
        iterator = self.element.iter()
        return_ele: Optional[ElementTree.Element] = None
        for ele in iterator:
            if ele.get("name", default=None) == name:
                return_ele = ele
                break
        return return_ele

    def get_element_by_path(self, hooks: List[str]) -> Optional[List[ElementTree.Element]]:
        """
        Find elements in spectrum by its path.

        Arguments:
            hooks (list): list of parent elements for the target element.

        Returns:
            elements (list): list of XML objects
            found in the path

        Example:

            To access cvParam in scanWindow tag:

            >>> spec.get_element_by_path(['scanList', 'scan', 'scanWindowList',
            ...     'scanWindow', 'cvParam'])

        """
        return_ele: Optional[List[ElementTree.Element]] = None
        if len(hooks) > 0:
            path_array: List[str] = ["."]
            for hook in hooks:
                path_array.append("{ns}{hook}".format(ns=self.ns, hook=hook))
            path: str = "/".join(path_array)
            return_ele = self.element.findall(path)

        return return_ele

    def _register(self, decoded_tuple: Tuple[str, Union['NDArray', Tuple]]) -> None:
        d_type, array = decoded_tuple
        if d_type == "mz":
            self._mz: Union['NDArray', Tuple] = array
        elif d_type == "i":
            self._i: Union['NDArray', Tuple] = array
        elif d_type == "time":
            self._time: Union['NDArray', Tuple] = array
        else:
            raise Exception("Unknown data Type ({0})".format(d_type))

    def _get_encoding_parameters(self, array_type: str) -> Tuple[bytes, str, Optional[str], List[str]]:
        """
        Find the correct parameter for decoding and return them as tuple.

        Arguments:
            array_type (str): data type of the array, e.g. m/z, time or
                intensity
        Returns:
            data (bytes)         : encoded data
            d_array_length (str) : length of the data array
            d_type (str)         : data type (e.g., "32-bit float")
            comp (List[str])     : compression methods
        """
        if self.element is None:
            raise ValueError("ElementTree element is None.")

        # Try to find binary data array by name first, then by value
        b_data_string = f"./{self.ns}binaryDataArrayList/{self.ns}binaryDataArray/{self.ns}cvParam[@name='{array_type}']/.."
        b_data_array = self.element.find(b_data_string)
        
        if b_data_array is None:
            # Try non-standard data array with value attribute
            b_data_string = f"./{self.ns}binaryDataArrayList/{self.ns}binaryDataArray/{self.ns}cvParam[@value='{array_type}']/.."
            b_data_array = self.element.find(b_data_string)

        # Handle case where no binary data array is found
        if b_data_array is None:
            return (b"", "0", "64-bit float", [])

        # Extract compression methods
        comp: List[str] = []
        numpress_encoding = False
        for cvParam in b_data_array.iterfind(f"./{self.ns}cvParam"):
            param_name = cvParam.get("name", "")
            if "compression" in param_name:
                comp.append(param_name)
                if "numpress" in param_name.lower():
                    numpress_encoding = True
        
        # Get array length
        d_array_length = self.element.get("defaultArrayLength", "0")
        
        # Determine data type
        d_type: Optional[str] = None
        if not numpress_encoding:
            d_type = self._find_data_type(b_data_array)
        
        # Extract binary data
        data_element = b_data_array.find(f"./{self.ns}binary")
        data = b""
        if data_element is not None and data_element.text:
            data = data_element.text.encode("utf-8")
        
        return (data, d_array_length, d_type, comp)
    
    def _find_data_type(self, b_data_array: ElementTree.Element) -> Optional[str]:
        """
        Find the data type from the binary data array element.
        
        Arguments:
            b_data_array: Binary data array XML element
            
        Returns:
            Data type name (e.g., "32-bit float") or None if not found
        """
        # List of data types to check, in order of preference
        data_types = [
            "32-bit float",
            "64-bit float",
            "32-bit integer",
            "64-bit integer",
            "null-terminated ASCII string",
        ]
        
        for data_type in data_types:
            try:
                accession = self.obo_translator[data_type]["id"]
                element = b_data_array.find(f"./{self.ns}cvParam[@accession='{accession}']")
                if element is not None:
                    return element.get("name")
            except (KeyError, TypeError):
                # Data type not found in obo_translator, try next one
                continue
        
        # Default to 64-bit float if nothing found
        return "64-bit float"

    @property
    def measured_precision(self) -> float:
        """
        Set the measured and internal precision.

        Returns:
            value (float): measured Precision (e.g. 5e-6)
        """
        return self._measured_precision

    @measured_precision.setter
    def measured_precision(self, value: float) -> None:
        self._measured_precision: float = value
        self.internal_precision: int = int(round(50000.0 / (value * 1e6)))
        return

    def _decode_to_numpy(self, data: bytes, d_array_length: str, data_type: str, comp: List[str]) -> 'NDArray':
        """
        Decode the b64 encoded and packed strings from data as numpy arrays.

        Returns:
            data (np.ndarray): Returns the unpacked data as a tuple. Returns an
                               empty list if there is no raw data or raises an
                               exception if data could not be decoded.

        d_array_length just for compatibility
        """
        out_data: Union[bytes, 'NDArray'] = b64dec(data)
        if len(out_data) != 0:
            if "zlib" in comp or "zlib compression" in comp:
                out_data = zlib.decompress(out_data)
            if (
                "ms-np-linear" in comp
                or "ms-np-pic" in comp
                or "ms-np-slof" in comp
                or "MS-Numpress linear prediction compression" in comp
                or "MS-Numpress short logged float compression" in comp
            ):
                out_data = self._decodeNumpress_to_array(out_data, comp)
            if data_type == "32-bit float":
                # one character code may be sufficient too (f)
                f_type = np.float32
                out_data = np.frombuffer(out_data, f_type)
            elif data_type == "64-bit float":
                # one character code may be sufficient too (d)
                f_type = np.float64
                out_data = np.frombuffer(out_data, f_type)
            elif data_type == "32-bit integer":
                # one character code may be sufficient too (i)
                i_type = np.int32
                out_data = np.frombuffer(out_data, i_type)
            elif data_type == "64-bit integer":
                # one character code may be sufficient too (l)
                i_type = np.int64
                out_data = np.frombuffer(out_data, i_type)
            # TODO elif data_type == "null-terminated ASCII string":
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        else:
            out_data = np.array([])
        return out_data

    def _decode_to_tuple(self, data: bytes, d_array_length: str, float_type: str, comp: List[str]) -> Union[Tuple, List]:
        """
        Decode b64 encoded and packed strings.

        Returns:
            data (tuple): Returns the unpacked data as a tuple.
                Returns an empty list if there is no raw data or
                raises an exception if data could not be decoded.
        """
        dec_data: bytes = b64dec(data)
        ret_data: Union[Tuple, List]
        
        if len(dec_data) != 0:
            if "zlib" in comp or "zlib compression" in comp:
                dec_data = zlib.decompress(dec_data)
            if set(["ms-np-linear", "ms-np-pic", "ms-np-slof"]) & set(comp):
                self._decodeNumpress(data, comp)
            # else:
            #     print(
            #         'New data compression ({0}) detected, cant decompress'.format(
            #             comp
            #         )
            #     )
            #     sys.exit(1)
            f_type: str
            if float_type == "32-bit float":
                f_type = "f"
            elif float_type == "64-bit float":
                f_type = "d"
            fmt: str = "{endian}{array_length}{float_type}".format(
                endian="<", array_length=d_array_length, float_type=f_type
            )
            ret_data = unpack(fmt, dec_data)
        else:
            ret_data = []
        return ret_data

    def _decodeNumpress_to_array(self, data: bytes, compression: List[str]) -> 'NDArray':
        """
        Decode golomb-rice encoded data (aka numpress encoded data).

        Arguments:
            data (str)        : Encoded data string
            compression (str) : Decompression algorithm to be used
                (valid are 'ms-np-linear', 'ms-np-pic', 'ms-np-slof')

        Returns:
            array (list): Returns the unpacked data as an array of floats.

        """
        result: 'NDArray' = []
        comp_ms_tags: List[str] = [self.calling_instance.OT[comp]["id"] for comp in compression]
        data_array: 'NDArray' = np.frombuffer(data, dtype=np.uint8)
        if "MS:1002312" in comp_ms_tags:
            from .decoder import MSDecoder

            result = MSDecoder.decode_linear(data_array)
        elif "MS:1002313" in comp_ms_tags:
            from .decoder import MSDecoder

            result = MSDecoder.decode_pic(data_array)
        elif "MS:1002314" in comp_ms_tags:
            from .decoder import MSDecoder

            result = MSDecoder.decode_slof(data_array)
        return result

    def _median(self, data: Union[List[float], 'NDArray']) -> float:
        """
        Compute median.

        Arguments:
            data (list): list of numeric values

        Returns:
            median (float): median of the input data
        """
        return float(np.median(data))

    def to_string(self, encoding: str = "latin-1", method: str = "xml") -> bytes:
        """
        Return string representation of the xml element the
        spectrum was initialized with.

        Keyword Arguments:
            encoding (str) : text encoding of the returned string.\n
                             Default is latin-1.
            method (str)   : text format of the returned string.\n
                             Default is xml, alternatives are html and text.

        Returns:
            element (str)  : xml string representation of the spectrum.
        """
        return ElementTree.tostring(self.element, encoding=encoding, method=method)