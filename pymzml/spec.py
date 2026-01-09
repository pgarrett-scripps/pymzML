import contextlib
import logging
import math
import xml.etree.ElementTree as ElementTree
from collections import defaultdict as ddict
from functools import cached_property, lru_cache
from operator import itemgetter as itemgetter
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from . import regex_patterns
from .constants import (
    PROTON_MASS,
    DataType,
    NoiseMode,
    PeakType,
    SpectrumMSAccession,
    TimeUnit,
)
from .msdata import MsData
from .utils.utils import filter_noise, filter_range

logger = logging.getLogger(__name__)


def centroid_peaks_numpy(peaks: NDArray[np.float64]) -> NDArray[np.float64]:
    """Centroid peaks using numpy-optimized vectorized Gaussian fitting."""
    i_array = np.asarray(peaks[:, 1], dtype=np.float64)
    mz_array = np.asarray(peaks[:, 0], dtype=np.float64)

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


class Spectrum(MsData):

    def __repr__(self) -> str:
        """String representation of Spectrum object."""
        return f"<__main__.Spectrum object with native ID {self.ID} at {hex(id(self))}>"

    def __str__(self) -> str:
        """String representation of Spectrum object."""
        return f"<__main__.Spectrum object with native ID {self.ID} at {hex(id(self))}>"

    @lru_cache  # noqa: B019
    def __getitem__(self, accession: str) -> str | float | bool | list[str | float] | None:
        """Get spectrum XML information by accession tag or OBO name."""
        if accession == "id":
            return self.ID

        # First try searching by accession
        search_string = f'.//*[@accession="{accession}"]'
        elements: list[float | str] = []
        for x in self.element.iterfind(search_string):
            val = x.attrib.get("value", "")
            with contextlib.suppress(ValueError):
                val = float(val)
            elements.append(val)

        # If no results, try searching by name
        if len(elements) == 0:
            search_string = f'.//*[@name="{accession}"]'
            for x in self.element.iterfind(search_string):
                val = x.attrib.get("value", "")
                with contextlib.suppress(ValueError):
                    val = float(val)
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
        """Get accession value with default fallback (like dict.get)."""
        val = self[acc]
        return default if val is None else val

    def __contains__(self, value: str) -> bool:
        """Check if MS tag or name exists in spectrum."""
        return self[value] is not None

    @cached_property
    def TIC(self) -> float:
        """Get total ion current (TIC) for this spectrum."""

        tic_element = self.element.find(
            f"./{self.ns}cvParam[@accession='{SpectrumMSAccession.TOTAL_ION_CURRENT}']"
        )
        if tic_element is not None:
            value_str = tic_element.get("value")
            if value_str is not None:
                return float(value_str)
        return 0.0

    @cached_property
    def ID(self) -> str | None:
        """Get native ID of spectrum."""
        return self.element.get("id")

    @cached_property
    def id_dict(self) -> MappingProxyType[str, str | int]:
        """Get all key-value pairs from spectrum ID attribute."""
        tuples: list[tuple[str, str | int]] = []
        spec_id = self.element.attrib.get("id", "")
        matches = regex_patterns.SPECTRUM_PATTERN3.findall(spec_id)
        id_dict = {}
        if matches:
            for k, v in matches:
                k = k.strip()
                v = v.strip()
                with contextlib.suppress(ValueError):
                    v = int(v)
                tuples.append((k, v))
            id_dict = dict(tuples)
        else:
            id_dict = {}
        return MappingProxyType(id_dict)

    @cached_property
    def index(self) -> int | str | None:
        """Get 0-based index of spectrum."""
        index = None
        index = self.element.get("index")
        if index:
            with contextlib.suppress(ValueError):
                index = int(index)
        return index

    @cached_property
    def ms_level(self) -> int | None:
        """Get MS level of spectrum (MS1, MS2, etc)."""
        ms_level = None
        sub_element = self.element.find(
            f".//{self.ns}cvParam[@accession='{SpectrumMSAccession.MS_LEVEL}']"
        )
        if sub_element is not None:
            value_str = sub_element.get("value")
            if value_str is not None:
                ms_level = int(value_str)
        return ms_level

    @cached_property
    def scan_time(self) -> tuple[float | None, str | None]:
        """Get scan time (retention time) and its unit."""
        scan_time = None
        scan_time_unit = None
        scan_time_ele = self.element.find(
            f".//*[@accession='{SpectrumMSAccession.SCAN_START_TIME}']"
        )
        if scan_time_ele is not None:
            value_str = scan_time_ele.attrib.get("value")
            if value_str is not None:
                scan_time = float(value_str)
            scan_time_unit = scan_time_ele.get("unitName", "unicorns")
        return scan_time, scan_time_unit

    def transform_scan_time(
        self, time_unit: TimeUnit = TimeUnit.SECOND
    ) -> tuple[float | None, str | None]:
        scan_time, scan_unit = self.scan_time

        if scan_time is None or scan_unit is None:
            raise ValueError("Scan time or scan unit is None.")

        unit_lower = scan_unit.lower()
        match unit_lower:
            case TimeUnit.MILLISECOND:
                scan_time_in_minutes = scan_time / 1000.0 / 60.0
            case TimeUnit.SECOND:
                scan_time_in_minutes = scan_time / 60.0
            case TimeUnit.MINUTE:
                scan_time_in_minutes = scan_time
            case TimeUnit.HOUR:
                scan_time_in_minutes = scan_time * 60.0
            case _:
                raise ValueError(f"Time unit '{scan_unit}' unknown")

        match time_unit:
            case TimeUnit.MILLISECOND:
                return scan_time_in_minutes * 60.0 * 1000.0, TimeUnit.MILLISECOND
            case TimeUnit.SECOND:
                return scan_time_in_minutes * 60.0, TimeUnit.SECOND
            case TimeUnit.MINUTE:
                return scan_time_in_minutes, TimeUnit.MINUTE
            case TimeUnit.HOUR:
                return scan_time_in_minutes / 60.0, TimeUnit.HOUR

    @cached_property
    def selected_precursors(self) -> tuple[MappingProxyType[str, Any], ...]:
        """Get selected precursors for MS2 spectrum."""
        selected_precursor_mzs = self.element.findall(
            f".//*[@accession='{SpectrumMSAccession.SELECTED_ION_MZ}']"
        )
        selected_precursor_is = self.element.findall(
            f".//*[@accession='{SpectrumMSAccession.PEAK_INTENSITY}']"
        )
        selected_precursor_cs = self.element.findall(
            f".//*[@accession='{SpectrumMSAccession.CHARGE_STATE}']"
        )
        precursors = self.element.findall(f"./{self.ns}precursorList/{self.ns}precursor")

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
            (DataType.INTENSITY, i_values),
            ("charge", charges),
            ("precursor id", ids),
            ("element", precursors),
        ]

        selected_precursors: list[MappingProxyType[str, Any]] = []
        for pos, mz in enumerate(mz_values):
            dict_2_save: dict[str, Any] = {DataType.MZ: mz}
            for key, list_of_values in _vals:
                if pos < len(list_of_values):
                    dict_2_save[key] = list_of_values[pos]
            selected_precursors.append(MappingProxyType(dict_2_save))

        return tuple(selected_precursors)

    @cached_property
    def precursors(self) -> tuple[str, ...]:
        """Get list of precursor IDs."""
        # self.deprecation_warning(sys._getframe().f_code.co_name)
        precursors_elems = self.element.findall(f"./{self.ns}precursorList/{self.ns}precursor")
        precursors: list[str] = []
        for prec in precursors_elems:
            spec_ref = prec.get("spectrumRef")
            if spec_ref:
                match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_ref)
                if match:
                    precursors.append(match.group(1))
        return tuple(precursors)

    @cached_property
    def cpeaks(self) -> NDArray[np.float64]:
        return self._centroid_peaks()

    @cached_property
    def ppeaks(self) -> NDArray[np.float64]:
        return self._profile_peaks()

    @cached_property
    def dpeaks(self) -> NDArray[np.float64]:
        return self._deconvolute_peaks()

    @cached_property
    def raw_peaks(self) -> NDArray[np.float64]:
        """Get raw peaks as numpy array without any processing."""
        mz_params = self._get_encoding_parameters("m/z array")
        i_params = self._get_encoding_parameters("intensity array")
        mz = self._decode(*mz_params)
        i = self._decode(*i_params)
        arr = np.stack((mz, i), axis=-1)
        return arr

    def peaks(
        self,
        peak_type: str | PeakType = PeakType.CENTROIDED,
        mz_range: tuple[float | None, float | None] = (None, None),
        apply_noise_filter: bool = False,
        mode: str | NoiseMode = NoiseMode.MEDIAN,
        noise_level: float | None = None,
        signal_to_noise_threshold: float = 1.0,
        sort_by: Literal["mz", "i"] | None = None,
    ) -> NDArray[np.float64]:
        """Get peaks as numpy array (profile, centroided, or deconvoluted)."""
        # Convert string to enum if needed
        if isinstance(peak_type, str):  # type: ignore
            peak_type = PeakType(peak_type)

        match peak_type:
            case PeakType.PROFILE:
                peaks = self.ppeaks
            case PeakType.CENTROIDED:
                peaks = self.cpeaks
            case PeakType.DECONVOLUTED:
                peaks = self.dpeaks
            case _:
                raise ValueError(f"Unknown peak type: {peak_type}")

        if mz_range != (None, None):
            peaks = filter_range(peaks, mz_range)

        if apply_noise_filter:
            peaks = filter_noise(peaks, mode, noise_level, signal_to_noise_threshold)

        if sort_by is not None:
            if sort_by == "mz":
                peaks = peaks[peaks[:, 0].argsort()]
            elif sort_by == "i":
                peaks = peaks[peaks[:, 1].argsort()]
            else:
                raise ValueError(f"Unknown sort_by value: {sort_by}")

        return peaks

    @property
    def mz(self) -> NDArray[np.float64]:
        """Get m/z array from the spectrum."""
        return self.cpeaks[:, 0]

    @property
    def i(self) -> NDArray[np.float64]:
        """Get intensity array from the spectrum."""
        return self.cpeaks[:, 1]

    def get_array(self, arr_name: str) -> NDArray[np.float64] | None:
        """Get a specific data array by name from the spectrum."""
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
        b_data_arrays = self.element.findall(b_data_string)
        array_names = [arr.attrib["name"] for arr in b_data_arrays]

        if not_found_array is not None:
            formatted_names = [f"\t- {name}" for name in array_names]
            print(f"Requested array ({not_found_array}) not found.\nAvailable arrays are:")
            print("\n".join(formatted_names))

        return array_names

    def _deconvolute_peaks(self, *args: Any, **kwargs: Any) -> NDArray[np.float64]:
        """Deconvolute peaks using ms_deisotope."""
        logger.debug(f"Deconvoluting spectrum {self.ID}")
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

    """
    @property
    def _is_profile(self) -> bool | None:
        # TODO: ALREADY IN MSDATA? SHOULD I REMOVE THIS?
        try:
            profile_ot = self.obo_translator.name.get(
                "profile spectrum"
            ) or self.obo_translator.name.get("profile mass spectrum")
            if profile_ot:
                acc = profile_ot["id"]
                is_profile = self.element.find(f".//*[@accession='{acc}']") is not None
            else:
                is_profile = None
        except (TypeError, AttributeError):
            is_profile = None

        return is_profile
    """

    def _centroid_peaks(self) -> NDArray[np.float64]:
        """Centroid peaks using Gaussian fitting if profile spectrum."""
        logger.debug(f"Centroiding spectrum {self.ID}")

        if self.is_profile:
            return centroid_peaks_numpy(self.raw_peaks)
        else:
            return self.raw_peaks  # raw peaks are already centroided

    def _profile_peaks(self) -> NDArray[np.float64]:
        logger.debug(f"Reprofiling spectrum {self.ID}")
        if not self.is_profile:
            return self.raw_peaks  # raw peaks are already profile
        else:
            raise NotImplementedError("Reprofiling of profile spectra is not implemented.")

    def _mz_2_mass(self, mz: float, charge: int) -> float:
        """Calculate uncharged mass from m/z and charge."""
        return (mz - PROTON_MASS) * charge

    # TODO: Update this
    def set_params_from_reference_group(self, ref_element: ElementTree.Element) -> None:
        """Set parameters from reference group."""
        ref = self.element.find(f"{self.ns}referenceableParamGroupRef")
        if ref is not None:
            ref_id = ref.get("ref")
            ele = ref_element.find(f".//*[@id='{ref_id}']")
            if ele is not None and ref_id == ele.get("id"):
                for param in ele.iter():
                    self.element.append(param)

    def ppm2abs(
        self, value: float, ppm_value: float, direction: int = 1, factor: float = 1
    ) -> float:
        """Calculate absolute error for m/z value given ppm precision."""
        return value + (value * (ppm_value * factor)) * direction

    def find_peaks(
        self,
        mz: float,
        tolerance: float,
        ppm_tol: bool = True,
        peak_type: PeakType = PeakType.CENTROIDED,
    ) -> list[tuple[float, float]]:
        """Check if spectrum has peak at given m/z within precision tolerance."""
        peaks = self.peaks(peak_type)

        tolerance_offset = mz * (tolerance / 1_000_000) if ppm_tol else tolerance
        mz_min = mz - tolerance_offset
        mz_max = mz + tolerance_offset

        matched_peaks = [
            (mz_val, intensity) for mz_val, intensity in peaks if mz_min <= mz_val <= mz_max
        ]
        if matched_peaks:
            return matched_peaks
        return []

    def has_peak(
        self,
        mz: float,
        tolerance: float,
        ppm_tol: bool = True,
        peak_type: PeakType = PeakType.CENTROIDED,
    ) -> list[tuple[float, float]] | None:
        """Check if spectrum has peak at given m/z within precision tolerance."""

        matched_peaks = self.find_peaks(mz, tolerance, ppm_tol, peak_type)
        if matched_peaks:
            return matched_peaks
        return None

    def has_overlapping_peak(
        self,
        mz: float,
        tolerance: float,
        ppm_tol: bool = True,
        peak_type: PeakType = PeakType.CENTROIDED,
    ) -> bool:
        """Check if spectrum has multiple peaks near given m/z."""
        matched_peaks = self.find_peaks(mz, tolerance, ppm_tol, peak_type)
        return len(matched_peaks) > 1

    def similarity_to(
        self, spec2: "Spectrum", round_precision: int = 0, peak_type: PeakType = PeakType.CENTROIDED
    ) -> float:
        """Compute cosine similarity between two spectra."""
        assert isinstance(spec2, Spectrum), "Spectrum 2 is not a pymzML spectrum"

        vector1: dict[float, float] = ddict(float)
        vector2: dict[float, float] = ddict(float)
        mzs: set[float] = set()

        raw_peaks_1 = self.peaks(peak_type)
        for mz, i in raw_peaks_1:
            rounded_mz = round(mz, round_precision)
            vector1[rounded_mz] += i
            mzs.add(rounded_mz)

        raw_peaks_2 = spec2.peaks(peak_type)
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
