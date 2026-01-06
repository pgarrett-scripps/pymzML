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

from typing import Any

import math
import xml.etree.ElementTree as ElementTree
from collections import defaultdict as ddict
from functools import lru_cache
from operator import itemgetter as itemgetter

import numpy as np
from numpy.typing import NDArray

from . import regex_patterns
from .constants import PeakType, DataType, NoiseMode, PROTON_MASS

from .msdata import MsData


class Spectrum(MsData):
    """
    Spectrum class which inherits from MsData.

    Arguments:
        element (xml.etree.ElementTree.Element): spectrum as xml element

    Keyword Arguments:
        measured_precision (float): in ppm, i.e. 5e-6 equals to 5 ppm.
        obo_version (str, optional): obo version number.
    """

    def __init__(
        self,
        element: ElementTree.Element = ElementTree.Element(""),
        measured_precision: float = 5e-6,
        *,
        obo_version: str | None = None,
    ) -> None:
        super().__init__(element, measured_precision, obo_version=obo_version)

        # Spectrum-specific attributes
        self._centroided_peaks: NDArray[np.float64] | None = None
        self._centroided_peaks_sorted_by_i: NDArray[np.float64] | None = None
        self._extreme_values: dict[str, tuple[float, float]] | None = None
        self._id: int | str | None = None
        self._id_dict: dict[str, str | int] | None = None
        self._index: int | str | None = None
        self._ms_level: int | None = None
        self._peak_dict: dict[str, NDArray[np.float64] | None] = {
            PeakType.RAW: None,
            PeakType.CENTROIDED: None,
            PeakType.REPROFILED: None,
            PeakType.DECONVOLUTED: None,
        }
        self._selected_precursors: list[dict[str, Any]] | None = None
        self.reprofiled: bool = False
        self._reprofiled_peaks: dict[float, float] | None = None
        self._scan_time: float | None = None
        self._scan_time_unit: str | None = None
        self._scan_time_in_minutes: float | None = None
        self._t_mass_set: set[int] | None = None
        self._t_mz_set: set[int] | None = None
        self._tic: float | None = None
        self._precursors: list[str] | None = None
        self._transformed_mass_with_error: dict[int, list[tuple[float, float]]] | None = None
        self._transformed_mz_with_error: dict[int, list[tuple[float, float]]] | None = None
        self._transformed_peaks: list[tuple[int, float]] | None = None
        self._ms_deisotop_warning_printed: bool = False

    def __del__(self) -> None:
        """Clear self.element to limit RAM usage"""
        if self.element is not None:
            self.element.clear()

    def __add__(self, other_spec: "Spectrum") -> "Spectrum":
        """
        Adds two pymzml spectra

        Arguments:
            other_spec: spectrum to add to the current spectrum

        Returns:
            self: reference to the edited spectrum

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
        if self._peak_dict[PeakType.REPROFILED] is None:
            reprofiled = self._reprofile_Peaks()
            self.set_peaks(reprofiled, PeakType.REPROFILED)
        if other_spec._peak_dict[PeakType.REPROFILED] is None:
            other_spec.set_peaks(other_spec._reprofile_Peaks(), PeakType.REPROFILED)

        self_reprofiled = self._peak_dict[PeakType.REPROFILED]
        other_reprofiled = other_spec._peak_dict[PeakType.REPROFILED]
        if self_reprofiled is not None and other_reprofiled is not None:
            # Add intensities at matching m/z values
            self._peak_dict[PeakType.REPROFILED] = self._add_reprofiled_peaks(
                self_reprofiled, other_reprofiled
            )
        return self

    def __sub__(self, other_spec: "Spectrum") -> "Spectrum":
        """
        Subtracts two pymzml spectra.

        Arguments:
            other_spec: spectrum to subtract from the current spectrum

        Returns:
            self: returns self after other_spec was subtracted
        """
        assert isinstance(other_spec, Spectrum)
        if self._peak_dict[PeakType.REPROFILED] is None:
            self.set_peaks(self._reprofile_Peaks(), PeakType.REPROFILED)
        if other_spec._peak_dict[PeakType.REPROFILED] is None:
            other_spec.set_peaks(other_spec._reprofile_Peaks(), PeakType.REPROFILED)

        self_reprofiled = self._peak_dict[PeakType.REPROFILED]
        other_reprofiled = other_spec._peak_dict[PeakType.REPROFILED]
        if self_reprofiled is not None and other_reprofiled is not None:
            # Subtract intensities at matching m/z values
            self._peak_dict[PeakType.REPROFILED] = self._subtract_reprofiled_peaks(
                self_reprofiled, other_reprofiled
            )
        self.set_peaks(None, PeakType.CENTROIDED)
        self.set_peaks(None, PeakType.RAW)
        return self

    def __mul__(self, value: int | float) -> "Spectrum":
        """
        Multiplies each intensity with a float, i.e. scales the spectrum.

        Arguments:
            value: value to multiply the intensities with

        Returns:
            self: returns self after intensities were scaled by value
        """
        assert isinstance(value, (int, float))
        for peak_type in [
            PeakType.RAW,
            PeakType.CENTROIDED,
            PeakType.REPROFILED,
            PeakType.DECONVOLUTED,
        ]:
            peaks = self._peak_dict[peak_type]
            if peaks is not None and len(peaks) > 0:
                if peak_type == PeakType.DECONVOLUTED:
                    # Deconvoluted has 3 columns: mass, intensity, charge
                    self._peak_dict[peak_type] = np.column_stack(
                        (peaks[:, 0], peaks[:, 1] * value, peaks[:, 2])
                    )
                else:
                    # Other types have 2 columns: mz, intensity
                    self._peak_dict[peak_type] = np.column_stack((peaks[:, 0], peaks[:, 1] * value))
        return self

    def __truediv__(self, value: int | float) -> "Spectrum":
        """
        Divides each intensity by a float, i.e. scales the spectrum.

        Arguments:
            value: value to divide the intensities by

        Returns:
            self: returns self after intensities were scaled by value
        """
        for peak_type in [
            PeakType.RAW,
            PeakType.CENTROIDED,
            PeakType.REPROFILED,
            PeakType.DECONVOLUTED,
        ]:
            peaks = self._peak_dict[peak_type]
            if peaks is not None and len(peaks) > 0:
                if peak_type == PeakType.DECONVOLUTED:
                    # Deconvoluted has 3 columns: mass, intensity, charge
                    self._peak_dict[peak_type] = np.column_stack(
                        (peaks[:, 0], peaks[:, 1] / value, peaks[:, 2])
                    )
                else:
                    # Other types have 2 columns: mz, intensity
                    self._peak_dict[peak_type] = np.column_stack((peaks[:, 0], peaks[:, 1] / value))
        return self

    def __div__(self, value: int | float) -> "Spectrum":
        """Integer division is the same as __truediv__ for this class"""
        return self.__truediv__(value)

    def __repr__(self) -> str:
        """Returns representative string for a spectrum object class"""
        return f"<__main__.Spectrum object with native ID {self.ID} at {hex(id(self))}>"

    def __str__(self) -> str:
        """Returns representative string for a spectrum object class"""
        return f"<__main__.Spectrum object with native ID {self.ID} at {hex(id(self))}>"

    @lru_cache()
    def __getitem__(self, accession: str) -> str | float | bool | list[str | float] | None:
        """
        Access spectrum XML information by tag name

        Args:
            accession: name of the XML tag

        Returns:
            value: value of the XML tag
        """
        if accession == "id":
            return self.ID

        if not accession.startswith("MS:"):
            try:
                obo_entry = self.obo_translator[accession]
                if obo_entry is not None:
                    accession = obo_entry["id"]
                else:
                    accession = "---"
            except (TypeError, KeyError):
                accession = "---"

        search_string = f'.//*[@accession="{accession}"]'
        elements: list[float | str] = []
        if self.element is not None:
            for x in self.element.iterfind(search_string):
                val = x.attrib.get("value", "")
                try:
                    val = float(val)
                except ValueError:
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

    def get(self, acc: str, default: Any | None = None) -> Any:
        """Mimic dicts get function.

        Args:
            acc: accession or obo tag to return
            default: default value if acc is not found
        """
        val = self[acc]
        return default if val is None else val

    def __contains__(self, value: str) -> bool:
        """Check if MS tag or name can be found in spectrum.

        Args:
            value: MS tag or OBO name

        Returns:
            bool
        """
        return self[value] is not None

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
    def t_mz_set(self) -> set[int]:
        """
        Creates a set of integers out of transformed m/z values
        (including all values in the defined imprecision).
        This is used to accelerate has_peak function and similar.

        Returns:
            t_mz_set (set): set of transformed m/z values
        """
        if self._t_mz_set is None:
            self._t_mz_set = set()
            cent_peaks = self.peaks(PeakType.CENTROIDED)
            for mz, _ in cent_peaks:
                self._t_mz_set |= set(
                    range(
                        int(round((mz - (mz * self.measured_precision)) * self.internal_precision)),
                        int(round((mz + (mz * self.measured_precision)) * self.internal_precision))
                        + 1,
                    )
                )
        return self._t_mz_set

    @property
    def transformed_mz_with_error(self) -> dict[int, list[tuple[float, float]]]:
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
            cent_peaks = self.peaks(PeakType.CENTROIDED)
            for mz, i in cent_peaks:
                for t_mz_with_error in range(
                    int(round((mz - (mz * self.measured_precision)) * self.internal_precision)),
                    int(round((mz + (mz * self.measured_precision)) * self.internal_precision)) + 1,
                ):
                    self._transformed_mz_with_error[t_mz_with_error].append((mz, i))
        return self._transformed_mz_with_error

    @property
    def transformed_peaks(self) -> list[tuple[int, float]]:
        """
        m/z value is multiplied by the internal precision.

        Returns:
            Transformed peaks (list): Returns a list of peaks (tuples of mz and
            intensity).
            Float m/z values are adjusted by the internal precision
            to integers.
        """
        if self._transformed_peaks is None:
            cent_peaks = self.peaks(PeakType.CENTROIDED)
            self._transformed_peaks = [(self.transform_mz(mz), i) for mz, i in cent_peaks]
        return self._transformed_peaks

    @property
    def TIC(self) -> float:
        """
        Property to access the total ion current for this spectrum.

        Returns:
            TIC (float): Total Ion Current of the spectrum.
        """
        if self._tic is None:
            if self.element is not None:
                tic_element = self.element.find(f"./{self.ns}cvParam[@accession='MS:1000285']")
                if tic_element is not None:
                    value_str = tic_element.get("value")
                    if value_str is not None:
                        self._tic = float(value_str)
        return self._tic if self._tic is not None else 0.0

    @property
    def ID(self) -> int | str | None:
        """
        Access the native id of the spectrum.

        Returns:
            ID: native ID of the spectrum
        """
        if self._id is None and self.element is not None:
            spec_id = self.element.get("id")
            if spec_id:
                match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_id)
                if match:
                    try:
                        self._id = int(match.group(1))
                    except ValueError:
                        self._id = match.group(1)
                else:
                    self._id = spec_id
        return self._id

    @property
    def id_dict(self) -> dict[str, str | int]:
        """
        Access to all entries stored the id attribute of a spectrum.

        Returns:
            id_dict: key value pairs for all entries in id attribute
        """
        if self._id_dict is None:
            tuples: list[tuple[str, str | int]] = []
            if self.element is not None:
                spec_id = self.element.attrib.get("id", "")
            else:
                spec_id = ""
            matches = regex_patterns.SPECTRUM_PATTERN3.findall(spec_id)
            if matches:
                for k, v in matches:
                    k = k.strip()
                    v = v.strip()
                    try:
                        v = int(v)
                    except ValueError:
                        pass
                    tuples.append((k, v))
                self._id_dict = dict(tuples)
            else:
                self._id_dict = {}
        return self._id_dict

    @property
    def index(self) -> int | str | None:
        """
        Access the index of the spectrum.

        Returns:
            index: index of the spectrum
        """
        if self._index is None:
            if self.element is not None:
                self._index = self.element.get("index")
            else:
                self._index = None
            if self._index:
                try:
                    self._index = int(self._index)
                except ValueError:
                    pass
        return self._index

    @property
    def ms_level(self) -> int | None:
        """
        Property to access the ms level.

        Returns:
            ms_level
        """
        if self._ms_level is None:
            if self.element is not None:
                sub_element = self.element.find(f".//{self.ns}cvParam[@accession='MS:1000511']")
                if sub_element is not None:
                    value_str = sub_element.get("value")
                    if value_str is not None:
                        self._ms_level = int(value_str)
        return self._ms_level

    @property
    def scan_time(self) -> tuple[float | None, str | None]:
        """
        Property to access the retention time and retention time unit.

        Returns:
            scan_time, scan_time_unit
        """
        if self._scan_time is None or self._scan_time_unit is None:
            if self.element is not None:
                scan_time_ele = self.element.find(".//*[@accession='MS:1000016']")
                if scan_time_ele is not None:
                    value_str = scan_time_ele.attrib.get("value")
                    if value_str is not None:
                        self._scan_time = float(value_str)
                    self._scan_time_unit = scan_time_ele.get("unitName", "unicorns")
        return self._scan_time, self._scan_time_unit

    def scan_time_in_minutes(self) -> float | None:
        """
        Property to access the retention time in minutes.

        Returns:
            scan_time in minutes
        """
        if self._scan_time_in_minutes is None:
            self._scan_time, _ = self.scan_time
            if self._scan_time is not None and self._scan_time_unit:
                unit_lower = self._scan_time_unit.lower()
                if unit_lower == "millisecond":
                    self._scan_time_in_minutes = self._scan_time / 1000.0 / 60.0
                elif unit_lower == "second":
                    self._scan_time_in_minutes = self._scan_time / 60.0
                elif unit_lower == "minute":
                    self._scan_time_in_minutes = self._scan_time
                elif unit_lower == "hour":
                    self._scan_time_in_minutes = self._scan_time * 60.0
                else:
                    raise ValueError(f"Time unit '{self._scan_time_unit}' unknown")
        return self._scan_time_in_minutes

    @property
    def selected_precursors(self) -> list[dict[str, Any]]:
        """
        Property to access the selected precursors of a MS2 spectrum.

        Returns:
            selected_precursors: list of precursor dictionaries
        """
        if self._selected_precursors is None:
            if self.element is not None:
                selected_precursor_mzs = self.element.findall(".//*[@accession='MS:1000744']")
                selected_precursor_is = self.element.findall(".//*[@accession='MS:1000042']")
                selected_precursor_cs = self.element.findall(".//*[@accession='MS:1000041']")
                precursors = self.element.findall(f"./{self.ns}precursorList/{self.ns}precursor")
            else:
                selected_precursor_mzs = []
                selected_precursor_is = []
                selected_precursor_cs = []
                precursors = []

            mz_values = [float(obj.get("value", "0")) for obj in selected_precursor_mzs]
            i_values = [float(obj.get("value", "0")) for obj in selected_precursor_is]
            charges = [int(obj.get("value", "0")) for obj in selected_precursor_cs]

            ids: list[str | None] = []
            for prec in precursors:
                spec_ref = prec.get("spectrumRef")
                if spec_ref is not None:
                    match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_ref)
                    ids.append(match.group(1) if match else None)
                else:
                    ids.append(None)

            _vals: list[tuple[str, list[Any]]] = [
                ("i", i_values),
                ("charge", charges),
                ("precursor id", ids),
                ("element", precursors),
            ]

            self._selected_precursors = []
            for pos, mz in enumerate(mz_values):
                dict_2_save: dict[str, Any] = {"mz": mz}
                for key, list_of_values in _vals:
                    if pos < len(list_of_values):
                        dict_2_save[key] = list_of_values[pos]
                self._selected_precursors.append(dict_2_save)

        return self._selected_precursors

    @property
    def precursors(self) -> list[str]:
        """

        IS THIS DEPRICIATED?

        List the precursor information of this spectrum.

        Returns:
            precursor: list of precursor ids
        """
        # self.deprecation_warning(sys._getframe().f_code.co_name)
        if not self._precursors:
            if self.element is not None:
                precursors = self.element.findall(f"./{self.ns}precursorList/{self.ns}precursor")
            else:
                precursors = []
            self._precursors = []
            for prec in precursors:
                spec_ref = prec.get("spectrumRef")
                if spec_ref:
                    match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_ref)
                    if match:
                        self._precursors.append(match.group(1))
        return self._precursors

    def remove_precursor_peak(self) -> NDArray[np.float64]:
        """Remove precursor peaks from the spectrum."""
        peaks = self.peaks(PeakType.CENTROIDED)

        for precursor in self.selected_precursors:
            mz = precursor["mz"]
            hp = self.has_peak(mz)
            if hp:
                for p in hp:
                    peaks = peaks[(peaks[:, 0] != p[0])]

        self.set_peaks(peaks, PeakType.CENTROIDED)
        self.set_peaks(peaks, PeakType.RAW)
        return peaks

    @property
    def mz(self) -> NDArray[np.float64]:
        """
        Returns the list of m/z values.

        Returns:
            mz: list of m/z values of spectrum
        """
        if self._mz is None:
            params = self._get_encoding_parameters("m/z array")
            self._mz = self._decode(*params)
        return self._mz

    @mz.setter
    def mz(self, mz_list: list[float] | NDArray[np.float64]) -> None:
        """Set m/z values."""
        mz_array = np.array(mz_list, dtype=np.float64)
        mz_array.sort()
        self._mz = mz_array

    @property
    def i(self) -> NDArray[np.float64]:
        """
        Returns the list of the intensity values.

        Returns:
            i: list of intensity values from the analyzed spectrum
        """
        if self._i is None:
            params = self._get_encoding_parameters("intensity array")
            self._i = self._decode(*params)
        return self._i

    @i.setter
    def i(self, intensity_list: list[float] | NDArray[np.float64]) -> None:
        """Set intensity values."""
        self._i = np.array(intensity_list, dtype=np.float64)

    def peaks(self, peak_type: str | PeakType = PeakType.RAW) -> NDArray[np.float64]:
        """
        Decode and return peaks as numpy array.

        Args:
            peak_type: currently supported types are: raw, centroided, reprofiled, deconvoluted

        Returns:
            peaks: numpy array of mz/i tuples (or mz/i/charge for deconvoluted)
        """
        # Convert string to enum if needed
        if isinstance(peak_type, str):  # type: ignore
            peak_type = PeakType(peak_type)

        if self._peak_dict[peak_type] is None:
            if self._peak_dict[PeakType.RAW] is None:
                mz_params = self._get_encoding_parameters("m/z array")
                i_params = self._get_encoding_parameters("intensity array")
                mz = self._decode(*mz_params)
                i = self._decode(*i_params)
                arr = np.stack((mz, i), axis=-1)
                self._peak_dict[PeakType.RAW] = arr

            if peak_type == PeakType.RAW:
                pass
            elif peak_type == PeakType.CENTROIDED:
                self._peak_dict[PeakType.CENTROIDED] = self._centroid_peaks()
            elif peak_type == PeakType.REPROFILED:
                self._peak_dict[PeakType.REPROFILED] = self._reprofile_Peaks()
            elif peak_type == PeakType.DECONVOLUTED:
                self._peak_dict[PeakType.DECONVOLUTED] = self._deconvolute_peaks()
            else:
                raise KeyError(f"Unknown peak type: {peak_type}")

        peaks = self._peak_dict[peak_type]
        if peaks is None:
            raise ValueError(f"No peaks available for peak type: {peak_type}")
        return peaks

    def get_array(self, arr_name: str) -> NDArray[np.float64] | None:
        """Get a specific data array by name."""
        array_params = self._get_encoding_parameters(arr_name)
        array = self._decode(*array_params)
        if len(array) == 0:
            _ = self.get_all_arrays_in_spec(not_found_array=arr_name)
            return None
        return array

    def get_tims_tof_ion_mobility(
        self, array_name: str = "mean inverse reduced ion mobility array"
    ) -> NDArray[np.float64] | None:
        """Get TIMS TOF ion mobility array."""
        return self.get_array(array_name)

    def get_all_arrays_in_spec(self, not_found_array: str | None = None) -> list[str]:
        """Get all available array names in the spectrum."""
        b_data_string = f"./{self.ns}binaryDataArrayList/{self.ns}binaryDataArray/{self.ns}cvParam[@unitCvRef='MS']"
        if self.element is not None:
            b_data_arrays = self.element.findall(b_data_string)
        else:
            b_data_arrays = []
        array_names = [arr.attrib["name"] for arr in b_data_arrays]

        if not_found_array is not None:
            formatted_names = [f"\t- {name}" for name in array_names]
            print(f"Requested array ({not_found_array}) not found.\nAvailable arrays are:")
            print("\n".join(formatted_names))

        return array_names

    def _deconvolute_peaks(self, *args: Any, **kwargs: Any) -> NDArray[np.float64]:
        """Deconvolute peaks using ms_deisotope."""
        from ms_deisotope.deconvolution import deconvolute_peaks  # type: ignore
        from ms_peak_picker import simple_peak  # type: ignore

        peaks = self.peaks(PeakType.CENTROIDED)

        # Pack peak matrix into expected structure
        peak_list = [simple_peak(p[0], p[1], 0.01) for p in peaks]
        decon_result = deconvolute_peaks(peak_list, *args, **kwargs)
        dpeaks = decon_result.peak_set

        # Pack deconvoluted peak list into matrix structure
        dpeaks_mat = np.zeros((len(dpeaks), 3), dtype=np.float64)
        for i, dp in enumerate(dpeaks):
            dpeaks_mat[i, :] = dp.neutral_mass, dp.intensity, dp.charge

        return dpeaks_mat

    def set_peaks(
        self,
        peaks: NDArray[np.float64]
        | list[tuple[int | float, int | float]]
        | dict[int | float, int | float]
        | None,
        peak_type: str | PeakType,
    ) -> None:
        """
        Assign a custom peak array of type peak_type

        Args:
            peaks: peaks as numpy array, list of (mz, intensity) tuples, dict {mz: intensity}, or None to clear
            peak_type: Either raw, centroided, reprofiled, or deconvoluted

        """
        # Convert string to enum if needed
        if isinstance(peak_type, str):  # type: ignore
            peak_type = PeakType(peak_type.lower())

        # Reset after changing peaks
        self._transformed_mass_with_error = None
        self._transformed_mz_with_error = None

        # Convert input to numpy array
        peaks_array: NDArray[np.float64] | None = None
        if peaks is not None:
            if isinstance(peaks, dict):
                # Convert dict to sorted list of tuples
                sorted_items = sorted(peaks.items())
                peaks_array = np.array(sorted_items, dtype=np.float64)
            elif isinstance(peaks, list):
                # Convert list of tuples to array
                peaks_array = np.array(peaks, dtype=np.float64)
            elif isinstance(peaks, np.ndarray):  # type: ignore
                # Ensure correct dtype
                peaks_array = peaks.astype(np.float64) if peaks.dtype != np.float64 else peaks
            else:
                raise TypeError(f"Unsupported peaks type: {type(peaks)}")

            # Ensure peaks is always 2D
            if len(peaks_array) > 0:
                if peaks_array.ndim != 2:
                    raise ValueError(f"Peaks array must be 2D, got shape: {peaks_array.shape}")

        self._peak_dict[peak_type] = peaks_array

        if peaks_array is not None and len(peaks_array) > 0:
            if peak_type in (PeakType.RAW, PeakType.CENTROIDED):
                self._mz = peaks_array[:, 0]
                self._i = peaks_array[:, 1]
        else:
            if peak_type in (PeakType.RAW, PeakType.CENTROIDED):
                self._mz = np.array([], dtype=np.float64)
                self._i = np.array([], dtype=np.float64)

    def _centroid_peaks(self) -> NDArray[np.float64]:
        """
        Perform a Gauss fit to centroid the peaks.

        Returns:
            centroided_peaks: array of centroided m/z, i tuples
        """
        try:
            profile_ot = self.obo_translator.name.get(
                "profile spectrum"
            ) or self.obo_translator.name.get("profile mass spectrum")
            if profile_ot:
                acc = profile_ot["id"]
                is_profile = (
                    self.element is not None
                    and self.element.find(f".//*[@accession='{acc}']") is not None
                )
            else:
                is_profile = None
        except (TypeError, AttributeError):
            is_profile = None

        if is_profile or self.reprofiled:
            return self._centroid_peaks_numpy()
        else:
            raw_peaks = self.peaks("raw")
            return raw_peaks

    def _centroid_peaks_numpy(self) -> NDArray[np.float64]:
        """
        Numpy-optimized version of centroid peaks using vectorized operations.

        Returns:
            centroided_peaks: array of centroided m/z, i tuples
        """
        if self._peak_dict["reprofiled"] is not None:
            reprofiled_peaks = self.peaks("reprofiled")
            if isinstance(reprofiled_peaks, np.ndarray): # type: ignore
                i_array = reprofiled_peaks[:, 1]
                mz_array = reprofiled_peaks[:, 0]
            else:
                return np.empty((0, 2), dtype=np.float64)
        else:
            i_array = np.asarray(self.i, dtype=np.float64)
            mz_array = np.asarray(self.mz, dtype=np.float64)

        if len(i_array) < 3:
            # Not enough points for Gaussian fitting, return as-is
            if len(i_array) > 0:
                return np.column_stack((mz_array, i_array))
            return np.empty((0, 2), dtype=np.float64)

        # Vectorized peak detection
        i_prev = i_array[:-2]
        i_curr = i_array[1:-1]
        i_next = i_array[2:]

        mz_prev = mz_array[:-2]
        mz_curr = mz_array[1:-1]
        mz_next = mz_array[2:]

        # Find peaks
        is_peak = (i_prev > 0) & (i_prev < i_curr) & (i_curr > i_next) & (i_next > 0)

        # Filter out peaks with irregular spacing
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
        valid_log = (y2 > y1) & (y3_adjusted > y1) & (y1 > 0)

        if not np.any(valid_log):
            return np.empty((0, 2), dtype=np.float64)

        x1 = x1[valid_log]
        y1 = y1[valid_log]
        x2 = x2[valid_log]
        y2 = y2[valid_log]
        x3 = x3[valid_log]
        y3_adjusted = y3_adjusted[valid_log]

        with np.errstate(divide="ignore", invalid="ignore"):
            double_log = np.log(y2 / y1) / np.log(y3_adjusted / y1)

            numerator = double_log * (x1 * x1 - x3 * x3) - x1 * x1 + x2 * x2
            denominator = 2 * (x2 - x1) - 2 * double_log * (x3 - x1)
            mue = numerator / denominator

            c_squared_num = x2 * x2 - x1 * x1 - 2 * x2 * mue + 2 * x1 * mue
            c_squared_denom = 2 * np.log(y1 / y2)
            c_squared = c_squared_num / c_squared_denom

            a = y1 * np.exp((x1 - mue) * (x1 - mue) / (2 * c_squared))

        # Filter out invalid results
        valid = np.isfinite(mue) & np.isfinite(a)
        mue = mue[valid]
        a = a[valid]

        return np.column_stack((mue, a))

    def _reprofile_Peaks(self) -> NDArray[np.float64]:
        """
        Performs reprofiling for property reprofiled_peaks.

        Returns:
            reprofiled_peaks: numpy array of reprofiled m/z, i pairs
        """
        tmp: dict[float, float] = ddict(float)
        cent_peaks = self.peaks(PeakType.CENTROIDED)
        for mz, i in cent_peaks:
            s = mz * self.measured_precision * 2
            s2 = s * s
            floor = mz - 5.0 * s
            ceil = mz + 5.0 * s
            ip = self.internal_precision / 4

            for pos in range(int(round(floor * ip)), int(round(ceil * ip)) + 1):
                if pos % 5 == 0:
                    a = float(pos) / float(ip)
                    y = i * math.exp(-1 * ((mz - a) * (mz - a)) / (2 * s2))
                    tmp[a] += y

        self.reprofiled = True
        self.set_peaks(None, PeakType.CENTROIDED)

        # Convert dict to sorted numpy array
        if tmp:
            sorted_items = sorted(tmp.items(), key=itemgetter(0))
            return np.array(sorted_items, dtype=np.float64)
        return np.empty((0, 2), dtype=np.float64)

    def _add_reprofiled_peaks(
        self, peaks1: NDArray[np.float64], peaks2: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Add two reprofiled peak arrays.

        Args:
            peaks1: First reprofiled peaks array
            peaks2: Second reprofiled peaks array

        Returns:
            Combined peaks array with summed intensities at matching m/z
        """
        # Create dictionaries for efficient lookup
        dict1 = {mz: i for mz, i in peaks1} if len(peaks1) > 0 else {}
        dict2 = {mz: i for mz, i in peaks2} if len(peaks2) > 0 else {}

        # Combine all m/z values
        all_mz = set(dict1.keys()) | set(dict2.keys())

        # Add intensities
        result = {mz: dict1.get(mz, 0.0) + dict2.get(mz, 0.0) for mz in all_mz}

        # Convert back to sorted numpy array
        if result:
            sorted_items = sorted(result.items(), key=itemgetter(0))
            return np.array(sorted_items, dtype=np.float64)
        return np.empty((0, 2), dtype=np.float64)

    def _subtract_reprofiled_peaks(
        self, peaks1: NDArray[np.float64], peaks2: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Subtract two reprofiled peak arrays.

        Args:
            peaks1: First reprofiled peaks array
            peaks2: Second reprofiled peaks array to subtract

        Returns:
            Result peaks array with subtracted intensities at matching m/z
        """
        # Create dictionaries for efficient lookup
        dict1 = {mz: i for mz, i in peaks1} if len(peaks1) > 0 else {}
        dict2 = {mz: i for mz, i in peaks2} if len(peaks2) > 0 else {}

        # Combine all m/z values
        all_mz = set(dict1.keys()) | set(dict2.keys())

        # Subtract intensities
        result = {mz: dict1.get(mz, 0.0) - dict2.get(mz, 0.0) for mz in all_mz}

        # Convert back to sorted numpy array
        if result:
            sorted_items = sorted(result.items(), key=itemgetter(0))
            return np.array(sorted_items, dtype=np.float64)
        return np.empty((0, 2), dtype=np.float64)

    def _mz_2_mass(self, mz: float, charge: int) -> float:
        """
        Calculate the uncharged mass for a given mz value

        Arguments:
            mz: m/z value
            charge: charge

        Returns:
            mass: Returns mass of a given m/z value
        """
        return (mz - PROTON_MASS) * charge

    def set_params_from_reference_group(self, ref_element: ElementTree.Element) -> None:
        """Set parameters from reference group."""
        if self.element is None:
            return
        ref = self.element.find(f"{self.ns}referenceableParamGroupRef")
        if ref is not None:
            ref_id = ref.get("ref")
            ele = ref_element.find(f".//*[@id='{ref_id}']")
            if ele is not None and ref_id == ele.get("id"):
                for param in ele.iter():
                    self.element.append(param)

    # Public functions

    def reduce(
        self,
        peak_type: str | PeakType = PeakType.RAW,
        mz_range: tuple[float | None, float | None] = (None, None),
    ) -> NDArray[np.float64]:
        """
        Remove all m/z values outside the given range.

        Arguments:
            peak_type: type of peaks to reduce
            mz_range: tuple of min, max values (None means no limit)

        Returns:
            peaks: array of mz, i tuples in the given range
        """
        # Convert string to enum if needed
        if isinstance(peak_type, str):  # type: ignore
            peak_type = PeakType(peak_type)

        arr = self.peaks(peak_type)

        # Handle None values in mz_range
        min_mz = mz_range[0] if mz_range[0] is not None else -np.inf
        max_mz = mz_range[1] if mz_range[1] is not None else np.inf

        mask = np.logical_and(arr[:, 0] >= min_mz, arr[:, 0] <= max_mz)
        peaks = arr[mask]
        self.set_peaks(peaks, peak_type)
        return peaks

    def remove_noise(
        self,
        mode: str | NoiseMode = NoiseMode.MEDIAN,
        noise_level: float | None = None,
        signal_to_noise_threshold: float = 1.0,
    ) -> "Spectrum":
        """
        Function to remove noise from peaks.

        Keyword arguments:
            mode: define mode for removing noise (median, mean, mad)
            noise_level: noise threshold
            signal_to_noise_threshold: S/N threshold for a peak to be accepted

        Returns:
            self: Returns self after noise removal
        """
        # Convert string to enum if needed
        if isinstance(mode, str):  # type: ignore
            mode = NoiseMode(mode)

        if noise_level is None:
            noise_level = self.estimated_noise_level(mode=mode)

        cent_peaks = self.peaks(PeakType.CENTROIDED)
        if len(cent_peaks) != 0:
            self._peak_dict[PeakType.CENTROIDED] = cent_peaks[
                cent_peaks[:, 1] / noise_level >= signal_to_noise_threshold
            ]

        raw_peaks = self.peaks(PeakType.RAW)
        if len(raw_peaks) != 0:
            self._peak_dict[PeakType.RAW] = raw_peaks[
                raw_peaks[:, 1] / noise_level >= signal_to_noise_threshold
            ]

        self._peak_dict[PeakType.REPROFILED] = None
        return self

    def estimated_noise_level(self, mode: str | NoiseMode = NoiseMode.MEDIAN) -> float:
        """
        Calculates noise threshold for function remove_noise.

        Keyword Arguments:
            mode: define mode for removing noise (median, mean, mad)

        Returns:
            noise_level: estimate noise threshold
        """
        # Convert string to enum if needed
        if isinstance(mode, str):  # type: ignore
            mode = NoiseMode(mode)

        cent_peaks = self.peaks(PeakType.CENTROIDED)
        if len(cent_peaks) == 0:
            return 0.0

        if mode not in self.noise_level_estimate:
            if mode == NoiseMode.MEDIAN:
                self.noise_level_estimate[mode] = float(np.median(cent_peaks[:, 1]))
            elif mode == NoiseMode.MAD:
                median = self.estimated_noise_level(mode=NoiseMode.MEDIAN)
                self.noise_level_estimate[mode] = float(
                    np.median(np.abs(cent_peaks[:, 1] - median))
                )
            elif mode == NoiseMode.MEAN:
                self.noise_level_estimate[mode] = float(np.mean(cent_peaks[:, 1]))
            else:
                print(f"Unknown noise level estimation mode: {mode}")
                return 0.0

        return self.noise_level_estimate[mode]

    def highest_peaks(self, n: int) -> NDArray[np.float64]:
        """
        Function to retrieve the n-highest centroided peaks of the spectrum.

        Arguments:
            n: number of highest peaks to return

        Returns:
            centroided peaks: array with n-highest peaks
        """
        if self._centroided_peaks_sorted_by_i is None:
            cent_peaks = self.peaks("centroided")
            self._centroided_peaks_sorted_by_i = cent_peaks[cent_peaks[:, 1].argsort()]

        return self._centroided_peaks_sorted_by_i[-n:]

    def ppm2abs(
        self, value: float, ppm_value: float, direction: int = 1, factor: float = 1
    ) -> float:
        """
        Returns the value plus (or minus) the error for this value.

        Arguments:
            value: m/z value
            ppm_value: ppm value
            direction: plus or minus (1 or -1)
            factor: multiplication factor for the imprecision

        Returns:
            imprecision: imprecision for the given value
        """
        return value + (value * (ppm_value * factor)) * direction

    def extreme_values(self, key: str) -> tuple[float, float]:
        """
        Find extreme values, minimal and maximum m/z and intensity

        Arguments:
            key: "mz" or "i"

        Returns:
            extrema: tuple of minimal and maximum m/z or intensity
        """
        if key not in (DataType.MZ, DataType.INTENSITY):
            raise ValueError(
                f"Unknown extreme request: '{key}'; available values are: {DataType.MZ}, {DataType.INTENSITY}"
            )

        if self._extreme_values is None:
            self._extreme_values = {}

        if key not in self._extreme_values:
            try:
                raw_peaks = self.peaks(PeakType.RAW)
                if len(raw_peaks) > 0:
                    if key == DataType.MZ:
                        self._extreme_values["mz"] = (
                            float(raw_peaks[:, 0].min()),
                            float(raw_peaks[:, 0].max()),
                        )
                    else:
                        self._extreme_values["i"] = (
                            float(raw_peaks[:, 1].min()),
                            float(raw_peaks[:, 1].max()),
                        )
                else:
                    self._extreme_values[key] = (0.0, 0.0)
            except (ValueError, IndexError):
                self._extreme_values[key] = (0.0, 0.0)

        return self._extreme_values[key]

    def has_peak(self, mz2find: float) -> list[tuple[float, float]]:
        """
        Checks if a Spectrum has a certain peak.

        Arguments:
            mz2find: m/z value which should be found

        Returns:
            peaks: list of m/z, i tuples
        """
        value = self.transform_mz(mz2find)
        return self.transformed_mz_with_error.get(value, [])

    def has_overlapping_peak(self, mz: float) -> bool:
        """
        Checks if a spectrum has more than one peak for a given m/z value.

        Arguments:
            mz: m/z value which should be checked

        Returns:
            Boolean: True if a nearby peak is detected
        """
        for minus_or_plus in [-1, 1]:
            temp = self.has_peak(self.ppm2abs(mz, self.measured_precision, minus_or_plus, 1))
            if temp and len(temp) > 1:
                return True
        return False

    def similarity_to(self, spec2: "Spectrum", round_precision: int = 0) -> float:
        """
        Compares two spectra and returns cosine.

        Arguments:
            spec2: another pymzml spectrum
            round_precision: precision mzs are rounded to

        Returns:
            cosine: value between 0 and 1
        """
        assert isinstance(spec2, Spectrum), "Spectrum 2 is not a pymzML spectrum"

        vector1: dict[float, float] = ddict(float)
        vector2: dict[float, float] = ddict(float)
        mzs: set[float] = set()

        raw_peaks_1 = self.peaks(PeakType.RAW)
        for mz, i in raw_peaks_1:
            rounded_mz = round(mz, round_precision)
            vector1[rounded_mz] += i
            mzs.add(rounded_mz)

        raw_peaks_2 = spec2.peaks(PeakType.RAW)
        for mz, i in raw_peaks_2:
            rounded_mz = round(mz, round_precision)
            vector2[rounded_mz] += i
            mzs.add(rounded_mz)

        z = 0.0
        n_v1 = 0.0
        n_v2 = 0.0

        for mz in mzs:
            int1 = vector1[mz]
            int2 = vector2[mz]
            z += int1 * int2
            n_v1 += int1 * int1
            n_v2 += int2 * int2

        try:
            cosine = z / (math.sqrt(n_v1) * math.sqrt(n_v2))
        except ZeroDivisionError:
            cosine = 0.0

        return cosine

    def transform_mz(self, value: float) -> int:
        """
        Transform m/z values into the internal standard.

        Arguments:
            value: m/z value

        Returns:
            transformed value: internally transformed mz value
        """
        return int(round(value * self.internal_precision))

    @property
    def centroidedPeaks(self) -> NDArray[np.float64]:
        return self.peaks(PeakType.CENTROIDED)


if __name__ == "__main__":
    print(__doc__)
