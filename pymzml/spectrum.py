import contextlib
import logging
import math
from collections import defaultdict as ddict
from functools import cached_property, lru_cache
from operator import itemgetter as itemgetter
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from . import regex_patterns
from .constants import (
    BinaryDataArrayAccession,
    DataType,
    NoiseMode,
    PeakType,
    SpectrumMSAccession,
    SpectrumType,
    TimeUnit,
)
from .msdata import MsData
from .utils import centroid_peaks_numpy, filter_noise, filter_range

logger = logging.getLogger(__name__)


class Spectrum(MsData):
    def __repr__(self) -> str:
        """String representation of Spectrum object."""
        return f"Spectrum(ID='{self.ID}', level={self.ms_level})"

    def __str__(self) -> str:
        """String representation of Spectrum object."""
        return self.__repr__()

    @lru_cache
    def __getitem__(self, accession: str) -> list[str] | None:
        """Get spectrum XML information by accession tag"""

        search_string = f'.//*[@accession="{accession}"]'
        elements: list[str] = []
        for x in self.element.iterfind(search_string):
            val = x.attrib.get("value", "")
            elements.append(val)

        if not elements:
            return None

        return elements

    def get(self, acc: str, default: Any | None = None) -> Any:
        """Get accession value with default fallback (like dict.get)."""
        val = self[acc]
        return default if val is None else val

    def __contains__(self, value: str) -> bool:
        """Check if MS tag or name exists in spectrum."""
        return self[value] is not None

    @cached_property
    def TIC(self) -> float | None:
        """Get total ion current (TIC) for this spectrum."""

        tic_element = self.element.find(
            f"./{self.ns}cvParam[@accession='{SpectrumMSAccession.TOTAL_ION_CURRENT}']"
        )
        if tic_element is not None:
            value_str = tic_element.get("value")
            if value_str is not None:
                return float(value_str)

        return None

    @cached_property
    def ID(self) -> str | None:
        """Get native ID of spectrum."""
        return self.element.get("id")

    @cached_property
    def controller_type(self) -> int | None:
        """Get controller type from ID."""
        if self.ID is None:
            raise ValueError("Spectrum ID is None")
        match = regex_patterns.SPECTRUM_CONTROLLER_TYPE_PATTERN.search(self.ID)
        if match:
            return int(match.group(1))
        return None

    @cached_property
    def controller_number(self) -> int | None:
        """Get controller number from ID."""
        if self.ID is None:
            raise ValueError("Spectrum ID is None")
        match = regex_patterns.SPECTRUM_CONTROLLER_NUMBER_PATTERN.search(self.ID)
        if match:
            return int(match.group(1))
        return None

    @cached_property
    def scan(self) -> int | None:
        """Get scan number from ID."""
        if self.ID is None:
            raise ValueError("Spectrum ID is None")
        match = regex_patterns.SPECTRUM_SCAN_PATTERN.search(self.ID)
        if match:
            return int(match.group(1))
        return None

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
    def _scan_time(self) -> tuple[float | None, str | None]:
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
            scan_time_unit = scan_time_ele.get("unitName")

        if scan_time_unit is None:
            raise ValueError("Scan time unit is None.")

        return scan_time, scan_time_unit

    @property
    def scan_unit(self) -> str | None:
        """Get scan time unit."""
        _, scan_unit = self._scan_time
        return scan_unit

    @property
    def scan_time(self) -> float | None:
        """Get scan time value."""
        scan_time, _ = self._scan_time
        return scan_time

    @property
    def scan_time_seconds(self) -> float:
        """Get scan time in seconds."""
        return self._transform_scan_time(TimeUnit.SECOND)

    @property
    def scan_time_minutes(self) -> float:
        """Get scan time in minutes."""
        return self._transform_scan_time(TimeUnit.MINUTE)

    def _transform_scan_time(self, time_unit: TimeUnit = TimeUnit.SECOND) -> float:
        scan_time, scan_unit = self._scan_time

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
                return scan_time_in_minutes * 60.0 * 1000.0
            case TimeUnit.SECOND:
                return scan_time_in_minutes * 60.0
            case TimeUnit.MINUTE:
                return scan_time_in_minutes
            case TimeUnit.HOUR:
                return scan_time_in_minutes / 60.0

    @cached_property
    def spectrum_type(self) -> str:
        """Get spectrum type (centroid / profile / unknown)."""
        return (
            "centroid"
            if SpectrumType.CENTROID in self.accessions
            else "profile"
            if SpectrumType.PROFILE in self.accessions
            else "unknown"
        )

    @cached_property
    def is_profile(self) -> bool:
        """Check if spectrum is profile type."""
        return self.spectrum_type == "profile"

    @cached_property
    def is_centroid(self) -> bool:
        """Check if spectrum is centroid type."""
        return self.spectrum_type == "centroid"

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
    def cpeaks(self) -> NDArray[np.float64] | None:
        """Centroid peaks using Gaussian fitting if profile spectrum."""
        match peak_type := self.spectrum_type:
            case "centroid":
                logger.debug(f"Spectrum {self.ID} is already centroided.")
                return self.raw_peaks
            case "profile":
                logger.debug(f"Spectrum {self.ID} is profile, centroiding now.")
                return (
                    centroid_peaks_numpy(raw_peaks)
                    if (raw_peaks := self.raw_peaks) is not None
                    else None
                )
            case "unknown":
                logger.exception(f"Spectrum {self.ID} has unknown type, cannot centroid.")
                raise RuntimeError(f"Spectrum {self.ID} has unknown type, cannot centroid.")
            case _:
                raise RuntimeError(f"Should not reach here: unknown spectrum type {peak_type}.")

    @cached_property
    def ppeaks(self) -> NDArray[np.float64] | None:
        match peak_type := self.spectrum_type:
            case "profile":
                logger.debug(f"Spectrum {self.ID} is already profile.")
                return self.raw_peaks
            case "centroid":
                logger.warning(f"Spectrum {self.ID} is centroided, cannot get profile peaks.")
                raise RuntimeError(f"Spectrum {self.ID} is centroided, cannot get profile peaks.")
            case "unknown":
                logger.exception(f"Spectrum {self.ID} has unknown type, cannot get profile peaks.")
                raise RuntimeError(
                    f"Spectrum {self.ID} has unknown type, cannot get profile peaks."
                )
            case _:
                raise RuntimeError(f"Should not reach here: unknown spectrum type {peak_type}.")

    @cached_property
    def dpeaks(self) -> NDArray[np.float64] | None:
        """Deconvolute peaks using ms_deisotope."""
        logger.debug(f"Deconvoluting spectrum {self.ID}")
        from ms_deisotope.deconvolution import deconvolute_peaks  # type: ignore
        from ms_peak_picker import simple_peak  # type: ignore

        peaks = self.cpeaks

        if peaks is None:
            logger.warning(f"Spectrum {self.ID} has no centroid peaks, cannot deconvolute.")
            return None

        # Pack peak matrix into expected structure
        peak_list = [simple_peak(p[0], p[1], 0.01) for p in peaks]
        decon_result = deconvolute_peaks(peak_list)
        dpeaks = decon_result.peak_set

        # Pack deconvoluted peak list into matrix structure
        dpeaks_mat = np.zeros((len(dpeaks), 3), dtype=np.float64)
        for i, dp in enumerate(dpeaks):
            dpeaks_mat[i, :] = dp.neutral_mass, dp.intensity, dp.charge

        return dpeaks_mat

    @property
    def raw_peaks(self) -> NDArray[np.float64] | None:
        """Get raw peaks as numpy array without any processing."""
        if self.mz is None or self.intensity is None:
            return None

        arr = np.stack((self.mz, self.intensity), axis=-1)
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
    ) -> NDArray[np.float64] | None:
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

        if peaks is None:
            return None

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

    @cached_property
    def mz(self) -> NDArray[np.float64] | None:
        """Get m/z array from the spectrum."""
        return self.decode_binary_data_array(BinaryDataArrayAccession.MZ_ARRAY)

    @cached_property
    def intensity(self) -> NDArray[np.float64] | None:
        """Get intensity array from the spectrum."""
        return self.decode_binary_data_array(BinaryDataArrayAccession.INTENSITY_ARRAY)

    def get_array(self, arr_name: str) -> NDArray[np.float64] | None:
        """Get a specific data array by name from the spectrum."""
        array = self.decode_binary_data_array(arr_name)
        return array

    def get_tims_tof_ion_mobility(
        self,
        array_name: str = BinaryDataArrayAccession.MEAN_INVERSE_REDUCED_ION_MOBILITY_ARRAY,
    ) -> NDArray[np.float64] | None:
        """Get TIMS TOF ion mobility array."""
        return self.get_array(array_name)

    @property
    def mean_inverse_reduced_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.MEAN_INVERSE_REDUCED_ION_MOBILITY_ARRAY)

    @property
    def raw_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.RAW_ION_MOBILITY_ARRAY)

    @property
    def mean_ion_mobility_drift_time(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.MEAN_ION_MOBILITY_DRIFT_TIME_ARRAY)

    @property
    def deconvoluted_ion_mobility_drift_time(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.DECONVOLUTED_ION_MOBILITY_DRIFT_TIME_ARRAY)

    @property
    def mean_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.MEAN_ION_MOBILITY_ARRAY)

    @property
    def deconvoluted_inverse_reduced_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(
            BinaryDataArrayAccession.DECONVOLUTED_INVERSE_REDUCED_ION_MOBILITY_ARRAY
        )

    @property
    def raw_ion_mobility_drift_time(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.RAW_ION_MOBILITY_DRIFT_TIME_ARRAY)

    @property
    def raw_inverse_reduced_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.RAW_INVERSE_REDUCED_ION_MOBILITY_ARRAY)

    @property
    def deconvoluted_ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.DECONVOLUTED_ION_MOBILITY_ARRAY)

    @property
    def mean_charge(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.MEAN_CHARGE_ARRAY)

    @property
    def sampled_noise_intensity(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.SAMPLED_NOISE_INTENSITY_ARRAY)

    @property
    def charge_array(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.CHARGE_ARRAY)

    @property
    def sampled_noise_baseline(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.SAMPLED_NOISE_BASELINE_ARRAY)

    @property
    def ion_mobility(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.ION_MOBILITY_ARRAY)

    @property
    def baseline(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.BASELINE_ARRAY)

    @property
    def resolution(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.RESOLUTION_ARRAY)

    @property
    def scanning_quadrupole_position_upper_bound_mz(self) -> NDArray[np.float64] | None:
        return self.get_array(
            BinaryDataArrayAccession.SCANNING_QUADRUPOLE_POSITION_UPPER_BOUND_MZ_ARRAY
        )

    @property
    def scanning_quadrupole_position_lower_bound_mz(self) -> NDArray[np.float64] | None:
        return self.get_array(
            BinaryDataArrayAccession.SCANNING_QUADRUPOLE_POSITION_LOWER_BOUND_MZ_ARRAY
        )

    @property
    def noise(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.NOISE_ARRAY)

    @property
    def signal_to_noise(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.SIGNAL_TO_NOISE_ARRAY)

    @property
    def sampled_noise_mz(self) -> NDArray[np.float64] | None:
        return self.get_array(BinaryDataArrayAccession.SAMPLED_NOISE_MZ_ARRAY)

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

        if peaks is None:
            return []

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
        raw_peaks_2 = spec2.peaks(peak_type)

        if raw_peaks_1 is None or raw_peaks_2 is None:
            return 0.0

        for mz, i in raw_peaks_1:
            rounded_mz = round(mz, round_precision)
            vector1[rounded_mz] += i
            mzs.add(rounded_mz)

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
