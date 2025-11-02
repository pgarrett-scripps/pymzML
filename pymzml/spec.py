#!usr/bin/env python3
# -*- coding: latin-1 -*-
"""
The spectrum class offers a python object for mass spectrometry data.
The spectrum object holds the basic information of the spectrum and offers
methods to interrogate properties of the spectrum.
Data, i.e. mass over charge (m/z) and intensity decoding is performed on demand
and can be accessed via their properties, e.g. :py:attr:`~pymzml.spec.Spectrum.peaks`.

The Spectrum class is used in the :py:class:`~pymzml.run.Reader` class.
There each spectrum is accessible as a spectrum object.

Theoretical spectra can also be created using the setter functions.
For example, m/z values, intensities, and peaks can be set by the
corresponding properties: :py:attr:`pymzml.spec.Spectrum.mz`,
:py:attr:`pymzml.spec.Spectrum.i`, :py:attr:`pymzml.spec.Spectrum.peaks`.

Similar to the spectrum class, the chromatogram class allows interrogation
with profile data (time, intensity) in an total ion chromatogram.
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

import math
import re
import sys
import warnings
import xml.etree.ElementTree as ElementTree
import zlib
from base64 import b64decode as b64dec
from collections import defaultdict as ddict
from functools import lru_cache
from operator import itemgetter as itemgetter
from struct import unpack
from typing import Optional, List, Tuple, Dict, Any, Union, Set

try:
    import numpy as np
    from numpy.typing import NDArray
    HAS_NUMPY = True
except (ImportError, ModuleNotFoundError):
    HAS_NUMPY = False
    np = None
    NDArray = None  # type: ignore

try:
    DECON_DEP = True
    from ms_deisotope.deconvolution import deconvolute_peaks
    from ms_peak_picker import simple_peak
except (ImportError, ModuleNotFoundError) as e:
    DECON_DEP = False
    pass
from . import regex_patterns
from .decoder import MSDecoder
from .obo import OboTranslator

PROTON = 1.00727646677
ISOTOPE_AVERAGE_DIFFERENCE = 1.002

# Import Chromatogram from chromatogram.py for backward compatibility
# Import MsData from msdata.py
from .msdata import MsData


class MS_Spectrum(MsData):
    """
    General spectrum class for data handling.
    This class is kept for backward compatibility.
    """

    def _read_accessions(self):
        """Set all required variables for this spectrum."""
        self.accessions = {}
        if self.element is None:
            raise ValueError("Spectrum element is None.")
        for element in self.element.iter():
            accession = element.get("accession")
            name = element.get("name")
            if accession is not None:
                self.accessions[name] = accession
        if "profile spectrum" in self.accessions.keys():
            self._profile = True

    def get_element_by_name(self, name: str) -> Optional[ElementTree.Element]:
        """
        Get element from the original tree by it's unit name.

        Arguments:
            name (str): unit name of the mzml element.

        Keyword Arguments:
            obo_version (str, optional): obo version number.

        """
        if self.element is None:
            raise ValueError("Spectrum element is None.")
        iterator = self.element.iter()
        return_ele = None
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
        return_ele = None
        if len(hooks) > 0:
            path_array = ["."]
            for hook in hooks:
                path_array.append("{ns}{hook}".format(ns=self.ns, hook=hook))
            path = "/".join(path_array)
            if self.element is None:
                raise ValueError("Spectrum element is None.")
            return_ele = self.element.findall(path)

        return return_ele

    def _register(self, decoded_tuple: Tuple[str, Union[NDArray, Tuple]]) -> None:
        d_type, array = decoded_tuple
        if d_type == "mz":
            self._mz = array
        elif d_type == "i":
            self._i = array
        elif d_type == "time":
            self._time = array
        else:
            raise Exception("Unknown data Type ({0})".format(d_type))

    def _get_encoding_parameters(self, array_type: str) -> Tuple[bytes, str, Optional[str], List[str]]:
        """
        Find the correct parameter for decoding and return them as tuple.

        Arguments:
            array_type (str): data type of the array, e.g. m/z, time or
                intensity
        Returns:
            data (str)           : encoded data
            comp (str)           : compression method
            d_type (str)         : data type
            d_array_length (str) : length of the data array
        """
        numpress_encoding = False

        b_data_string = "./{ns}binaryDataArrayList/{ns}binaryDataArray/{ns}cvParam[@name='{name}']/..".format(
            ns=self.ns, name=array_type
        )
        float_type_string = "./{ns}cvParam[@accession='{Acc}']"

        b_data_array = self.element.find(b_data_string)
        if not b_data_array:
            # non-standard data array
            b_data_string = "./{ns}binaryDataArrayList/{ns}binaryDataArray/{ns}cvParam[@value='{value}']/..".format(
                ns=self.ns, value=array_type
            )
            b_data_array = self.element.find(b_data_string)

        comp = []
        if b_data_array:
            for cvParam in b_data_array.iterfind("./{ns}cvParam".format(ns=self.ns)):
                if "compression" in cvParam.get("name"):
                    if "numpress" in cvParam.get("name").lower():
                        numpress_encoding = True
                    comp.append(cvParam.get("name"))
                d_array_length = self.element.get("defaultArrayLength")
            if not numpress_encoding:
                try:
                    # 32-bit float
                    d_type = b_data_array.find(
                        float_type_string.format(
                            ns=self.ns,
                            Acc=self.obo_translator["32-bit float"]["id"],
                        )
                    ).get("name")
                except:
                    try:
                        # 64-bit Float
                        d_type = b_data_array.find(
                            float_type_string.format(
                                ns=self.ns,
                                Acc=self.obo_translator["64-bit float"]["id"],
                            )
                        ).get("name")
                    except:
                        try:
                            # 32-bit integer
                            d_type = b_data_array.find(
                                float_type_string.format(
                                    ns=self.ns,
                                    Acc=self.obo_translator["32-bit integer"]["id"],
                                )
                            ).get("name")
                        except:
                            try:
                                # 64-bit integer
                                d_type = b_data_array.find(
                                    float_type_string.format(
                                        ns=self.ns,
                                        Acc=self.obo_translator["64-bit integer"]["id"],
                                    )
                                ).get("name")
                            except:
                                # null-terminated ASCII string
                                d_type = b_data_array.find(
                                    float_type_string.format(
                                        ns=self.ns,
                                        Acc=self.obo_translator[
                                            "null-terminated ASCII string"
                                        ]["id"],
                                    )
                                ).get("name")
            else:
                # compression is numpress, dont need data type here
                d_type = None
            data = b_data_array.find("./{ns}binary".format(ns=self.ns))
            if data is not None:
                data = data.text
        else:
            data = None
            d_array_length = 0
            d_type = "64-bit float"
        if data is not None:
            data = data.encode("utf-8")
        else:
            data = ""
        return (data, d_array_length, d_type, comp)

    @property
    def measured_precision(self):
        """
        Set the measured and internal precision.

        Returns:
            value (float): measured Precision (e.g. 5e-6)
        """
        return self._measured_precision

    @measured_precision.setter
    def measured_precision(self, value):
        self._measured_precision = value
        self.internal_precision = int(round(50000.0 / (value * 1e6)))
        return

    def _decode_to_numpy(self, data, d_array_length, data_type, comp):
        """
        Decode the b64 encoded and packed strings from data as numpy arrays.

        Returns:
            data (np.ndarray): Returns the unpacked data as a tuple. Returns an
                               empty list if there is no raw data or raises an
                               exception if data could not be decoded.

        d_array_length just for compatibility
        """
        out_data = b64dec(data)
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

    def _decode_to_tuple(self, data, d_array_length, float_type, comp):
        """
        Decode b64 encoded and packed strings.

        Returns:
            data (tuple): Returns the unpacked data as a tuple.
                Returns an empty list if there is no raw data or
                raises an exception if data could not be decoded.
        """
        dec_data = b64dec(data)
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
            if float_type == "32-bit float":
                f_type = "f"
            elif float_type == "64-bit float":
                f_type = "d"
            fmt = "{endian}{array_length}{float_type}".format(
                endian="<", array_length=d_array_length, float_type=f_type
            )
            ret_data = unpack(fmt, dec_data)
        else:
            ret_data = []
        return ret_data

    def _decodeNumpress_to_array(self, data: bytes, compression: List[str]) -> List[float]:
        """
        Decode golomb-rice encoded data (aka numpress encoded data).

        Arguments:
            data (str)        : Encoded data string
            compression (str) : Decompression algorithm to be used
                (valid are 'ms-np-linear', 'ms-np-pic', 'ms-np-slof')

        Returns:
            array (list): Returns the unpacked data as an array of floats.

        """
        result: List[float] = []
        comp_ms_tags = [self.calling_instance.OT[comp]["id"] for comp in compression]
        data = np.frombuffer(data, dtype=np.uint8)
        if "MS:1002312" in comp_ms_tags:
            result = MSDecoder.decode_linear(data)
        elif "MS:1002313" in comp_ms_tags:
            result = MSDecoder.decode_pic(data)
        elif "MS:1002314" in comp_ms_tags:
            result = MSDecoder.decode_slof(data)
        return result

    def _median(self, data):
        """
        Compute median.

        Arguments:
            data (list): list of numeric values

        Returns:
            median (float): median of the input data
        """
        return np.median(data)

    def to_string(self, encoding: str = "latin-1", method: str = "xml") -> Tuple[str, List]:
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


class Spectrum(MsData):
    """
    Spectrum class which inherits from class :py:attr:`pymzml.spec.MS_Spectrum`

    Arguments:
        element (xml.etree.ElementTree.Element): spectrum as xml element

    Keyword Arguments:
        measured_precision (float): in ppm, i.e. 5e-6 equals to 5 ppm.

    """

    def __init__(
        self,
        element: ElementTree.Element = ElementTree.Element(""),
        measured_precision: float = 5e-6,
        *,
        obo_version: Optional[str] = None,
    ) -> None:
        # Call parent class __init__
        super().__init__(element, measured_precision, obo_version=obo_version)
        
        # Spectrum-specific attributes
        self._centroided_peaks = None
        self._centroided_peaks_sorted_by_i = None
        self._extreme_values = None
        self._ID = None
        self._id_dict = None
        self._index = None
        self._ms_level = None
        self._mz = None
        self._peak_dict = {
            "raw": None,
            "centroided": None,
            "reprofiled": None,
            "deconvoluted": None,
        }
        self._selected_precursors = None
        self.reprofiled = False
        self._reprofiled_peaks = None
        self._scan_time = None
        self._scan_time_unit = None
        self._scan_time_in_minutes = None
        self._t_mass_set = None
        self._t_mz_set = None
        self._TIC = None
        self._precursors = None
        self._transformed_mass_with_error = None
        self._transformed_mz_with_error = None
        self._transformed_peaks = None
        self._ms_deisotop_warning_printed = False

    def __del__(self) -> None:
        """
        Clear self.element to limit RAM usage
        """
        if self.element is not None:
            self.element.clear()

    def __add__(self, other_spec: 'Spectrum') -> 'Spectrum':
        """
        Adds two pymzml spectra

        Arguments:
            other_spec (Spectrum): spectrum to add to the current spectrum

        Returns:
            self (Spectrum): reference to the edited spectrum

        Example:

        >>> import pymzml
        >>> s = pymzml.spec.Spectrum( measuredPrescision = 20e-6 )
        >>> file_to_read = "../mzML_example_files/xy.mzML.gz"
        >>> run = pymzml.run.Reader(
        ...     file_to_read ,
        ...     MS1_Precision = 5e-6 ,
        ...     MSn_Precision = 20e-6
        ... )
        >>> for spec in run:
        ...     s += spec

        """
        assert isinstance(other_spec, Spectrum)
        if self._peak_dict["reprofiled"] is None:
            reprofiled: Dict[float, float] = self._reprofile_Peaks()
            self.set_peaks(reprofiled, "reprofiled")
        if other_spec._peak_dict["reprofiled"] is None:
            other_spec.set_peaks(other_spec._reprofile_Peaks(), "reprofiled")
        for mz, i in other_spec.peaks("reprofiled"):
            self._peak_dict["reprofiled"][mz] += i
        return self

    def __sub__(self, other_spec: 'Spectrum') -> 'Spectrum':
        """
        Subtracts two pymzml spectra.

        Arguments:
            other_spec (spec.Spectrum): spectrum to subtract from the current
                spectrum

        Returns:
            self (spec.Spectrum): returns self after other_spec was subtracted
        """
        assert isinstance(other_spec, Spectrum)
        if self._peak_dict["reprofiled"] is None:
            self.set_peaks(self._reprofile_Peaks(), "reprofiled")
        if other_spec._peak_dict["reprofiled"] is None:
            other_spec.set_peaks(other_spec._reprofile_Peaks(), "reprofiled")
        for mz, i in other_spec.peaks("reprofiled"):
            self._peak_dict["reprofiled"][mz] -= i
        self.set_peaks(None, "centroided")
        self.set_peaks(None, "raw")
        return self

    def __mul__(self, value: Union[int, float]) -> 'Spectrum':
        """
        Multiplies each intensity with a float, i.e. scales the spectrum.

        Arguments:
            value (int, float): value to multiply the intensities with

        Returns:
            self (spec.Spectrum): returns self after intensities were scaled
                by value
        """
        assert isinstance(value, (int, float))
        if self._peak_dict["raw"] is not None:
            self.set_peaks(
                np.column_stack(
                    (self.peaks("raw")[:, 0], self.peaks("raw")[:, 1] * value)
                ),
                "raw",
            )
        if self._peak_dict["centroided"] is not None:
            self.set_peaks(
                np.column_stack(
                    (self.centroided_peaks[:, 0], self.centroided_peaks[:, 1] * value)
                ),
                "centroided",
            )
        if self._peak_dict["reprofiled"] is not None:
            for mz in self._peak_dict["reprofiled"].keys():
                self._peak_dict["reprofiled"][mz] *= float(value)
        return self

    def __truediv__(self, value: Union[int, float]) -> 'Spectrum':
        """
        Divides each intensity by a float, i.e. scales the spectrum.

        Arguments:
            value (int, float): value to divide the intensities by

        Returns:
            self (spec.Spectrum): returns self after intensities were scaled
                by value.
        """
        if self._peak_dict["reprofiled"] is not None:
            for mz, i in self.peaks("reprofiled"):
                self._peak_dict["reprofiled"][mz] /= float(value)
        if self._peak_dict["raw"] is not None:
            if len(self._peak_dict["raw"]) != 0:
                self.set_peaks(
                    np.column_stack(
                        (
                            self.peaks("raw")[:, 0],
                            self.peaks("raw")[:, 1] / float(value),
                        )
                    ),
                    "raw",
                )
        if self._peak_dict["centroided"] is not None:
            peaks = self._peak_dict["centroided"]
            scaled_peaks = peaks[:, 1] / value
            peaks[:, 1] = scaled_peaks
            self._peak_dict["centroided"] = peaks
        return self

    def __div__(self, value: Union[int, float]) -> 'Spectrum':
        """
        Integer division is the same as __truediv__ for this class
        """
        return self.__truediv__(value)

    def __repr__(self) -> str:
        """
        Returns representative string for a spectrum object class
        """
        return "<__main__.Spectrum object with native ID {0} at {1}>".format(
            self.ID, hex(id(self))
        )

    def __str__(self) -> str:
        """
        Returns representative string for a spectrum object class
        """
        return "<__main__.Spectrum object with native ID {0} at {1}>".format(
            self.ID, hex(id(self))
        )

    @lru_cache()
    def __getitem__(self, accession: str) -> Optional[Union[str, float, bool, List[Union[str, float]]]]:
        """
        Access spectrum XML information by tag name

        Args:
            accession(str): name of the XML tag

        Returns:
            value (float or str): value of the XML tag
        """
        #  TODO implement cache???
        if accession == "id":
            return_val = self.ID
        else:
            if not accession.startswith("MS:"):
                try:
                    accession = self.obo_translator[accession]["id"]
                except TypeError:
                    accession = "---"
            search_string = './/*[@accession="{0}"]'.format(accession)
            elements = []
            for x in self.element.iterfind(search_string):
                val = x.attrib.get("value", "")
                try:
                    val = float(val)
                except:
                    pass
                elements.append(val)

            if len(elements) == 0:
                return_val = None
            elif len(elements) == 1:
                return_val = elements[0]
            else:
                return_val = elements
        if return_val == "":
            return_val = True
        return return_val

    def get(self, acc: str, default: Any = None) -> Any:
        """Mimic dicts get function.

        Args:
            acc (str): accession or obo tag to return
            default (None, optional): default value if acc is not found
        """
        val: Any = self[acc]
        if val is None:
            val = default
        return val

    def __contains__(self, value: str) -> bool:
        """Check if MS tag or name can be found in spectrum.

        Args:
            value (str): MS tag or OBO name

        Returns:
            bool
        """
        r = False
        if self[value] is not None:
            r = True
        return r

    @property
    def measured_precision(self) -> float:
        """
        Sets the measured and internal precision

        Returns:
            value (float): measured precision (e.g. 5e-6)
        """
        return self._measured_precision

    @measured_precision.setter
    def measured_precision(self, value: float) -> None:
        self._measured_precision = value
        self.internal_precision = int(round(50000.0 / (value * 1e6)))
        return

    @property
    def t_mz_set(self) -> Set[int]:
        """
        Creates a set of integers out of transformed m/z values
        (including all values in the defined imprecision).
        This is used to accelerate has_peak function and similar.

        Returns:
            t_mz_set (set): set of transformed m/z values
        """
        if self._t_mz_set is None:
            self._t_mz_set = set()
            for mz, i in self.peaks("centroided"):
                self._t_mz_set |= set(
                    range(
                        int(
                            round(
                                (mz - (mz * self.measured_precision))
                                * self.internal_precision
                            )
                        ),
                        int(
                            round(
                                (mz + (mz * self.measured_precision))
                                * self.internal_precision
                            )
                        )
                        + 1,
                    )
                )
        return self._t_mz_set

    @property
    def transformed_mz_with_error(self) -> Dict[int, List[Tuple[float, float]]]:
        """
        Returns transformed m/z value with error

        Returns:
            tmz values (dict): Transformed m/z values in dictionary\n
                {\n
                m/z_with_error : [(m/z,intensity), ...], ...\n
                }\n
        """
        if self._transformed_mz_with_error is None:
            self._transformed_mz_with_error = ddict(list)
            for mz, i in self.peaks("centroided"):
                for t_mz_with_error in range(
                    int(
                        round(
                            (mz - (mz * self.measured_precision))
                            * self.internal_precision
                        )
                    ),
                    int(
                        round(
                            (mz + (mz * self.measured_precision))
                            * self.internal_precision
                        )
                    )
                    + 1,
                ):
                    self._transformed_mz_with_error[t_mz_with_error].append((mz, i))
        return self._transformed_mz_with_error

    @property
    def transformed_peaks(self) -> List[Tuple[int, float]]:
        """
        m/z value is multiplied by the internal precision.

        Returns:
            Transformed peaks (list): Returns a list of peaks (tuples of mz and
            intensity).
            Float m/z values are adjusted by the internal precision
            to integers.
        """
        if self._transformed_peaks is None:
            self._transformed_peaks = [
                (self.transform_mz(mz), i) for mz, i in self.peaks("centroided")
            ]
        return self._transformed_peaks

    @property
    def TIC(self) -> float:
        """
        Property to access the total ion current for this spectrum.

        Returns:
            TIC (float): Total Ion Current of the spectrum.
        """
        if self._TIC is None:
            self._TIC = float(
                self.element.find(
                    "./{ns}cvParam[@accession='MS:1000285']".format(ns=self.ns)
                ).get("value")
            )  # put hardcoded MS tags in minimum.py???
        return self._TIC

    @property
    def ID(self) -> Optional[Union[int, str]]:
        """
        Access the native id (last number in the id attribute) of the spectrum.

        Returns:
            ID (str): native ID of the spectrum
        """
        if self._ID is None:
            if self.element is not None:
                match = regex_patterns.SPECTRUM_ID_PATTERN.search(
                    self.element.get("id", None)
                )
                if match:
                    try:
                        self._ID = int(match.group(1))
                    except ValueError:
                        self._ID = match.group(1)
                else:
                    self._ID = self.element.get("id")
        return self._ID

    @property
    def id_dict(self) -> Dict[str, Union[str, int]]:
        """
        Access to all entries stored the id attribute of a spectrum.

        Returns:
            id_dict (dict): key value pairs for all entries in id attribute of a spectrum
        """
        if self._id_dict is None:
            tuples = []
            matches = regex_patterns.SPECTRUM_PATTERN3.findall(self.element.attrib["id"])
            if matches:
                for k, v in matches:
                    k = k.strip()
                    v = v.strip()
                    try:
                        v = int(v)
                    except ValueError:
                        pass
                    tuples.append([k, v])
                self._id_dict = dict(tuples)
            else:
                self._id_dict = {}
        return self._id_dict

    @property
    def index(self) -> Optional[Union[int, str]]:
        """
        Access the index of the spectrum.

        Returns:
            index (int): index of the spectrum

        Note:
            This does not necessarily correspond to the native spectrum ID
        """
        if self._index is None:
            self._index = self.element.get("index")
            try:
                self._index = int(self._index)
            except:
                pass
        return self._index

    @property
    def ms_level(self) -> Optional[int]:
        """
        Property to access the ms level.

        Returns:
            ms_level (int):
        """
        if self._ms_level is None:
            sub_element = self.element.find(
                ".//{ns}cvParam[@accession='MS:1000511']".format(ns=self.ns)
            )
            if sub_element is not None:
                self._ms_level = int(
                    sub_element.get("value")
                )  # put hardcoded MS tags in minimum.py???
        return self._ms_level

    @property
    def scan_time(self) -> Tuple[Optional[float], Optional[str]]:
        """
        Property to access the retention time and retention time unit.
        Please note, that we do not assume the retention time unit,
        if it is not correctly defined in the mzML.
        It is set to 'unicorns' in this case.

        Returns:
            scan_time (float):
            scan_time_unit (str):
        """
        if self._scan_time is None or self._scan_time_unit is None:
            scan_time_ele = self.element.find(
                ".//*[@accession='MS:1000016']".format(ns=self.ns)
            )
            if scan_time_ele is not None:
                self._scan_time = float(scan_time_ele.attrib.get("value"))
                self._scan_time_unit = scan_time_ele.get("unitName", "unicorns")
        return self._scan_time, self._scan_time_unit

    # @property
    def scan_time_in_minutes(self) -> Optional[float]:
        """
        Property to access the retention time in minutes.
        If the retention time unit is defined within the mzML,
        the retention time is converted into minutes and returned
        without the unit.

        Returns:
            scan_time (float):
        """
        if self._scan_time_in_minutes is None:
            self._scan_time, time_unit = self.scan_time
            if self._scan_time_unit.lower() == "millisecond":
                self._scan_time_in_minutes = self._scan_time / 1000.0 / 60.0
            if self._scan_time_unit.lower() == "second":
                self._scan_time_in_minutes = self._scan_time / 60.0
            elif self._scan_time_unit.lower() == "minute":
                self._scan_time_in_minutes = self._scan_time
            elif self._scan_time_unit.lower() == "hour":
                self._scan_time_in_minutes = self._scan_time * 60.0
            else:
                raise Exception("Time unit '{0}' unknown".format(self._scan_time_unit))
        return self._scan_time_in_minutes

    @property
    def selected_precursors(self) -> List[Dict[str, Any]]:
        """
        Property to access the selected precursors of a MS2 spectrum. Returns
        a list of dicts containing the precursors mz and, if available intensity
        and charge for each precursor.

        Returns:
            selected_precursors (list):
        """
        if self._selected_precursors is None:
            selected_precursor_mzs = self.element.findall(
                ".//*[@accession='MS:1000744']"
            )
            selected_precursor_is = self.element.findall(
                ".//*[@accession='MS:1000042']"
            )
            selected_precursor_cs = self.element.findall(
                ".//*[@accession='MS:1000041']"
            )
            precursors = self.element.findall(
                "./{ns}precursorList/{ns}precursor".format(ns=self.ns)
            )

            mz_values = []
            i_values = []
            charges = []
            ids = []
            for obj in selected_precursor_mzs:
                mz = obj.get("value")
                mz_values.append(float(mz))
            for obj in selected_precursor_is:
                i = obj.get("value")
                i_values.append(float(i))
            for obj in selected_precursor_cs:
                c = obj.get("value")
                charges.append(int(c))
            for prec in precursors:
                spec_ref = prec.get("spectrumRef")
                if spec_ref is not None:
                    ids.append(
                        regex_patterns.SPECTRUM_ID_PATTERN.search(spec_ref).group(1)
                    )
                else:
                    ids.append(None)
                # ids.append()
            self._selected_precursors = []
            for pos, mz in enumerate(mz_values):
                dict_2_save = {"mz": mz}
                for key, list_of_values in [
                    ("i", i_values),
                    ("charge", charges),
                    ("precursor id", ids),
                    ("element", precursors),
                ]:
                    try:
                        dict_2_save[key] = list_of_values[pos]
                    except:
                        continue
                self._selected_precursors.append(dict_2_save)

        return self._selected_precursors

    @property
    def precursors(self) -> List[str]:
        """
        List the precursor information of this spectrum, if available.
        Returns:
            precursor(list): list of precursor ids for this spectrum.
        """
        self.deprecation_warning(sys._getframe().f_code.co_name)
        if not self._precursors:
            precursors = self.element.findall(
                "./{ns}precursorList/{ns}precursor".format(ns=self.ns)
            )
            self._precursors = []
            for prec in precursors:
                spec_ref = prec.get("spectrumRef")
                self._precursors.append(
                    regex_patterns.SPECTRUM_ID_PATTERN.search(spec_ref).group(1)
                )
        return self._precursors

    def remove_precursor_peak(self) -> Union['NDArray', List]:
        peaks: Union['NDArray', List] = self.peaks("centroided")
        for precursor in self.selected_precursors:
            mz: float = precursor["mz"]
            hp: List[Tuple[float, float]] = self.has_peak(mz)
            if hp:
                for p in hp:
                    peaks = peaks[(peaks[:, 0] != p[0])]
        self.set_peaks(peaks, "centroided")
        self.set_peaks(peaks, "raw")
        return peaks

    @property
    def mz(self) -> Union['NDArray', Tuple, List]:
        """
        Returns the list of m/z values. If the m/z values are encoded, the
        function :func:`~spec.MS_Spectrum._decode` is used to decode the encoded data.
        The mz property can also be set, e.g. for theoretical data.
        However, it is recommended to use the peaks property to set mz and
        intensity tuples at same time.

        Returns:
            mz (list): list of m/z values of spectrum.
        """
        if self._mz is None:
            params = self._get_encoding_parameters("m/z array")
            self._mz = self._decode(*params)
        return self._mz

    @mz.setter
    def mz(self, mz_list: Union[List[float], 'NDArray']) -> None:
        """"""
        mz_list = np.array(mz_list, dtype=np.float64)
        mz_list.sort()
        self._mz = mz_list

    @property
    def i(self) -> Union['NDArray', Tuple, List]:
        """
        Returns the list of the intensity values.
        If the intensity values are encoded, the function :func:`~spec.MS_Spectrum._decode`
        is used to decode the encoded data.\n
        The i property can also be set, e.g. for theoretical data. However,
        it is recommended to use the peaks property to set mz and intensity
        tuples at same time.

        Returns
            i (list): list of intensity values from the analyzed spectrum
        """
        if self._i is None:
            params = self._get_encoding_parameters("intensity array")
            self._i = self._decode(*params)
        return self._i

    @i.setter
    def i(self, intensity_list: Union[List[float], 'NDArray']) -> None:
        self._i = intensity_list

    def peaks(self, peak_type: str) -> Union['NDArray', List[Tuple[float, float]], Dict[float, float]]:
        """
        Decode and return a list of mz/i tuples.

        Args:
            peak_type(str): currently supported types are:
                raw, centroided and reprofiled

        Returns:
            peaks (list or ndarray): list or numpy array of mz/i tuples or arrays
        """
        if self._peak_dict[peak_type] is None:
            if self._peak_dict["raw"] is None:
                mz_params = self._get_encoding_parameters("m/z array")
                i_params = self._get_encoding_parameters("intensity array")
                mz = self._decode(*mz_params)
                i = self._decode(*i_params)
                if HAS_NUMPY:
                    arr = np.stack((mz, i), axis=-1)
                else:
                    # Create list of tuples for non-numpy case
                    arr = list(zip(mz, i))
                self._peak_dict[peak_type] = arr
            if peak_type == "raw":
                pass
            elif peak_type == "centroided":
                self._peak_dict["centroided"] = self._centroid_peaks()
            elif peak_type == "reprofiled":
                self._peak_dict["reprofiled"] = self._reprofile_Peaks()
            elif peak_type == "deconvoluted":
                self._peak_dict["deconvoluted"] = self._deconvolute_peaks()
            else:
                raise KeyError

        if HAS_NUMPY and not isinstance(self._peak_dict[peak_type], np.ndarray):
            peaks = self._array(self._peak_dict[peak_type])
        else:
            peaks = self._peak_dict[peak_type]
        if peak_type == "reprofiled":
            peaks = list(self._peak_dict[peak_type].items())
            peaks.sort(key=itemgetter(0))
        return peaks

    @lru_cache()
    def get_array(self, arr_name: str) -> Optional[Union['NDArray', Tuple, List]]:
        array_params: Tuple[bytes, str, Optional[str], List[str]] = self._get_encoding_parameters(arr_name)
        array: Union['NDArray', Tuple, List] = self._decode(*array_params)
        if len(array) == 0:
            array = None
            _ = self.get_all_arrays_in_spec(not_found_array=arr_name)
        return array

    def get_tims_tof_ion_mobility(
        self, array_name: str = "mean inverse reduced ion mobility array"
    ) -> Optional[Union['NDArray', Tuple, List]]:
        arr: Optional[Union['NDArray', Tuple, List]] = self.get_array(array_name)
        if arr is None:
            _ = self.get_all_arrays_in_spec(not_found_array=array_name)
        return arr

    def get_all_arrays_in_spec(self, not_found_array: Optional[str] = None) -> List[str]:
        b_data_string: str = "./{ns}binaryDataArrayList/{ns}binaryDataArray/{ns}cvParam[@unitCvRef='MS']".format(
            ns=self.ns
        )
        b_data_arrays: List[ElementTree.Element] = self.element.findall(b_data_string)
        array_names: List[str] = [arr.attrib["name"] for arr in b_data_arrays]
        formatted_array_names: List[str] = []
        for name in array_names:
            formatted_array_names.append("\t- {name}".format(name=name))
        if not_found_array is not None:
            print(
                "Requested array ({not_found_array}) not found.\nAvailable arrays are:".format(
                    not_found_array=not_found_array
                )
            )
            print("\n".join(formatted_array_names))
        return array_names

    def _deconvolute_peaks(self, *args: Any, **kwargs: Any) -> Optional['NDArray']:
        if DECON_DEP is True:
            peaks = self.peaks("centroided")
            # pack peak matrix into expected structure
            peaks = [simple_peak(p[0], p[1], 0.01) for p in peaks]
            decon_result = deconvolute_peaks(peaks, *args, **kwargs)
            dpeaks = decon_result.peak_set
            # pack deconvoluted peak list into matrix structure
            dpeaks_mat = np.zeros((len(dpeaks), 3), dtype=float)
            for i, dp in enumerate(dpeaks):
                dpeaks_mat[i, :] = dp.neutral_mass, dp.intensity, dp.charge
            return dpeaks_mat
        else:
            if self._ms_deisotop_warning_printed is False:
                print(
                    "ms_deisotope is missing, please install using pip install ms_deisotope"
                )
                self._ms_deisotop_warning_printed = True

    def set_peaks(self, peaks: Optional[Union['NDArray', List[Tuple[float, float]], Dict[float, float]]], peak_type: str) -> None:
        """
        Assign a custom peak array of type peak_type

        Args:
            peaks(list or ndarray): list or array of mz/i values
            peak_type(str): Either raw, centroided or reprofiled

        """
        peak_type = peak_type.lower()
        # reset after changing peaks
        self._transformed_mass_with_error = None
        self._transformed_mz_with_error = None
        if peak_type == "raw":
            # if not isinstance(peaks, np.ndarray):
            #     peaks = np.array(peaks)
            self._peak_dict["raw"] = peaks
            try:
                self._mz = self.peaks("raw")[:, 0]
                self._i = self.peaks("raw")[:, 1]
            except IndexError:
                self._mz = np.array([])
                self._i = np.array([])

        elif peak_type == "centroided":
            # if not isinstance(peaks, np.ndarray):
            #     peaks = np.array(peaks)
            self._peak_dict["centroided"] = peaks
            try:
                self._mz = self.peaks("raw")[:, 0]
                self._i = self.peaks("raw")[:, 1]
            except IndexError:
                self._mz = np.array([])
                self._i = np.array([])

        elif peak_type == "reprofiled":
            try:
                self._peak_dict["reprofiled"] = peaks
            except TypeError:
                self._peak_dict["reprofiled"] = None
        elif peak_type == "deconvoluted":
            self._peak_dict["deconvoluted"] = peaks
            try:
                self._mz = self.peaks("raw")[:, 0]
                self._i = self.peaks("raw")[:, 1]
            except IndexError:
                self._mz = np.array([])
        else:
            raise Exception(
                "Peak type is not suppported\n"
                'Choose either "raw", "centroided" or "reprofiled"'
            )

    def _centroid_peaks(self) -> Union['NDArray', List[Tuple[float, float]]]:
        """
        Perform a Gauss fit to centroid the peaks for the property
        centroided_peaks.

        Returns:
            centroided_peaks (list): list of centroided m/z, i tuples
        """

        try:
            profile_ot = self.obo_translator.name.get("profile spectrum", None)
            if profile_ot is None:
                profile_ot = self.obo_translator.name.get("profile mass spectrum", None)
            acc = profile_ot["id"]
            is_profile = (
                True
                if self.element.find(
                    ".//*[@accession='{acc}']".format(ns=self.ns, acc=acc)
                )
                is not None
                else None
            )

        except (TypeError, AttributeError) as e:
            # user creadted spectrum objects without xml and calling instance cant determine if they are reprofiled or not
            is_profile = None

        if is_profile is not None or self.reprofiled:  # check if spec is a profile spec
            # Use numpy-optimized version if available, otherwise fall back to Python implementation
            if HAS_NUMPY:
                return self._centroid_peaks_numpy()
            else:
                return self._centroid_peaks_python()
        else:
            return self.peaks("raw")

    def _centroid_peaks_numpy(self) -> List[Tuple[float, float]]:
        """
        Numpy-optimized version of centroid peaks using vectorized operations.
        
        Returns:
            centroided_peaks (list): list of centroided m/z, i tuples
        """
        if self._peak_dict["reprofiled"] is not None:
            reprofiled_peaks = self.peaks("reprofiled")
            i_array = np.array([i for mz, i in reprofiled_peaks], dtype=np.float64)
            mz_array = np.array([mz for mz, i in reprofiled_peaks], dtype=np.float64)
        else:
            i_array = np.asarray(self.i, dtype=np.float64)
            mz_array = np.asarray(self.mz, dtype=np.float64)
        
        # Vectorized peak detection
        # Find local maxima where i[pos-1] < i[pos] > i[pos+1] and all > 0
        if len(i_array) < 3:
            return []
        
        # Create shifted arrays for comparison
        i_prev = i_array[:-2]  # i[pos-1]
        i_curr = i_array[1:-1]  # i[pos]
        i_next = i_array[2:]  # i[pos+1]
        
        mz_prev = mz_array[:-2]  # mz[pos-1]
        mz_curr = mz_array[1:-1]  # mz[pos]
        mz_next = mz_array[2:]  # mz[pos+1]
        
        # Find peaks: 0 < i_prev < i_curr > i_next > 0
        is_peak = (i_prev > 0) & (i_prev < i_curr) & (i_curr > i_next) & (i_next > 0)
        
        # Filter out peaks with irregular spacing (x2-x1 > (x3-x2)*10 or (x2-x1)*10 < x3-x2)
        dx1 = mz_curr - mz_prev
        dx2 = mz_next - mz_curr
        valid_spacing = ~((dx1 > dx2 * 10) | (dx1 * 10 < dx2))
        
        is_peak = is_peak & valid_spacing
        
        # Extract valid peaks
        x1 = mz_prev[is_peak]
        y1 = i_prev[is_peak]
        x2 = mz_curr[is_peak]
        y2 = i_curr[is_peak]
        x3 = mz_next[is_peak]
        y3 = i_next[is_peak]
        
        # Handle y3 == y1 case
        y3_adjusted = np.where(y3 == y1, y3 + 0.01 * y1, y3)
        
        # Vectorized Gaussian fit calculation
        # Avoid log of zero or negative and division by zero
        valid_log = (y2 > y1) & (y3_adjusted > y1) & (y1 > 0)
        
        if not np.any(valid_log):
            return []
        
        x1 = x1[valid_log]
        y1 = y1[valid_log]
        x2 = x2[valid_log]
        y2 = y2[valid_log]
        x3 = x3[valid_log]
        y3_adjusted = y3_adjusted[valid_log]
        
        # Calculate double_log = log(y2/y1) / log(y3/y1)
        with np.errstate(divide='ignore', invalid='ignore'):
            double_log = np.log(y2 / y1) / np.log(y3_adjusted / y1)
            
            # Calculate mue (mean of Gaussian)
            numerator = double_log * (x1 * x1 - x3 * x3) - x1 * x1 + x2 * x2
            denominator = 2 * (x2 - x1) - 2 * double_log * (x3 - x1)
            mue = numerator / denominator
            
            # Calculate c_squared (variance)
            c_squared_num = x2 * x2 - x1 * x1 - 2 * x2 * mue + 2 * x1 * mue
            c_squared_denom = 2 * np.log(y1 / y2)
            c_squared = c_squared_num / c_squared_denom
            
            # Calculate A (amplitude)
            A = y1 * np.exp((x1 - mue) * (x1 - mue) / (2 * c_squared))
        
        # Filter out invalid results (NaN or inf)
        valid = np.isfinite(mue) & np.isfinite(A)
        mue = mue[valid]
        A = A[valid]
        
        # Convert to list of tuples
        tmp = list(zip(mue.tolist(), A.tolist()))
        return tmp

    def _centroid_peaks_python(self) -> List[Tuple[float, float]]:
        """
        Pure Python implementation of centroid peaks (slower but no numpy dependency).
        
        Returns:
            centroided_peaks (list): list of centroided m/z, i tuples
        """
        tmp = []
        if self._peak_dict["reprofiled"] is not None:
            i_array = [i for mz, i in self.peaks("reprofiled")]
            mz_array = [mz for mz, i in self.peaks("reprofiled")]
        else:
            i_array = self.i
            mz_array = self.mz
        
        for pos, i in enumerate(i_array[:-1]):
            if pos <= 1:
                continue
            if 0 < i_array[pos - 1] < i > i_array[pos + 1] > 0:
                x1 = float(mz_array[pos - 1])
                y1 = float(i_array[pos - 1])
                x2 = float(mz_array[pos])
                y2 = float(i_array[pos])
                x3 = float(mz_array[pos + 1])
                y3 = float(i_array[pos + 1])
                if x2 - x1 > (x3 - x2) * 10 or (x2 - x1) * 10 < x3 - x2:
                    continue
                if y3 == y1:
                    y3 += 0.01 * y1

                try:
                    double_log = math.log(y2 / y1) / math.log(y3 / y1)
                    mue = (double_log * (x1 * x1 - x3 * x3) - x1 * x1 + x2 * x2) / (
                        2 * (x2 - x1) - 2 * double_log * (x3 - x1)
                    )
                    c_squarred = (
                        x2 * x2 - x1 * x1 - 2 * x2 * mue + 2 * x1 * mue
                    ) / (2 * math.log(y1 / y2))
                    A = y1 * math.exp((x1 - mue) * (x1 - mue) / (2 * c_squarred))
                except ZeroDivisionError:
                    continue
                tmp.append((mue, A))
        return tmp

    def _reprofile_Peaks(self) -> Dict[float, float]:
        """
        Performs reprofiling for property reprofiled_peaks.

        Returns:
            reprofiled_peaks (list): list of reprofiled m/z, i tuples
        """
        tmp: Dict[float, float] = ddict(int)
        for mz, i in self.peaks("centroided"):
            # Let the measured precision be 2 sigma of the signal width
            # When using normal distribution
            # FWHM = 2 sqt(2 * ln(2)) sigma = 2.3548 sigma
            s: float = mz * self.measured_precision * 2  # in before 2
            s2: float = s * s
            floor: float = mz - 5.0 * s  # Gauss curve +- 3 sigma
            ceil: float = mz + 5.0 * s
            ip: float = self.internal_precision / 4
            # more spacing, i.e. less points describing the gauss curve
            # -> faster adding
            for _ in range(int(round(floor * ip)), int(round(ceil * ip)) + 1):
                if _ % int(5) == 0:
                    a: float = float(_) / float(ip)
                    y: float = i * math.exp(-1 * ((mz - a) * (mz - a)) / (2 * s2))
                    tmp[a] += y
        self.reprofiled = True
        self.set_peaks(None, "centroided")
        return tmp

    def _mz_2_mass(self, mz: float, charge: int) -> float:
        """
        Calculate the uncharged mass for a given mz value

        Arguments:
            mz (float)  : m/z value
            charge(int) : charge

        Returns:
            mass (float): Returns mass of a given m/z value
        """
        return (mz - PROTON) * charge

    def _set_params_from_reference_group(self, ref_element: ElementTree.Element) -> None:
        ref: Optional[ElementTree.Element] = self.element.find("{ns}referenceableParamGroupRef".format(ns=self.ns))
        if ref is not None:
            ref_id: Optional[str] = ref.get("ref")
            ele: Optional[ElementTree.Element] = ref_element.find(".//*[@id='{ref}']".format(ref=ref_id, ns=self.ns))
            if ele is not None and ref_id == ele.get("id"):
                for param in ele.iter():
                    self.element.append(ele)
                    acc: Optional[str] = param.get("accession")

    # Public functions

    def reduce(self, peak_type: str = "raw", mz_range: Tuple[Optional[float], Optional[float]] = (None, None)) -> Union['NDArray', List]:
        """
        Remove all m/z values outside the given range.

        Arguments:
            mz_range (tuple): tuple of min, max values

        Returns:
            peaks (list): list of mz, i tuples in the given range.
        """
        arr = self.peaks(peak_type)
        peaks = arr[
            np.where(np.logical_and(arr[:, 0] >= mz_range[0], arr[:, 0] <= mz_range[1]))
        ]
        self.set_peaks(peaks, peak_type)
        return peaks

    def remove_noise(
        self, mode: str = "median", noise_level: Optional[float] = None, signal_to_noise_threshold: float = 1.0
    ) -> 'Spectrum':
        """
        Function to remove noise from peaks, centroided peaks and reprofiled
        peaks.

        Keyword arguments:
                mode (str): define mode for removing noise. Default = "median"
                (other modes: "mean", "mad")
            noise_level (float): noise threshold
            signal_to_noise_threshold (float): S/N threshold for a peak to be accepted

        Returns:
            reprofiled peaks (list): Returns a list with tuples of
            m/z-intensity pairs above the noise threshold

        """
        # Thanks to JD Hogan for pointing it out!
        callPeaks = self.peaks("raw")
        # callcentPeaks = self.peaks("centroided")
        if noise_level is None:
            noise_level = self.estimated_noise_level(mode=mode)
        if len(self.peaks("centroided")) != 0:
            self._peak_dict["centroided"] = self.peaks("centroided")[
                self.peaks("centroided")[:, 1] / noise_level
                >= signal_to_noise_threshold
            ]
        if len(self.peaks("raw")) != 0:
            self._peak_dict["raw"] = self.peaks("raw")[
                self.peaks("raw")[:, 1] / noise_level >= signal_to_noise_threshold
            ]
        self._peak_dict["reprofiled"] = None
        return self

    def estimated_noise_level(self, mode: str = "median") -> float:
        """
        Calculates noise threshold for function remove_noise.

        Different modes are available. Default is 'median'

        Keyword Arguments:
            mode (str): define mode for removing noise. Default = "median"
                (other modes: "mean", "mad")

        Returns:
            noise_level (float): estimate noise threshold


        """
        if len(self.peaks("centroided")) == 0:  # or is None?
            return 0

        self.noise_level_estimate = {}
        if mode not in self.noise_level_estimate.keys():
            if mode == "median":
                self.noise_level_estimate["median"] = np.median(
                    self.peaks("centroided")[:, 1]
                )
            elif mode == "mad":
                median = self.estimated_noise_level(mode="median")
                self.noise_level_estimate["mad"] = np.median(
                    abs(self.peaks("centroided")[:, 1] - median)
                )
            elif mode == "mean":
                self.noise_level_estimate["mean"] = sum(
                    self.peaks("centroided")[:, 1]
                ) / float(len(self.peaks("centroided")))
            else:
                print(
                    "Do not understand noise level estimation method call with given mode: {0}".format(
                        mode
                    )
                )
            return_value = self.noise_level_estimate[mode]
        return return_value

    def highest_peaks(self, n: int) -> Union['NDArray', List[Tuple[float, float]]]:
        """
        Function to retrieve the n-highest centroided peaks of the spectrum.

        Arguments:
            n (int): number of highest peaks to return.

        Returns:
            centroided peaks (list): list mz, i tupls with n-highest

        Example:

        >>> run = pymzml.run.Reader(
        ...     "tests/data/example.mzML.gz",
        ...      MS_precisions =  {
        ...         1 : 5e-6,
        ...         2 : 20e-6
        ...     }
        ... )
        >>> for spectrum in run:
        ...     if spectrum.ms_level == 2:
        ...         if spectrum.ID == 1770:
        ...             for mz,i in spectrum.highest_peaks(5):
        ...                print(mz, i)

        """
        if self._centroided_peaks_sorted_by_i is None:
            self._centroided_peaks_sorted_by_i = self.peaks("centroided")[
                self.peaks("centroided")[:, 1].argsort()
            ]
        return self._centroided_peaks_sorted_by_i[-n:]

    def ppm2abs(self, value: float, ppm_value: float, direction: int = 1, factor: float = 1) -> float:
        """
        Returns the value plus (or minus, dependent on direction) the
        error (measured precision ) for this value.

        Arguments:
            value (float)   : m/z value
            ppm_value (int)  : ppm value

        Keyword Arguments:
            direction (int) : plus or minus the considered m/z value.
                The argument *direction* should be 1 or -1
            factor (int)    : multiplication factor for the imprecision.
                The argument *factor* should be bigger than 0

        Returns:
            imprecision (float): imprecision for the given value

        """
        result = value + (value * (ppm_value * factor)) * direction
        return result

    def extreme_values(self, key: str) -> Tuple[float, float]:
        """
        Find extreme values, minimal and maximum m/z and intensity

        Arguments:
            key (str)       : m/z : "mz" or  intensity : "i"

        Returns:
            extrema (tuple) : tuple of minimal and maximum m/z or intensity

        """
        available_extreme_values = ["mz", "i"]
        if key not in available_extreme_values:
            print(
                "Do not understand extreme request: '{0}'; available values are: {1}".format(
                    key, available_extreme_values
                )
            )
            exit()
        if self._extreme_values is None:
            self._extreme_values = {}
        try:
            if key == "mz":
                all_mz_values = self.peaks("raw")[:, 0]
                self._extreme_values["mz"] = (all_mz_values.min(), all_mz_values.max())
                self._extreme_values["mz"] = (
                    self.peaks("raw")[:, 0].min(),
                    self.peaks("raw")[:, 0].max(),
                )
            else:
                all_i_values = self.peaks("raw")[:, 1]
                self._extreme_values["i"] = (
                    self.peaks("raw")[:, 1].min(),
                    self.peaks("raw")[:, 1].max(),
                )
        except ValueError:
            # emtpy spectrum
            self._extreme_values[key] = ()
        return self._extreme_values[key]

    def has_peak(self, mz2find: float) -> List[Tuple[float, float]]:
        """
        Checks if a Spectrum has a certain peak.
        Requires a m/z value as input and returns a list of peaks if the m/z
        value is found in the spectrum, otherwise ``[]`` is returned.
        Every peak is a tuple of m/z and intensity.

        Note:
            Multiple peaks may be found, depending on the defined precisions

        Arguments:
            mz2find (float): m/z value which should be found

        Returns:
            peaks (list): list of m/z, i tuples

        Example:

        >>> import pymzml
        >>> example_file = 'tests/data/example.mzML'
        >>> run = pymzml.run.Reader(
        ...     example_file,
        ...     MS_precisions =  {
        ...         1 : 5e-6,
        ...         2 : 20e-6
        ...     }
        ... )
        >>> for spectrum in run:
        ...     if spectrum.ms_level == 2:
        ...             peak_to_find = spectrum.has_peak(1016.5404)
        ...             print(peak_to_find)
        [(1016.5404, 19141.735187697403)]

        """
        value = self.transform_mz(mz2find)
        return self.transformed_mz_with_error[value]

    def has_overlapping_peak(self, mz: float) -> bool:
        """
        Checks if a spectrum has more than one peak for a given m/z value
        and within the measured precision

        Arguments:
            mz (float): m/z value which should be checked

        Returns:
            Boolean (bool): Returns ``True`` if a nearby peak is detected,
            otherwise ``False``
        """
        for minus_or_plus in [-1, 1]:
            target = self.ppm2abs(mz, self.measured_precision, minus_or_plus, 1)
            temp = self.has_peak(self.ppm2abs(mz, self.measured_precision))
            if temp and len(temp) > 1:
                return True
        return False

    def similarity_to(self, spec2: 'Spectrum', round_precision: int = 0) -> float:
        """
        Compares two spectra and returns cosine

        Arguments:
            spec2 (Spectrum): another pymzml spectrum that is compared to the
                current spectrum.

        Keyword Arguments:
            round_precision (int): precision mzs are rounded to, i.e. round( mz,
                round_precision )

        Returns:
            cosine (float): value between 0 and 1, i.e. the cosine between the
                two spectra.

        Note:
            Spectra data is transformed into an n-dimensional vector,
            where m/z values are binned in bins of 10 m/z and the intensities
            are added up. Then the cosine is calculated between those two
            vectors. The more similar the specs are, the closer the value is
            to 1.
        """
        assert isinstance(spec2, Spectrum), "Spectrum 2 is not a pymzML spectrum"

        vector1 = ddict(int)
        vector2 = ddict(int)
        mzs = set()
        for mz, i in self.peaks("raw"):
            vector1[round(mz, round_precision)] += i
            mzs.add(round(mz, round_precision))
        for mz, i in spec2.peaks("raw"):
            vector2[round(mz, round_precision)] += i
            mzs.add(round(mz, round_precision))

        z = 0
        n_v1 = 0
        n_v2 = 0

        for mz in mzs:
            int1 = vector1[mz]
            int2 = vector2[mz]
            z += int1 * int2
            n_v1 += int1 * int1
            n_v2 += int2 * int2
        try:
            cosine = z / (math.sqrt(n_v1) * math.sqrt(n_v2))
        except:
            cosine = 0.0
        return cosine

    def transform_mz(self, value: float) -> int:
        """
        pymzml uses an internal precision for different tasks. This precision
        depends on the measured precision and is calculated when
        :py:attr:`spec.Spectrum.measured_precision` is invoked. transform_mz
        can be used to transform m/z values into the internal standard.

        Arguments:
            value (float): m/z value

        Returns:
            transformed value (float): to internal standard transformed mz
            value this value can be used to probe internal dictionaries,
            lists or sets, e.g. :func:`pymzml.spec.Spectrum.t_mz_set`

        Example:

            >>> import pymzml
            >>> run = pymzml.run.Reader(
            ...     "test.mzML.gz" ,
            ...     MS_precisions =  {
            ...         1 : 5e-6,
            ...         2 : 20e-6
            ...     }
            ... )
            >>>
            >>> for spectrum in run:
            ...     if spectrum.ms_level == 2:
            ...         peak_to_find = spectrum.has_deconvoluted_peak(
            ...             1044.5804
            ...         )
            ...         print(peak_to_find)
            [(1044.5596, 3809.4356300564586)]

        """
        return int(round(value * self.internal_precision))

    def deprecation_warning(self, function_name: str) -> None:
        deprecation_lookup: Dict[str, str] = {
            "similarityTo": "similarity_to",
            "hasPeak": "has_peak",
            "extremeValues": "extreme_values",
            "transformMZ": "transform_mz",
            "hasOverlappingPeak": "has_overlapping_peak",
            "highestPeaks": "highest_peaks",
            "estimatedNoiseLevel": "estimated_noise_level",
            "removeNoise": "remove_noise",
            "newPlot": "new_plot",
            "centroidedPeaks": "peaks",
            "precursors": "selected_precursors",
        }
        warnings.warn(
            """
            Function: "{0}" deprecated since version 1.0.0, please use new function: "{1}"
            """.format(
                function_name, deprecation_lookup.get(function_name, "not_defined_yet")
            ),
            DeprecationWarning,
        )

    def similarityTo(self, spec2: 'Spectrum', round_precision: int = 0) -> float:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.similarity_to(spec2, round_precision=round_precision)

    def hasPeak(self, mz: float) -> List[Tuple[float, float]]:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.has_peak(mz)

    def extremeValues(self, key: str) -> Tuple[float, float]:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.extreme_values(key)

    def transformMZ(self, value: float) -> int:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.transform_mz(value)

    def hasOverlappingPeak(self, mz: float) -> bool:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.has_overlapping_peak(mz)

    def highestPeaks(self, n: int) -> Union['NDArray', List[Tuple[float, float]]]:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.highest_peaks(n)

    def estimatedNoiseLevel(self, mode: str = "median") -> float:
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.estimated_noise_level(mode=mode)

    def removeNoise(self, mode: str = "median", noiseLevel: Optional[float] = None) -> 'Spectrum':
        self.deprecation_warning(sys._getframe().f_code.co_name)
        return self.remove_noise(mode=mode, noise_level=noiseLevel)

    @property
    def centroidedPeaks(self) -> Union['NDArray', List[Tuple[float, float]]]:
        # self.deprecation_warning( sys._getframe().f_code.co_name )
        return self.peaks("centroided")


class Chromatogram(MsData):
    """
    Class for Chromatogram access and handling.
    """

    def __init__(self, element: ElementTree.Element, measured_precision: float = 5e-6, *, obo_version: Optional[str] = None) -> None:
        """
        Arguments:
            element (xml.etree.ElementTree.Element): spectrum as xml Element

        Keyword Arguments:
            measured_precision (float): in ppm, i.e. 5e-6 equals to 5 ppm.
            param (dict): parameter mapping for this spectrum
        """
        # Call parent class __init__
        super().__init__(element, measured_precision, obo_version=obo_version)
        
        # Chromatogram-specific attributes
        self._ms_level = None
        self._t_mass_set = None
        self._peaks = None
        self._t_mz_set = None
        self._centroided_peaks = None
        self._reprofiled_peaks = None
        self._deconvoluted_peaks = None
        self._extreme_values = None
        self._centroided_peaks_sorted_by_i = None
        self._transformed_mz_with_error = None
        self._transformed_mass_with_error = None
        self._precursors = None
        self._ID = None

    def __repr__(self) -> str:
        return "<__main__.Chromatogram object with native ID {0} at {1}>".format(
            self.ID, hex(id(self))
        )

    def __str__(self) -> str:
        return "<__main__.Chromatogram object with native ID {0} at {1}>".format(
            self.ID, hex(id(self))
        )

    @property
    def ID(self) -> Optional[str]:
        if self._ID is None:
            self._ID = self.element.get("id")
        return self._ID

    @property
    def mz(self) -> Union['NDArray', Tuple, List]:
        """"""
        print("Chromatogram has no property mz.\nReturn retention time instead")
        return self.time

    @property
    def time(self) -> Union['NDArray', Tuple, List]:
        """
        Returns the list of time values. If the time values are encoded, the
        function _decode() is used to decode the encoded data.\n
        The time property can also be set, e.g. for theoretical data.
        However, it is recommended to use the profile property to set time and
        intensity tuples at same time.

        Returns:
            time (list): list of time values from the analyzed chromatogram

        """
        if self._time is None:
            params = self._get_encoding_parameters("time array")
            self._time = self._decode(*params)
        return self._time

    @property
    def i(self) -> Union['NDArray', Tuple, List]:
        if self._i is None:
            params: Tuple[bytes, str, Optional[str], List[str]] = self._get_encoding_parameters("intensity array")
            self._i = self._decode(*params)
        return self._i

    @property
    def profile(self) -> Union['NDArray', List[List[float]]]:
        """
        Returns the list of peaks of the chromatogram as tuples (time, intensity).

        Returns:
            peaks (list): list of time, i tuples

        Example:

        >>> import pymzml
        >>> run = pymzml.run.Reader(
        ...     spectra.mzMl.gz,
        ...     MS_precisions = {
        ...         1 : 5e-6,
        ...         2 : 20e-6
        ...     }
        ... )
        >>> for entry in run:
        ...     if isinstance(entry, pymzml.spec.Chromatogram):
        ...         for time, intensity in entry.peaks:
        ...             print(time, intensity)

        Note:
           The peaks property can also be set, e.g. for theoretical data.
           It requires a list of time/intensity tuples.

        """
        if self._profile is None:
            if self._time is None and self._i is None:
                self._profile = []
                for pos, t in enumerate(self.time):
                    self._profile.append([t, self.i[pos]])
                    # much faster than zip ... list(zip(self.mz, self.i))
            elif self._time is not None and self._i is not None:
                self._profile = []
                for pos, t in enumerate(self.time):
                    self._profile.append([t, self.i[pos]])
            elif self._profile is None:
                self._profile = []
        return self._array(self._profile)

    @profile.setter
    def profile(self, tuple_list: List[Tuple[float, float]]) -> 'Chromatogram':
        if len(tuple_list) == 0:
            return self
        # self._mz, self._i = map(list, zip(*tuple_list))
        # same here .. zip is soooooo slow :)
        self._time: List[float] = []
        self._i: List[float] = []
        for time, i in tuple_list:
            self._time.append(time)
            self._i.append(i)
        self._peaks = tuple_list
        self._reprofiledPeaks = None
        self._centroidedPeaks = None
        return self

    def peaks(self) -> Union['NDArray', List[List[float]]]:
        """
        Return the list of peaks of the spectrum as tuples (time, intensity).

        Returns:
            peaks (list): list of time, intensity tuples

        Example:

        >>> import pymzml
        >>> run = pymzml.run.Reader(
        ...     spectra.mzMl.gz,
        ...     MS_precisions =  {
        ...         1 : 5e-6,
        ...         2 : 20e-6
        ...     }
        ... )
        >>> for entry in run:
        ...     if isinstance(entry, pymzml.spec.Chromatogram):
        ...         for time, intensity in entry.peaks:
        ...             print(time, intensity)

        Note:
           The peaks property can also be set, e.g. for theoretical data.
           It requires a list of time/intensity tuples.

        """
        return self.profile
