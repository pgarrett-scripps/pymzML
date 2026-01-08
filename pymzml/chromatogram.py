from typing import Any
from xml.etree.ElementTree import Element

import numpy as np
from numpy.typing import NDArray

from .constants import ChromatogramMSAccession, XMLAttribute, chromatogram_type_accessions
from .msdata import MsData


class Chromatogram(MsData):
    """Chromatogram object for accessing and handling chromatogram data."""

    def __init__(
        self,
        element: Element | None,
        measured_precision: float = 5e-6,
        *,
        obo_version: str | None = None,
    ) -> None:
        """Initialize Chromatogram from XML element."""
        # Call parent class __init__
        # Note: _time, _i, and _profile are inherited from MsData parent class
        super().__init__(element, measured_precision, obo_version=obo_version)

        # Chromatogram-specific attributes
        self._ms_level: int | None = None
        self._t_mass_set: Any = None
        self._peaks: NDArray[np.float64] | None = None
        self._t_mz_set: Any = None
        self._centroided_peaks: Any = None
        self._reprofiled_peaks: Any = None
        self._deconvoluted_peaks: Any = None
        self._extreme_values: Any = None
        self._centroided_peaks_sorted_by_i: Any = None
        self._transformed_mz_with_error: Any = None
        self._transformed_mass_with_error: Any = None
        self._precursors: Any = None
        self._id: str | None = None
        self._chromatogram_type: str | None = None
        self._precursor_mz: float | None = None
        self._product_mz: float | None = None
        self._polarity: str | None = None

    def __repr__(self) -> str:
        """String representation of Chromatogram object."""
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    def __str__(self) -> str:
        """String representation of Chromatogram object."""
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    @property
    def ms_level(self) -> None:
        return None

    @property
    def scan_time_in_minutes(self) -> None:
        return None

    @property
    def ID(self) -> str | None:
        """Get native ID of chromatogram."""
        if self._id is None and self.element is not None:
            self._id: str | None = self.element.get("id")
        return self._id

    @property
    def time(self) -> NDArray[np.float64] | None:
        """Get time array. Decodes if needed. Can be set for theoretical data."""
        if self._time is None:
            params = self._get_encoding_parameters("time array")
            self._time = self._decode(*params)
        return self._time

    @property
    def i(self) -> NDArray[np.float64] | None:
        """Get intensity array. Decodes if needed."""
        if self._i is None:
            params = self._get_encoding_parameters("intensity array")
            self._i = self._decode(*params)
        return self._i

    @property
    def profile(self) -> NDArray[np.float64]:
        """Get chromatogram profile as (time, intensity) tuples. Can be set for theoretical data."""
        if self._profile is None or isinstance(self._profile, bool):
            if self._time is not None and self._i is not None:
                time_data = self.time
                i_data = self.i
                if time_data is not None and i_data is not None:
                    self._profile = np.array(
                        [[t, i_data[pos]] for pos, t in enumerate(time_data)], dtype=np.float64
                    )
                else:
                    self._profile = np.array([], dtype=np.float64).reshape(0, 2)
            else:
                self._profile = np.array([], dtype=np.float64).reshape(0, 2)
        return self._profile

    @profile.setter
    def profile(self, tuple_list: list[tuple[float, float]]) -> None:
        """
        Set the chromatogram profile.

        Args:
            tuple_list (list): list of tuples (time, intensity)
        """
        if len(tuple_list) == 0:
            self._time = np.array([], dtype=np.float64)
            self._i = np.array([], dtype=np.float64)
            self._peaks = np.array([], dtype=np.float64).reshape(0, 2)
            return
        time_list: list[float] = []
        i_list: list[float] = []
        for time, i in tuple_list:
            time_list.append(time)
            i_list.append(i)
        self._time = np.array(time_list, dtype=np.float64)
        self._i = np.array(i_list, dtype=np.float64)
        self._peaks = np.array(tuple_list, dtype=np.float64)
        self._reprofiledPeaks = None
        self._centroidedPeaks = None

    def peaks(self) -> NDArray[np.float64]:
        """Return chromatogram peaks as (time, intensity) tuples. Can be set for theoretical data."""
        return self.profile

    @property
    def chromatogram_type(self) -> str | None:
        """Get chromatogram type."""
        if self._chromatogram_type is None and self.element is not None:
            for element in self.element.iter():
                if element.tag.endswith("}cvParam"):
                    accession = element.get(XMLAttribute.ACCESSION)
                    if accession in chromatogram_type_accessions:
                        self._chromatogram_type = element.get(XMLAttribute.NAME)
                        break
        return self._chromatogram_type

    @property
    def polarity(self) -> str | None:
        """Get polarity (positive or negative scan)."""
        if self._polarity is None and self.element is not None:
            for element in self.element.iter():
                if element.tag.endswith("}cvParam"):
                    accession = element.get(XMLAttribute.ACCESSION)
                    if accession in (
                        ChromatogramMSAccession.POSITIVE_SCAN,
                        ChromatogramMSAccession.NEGATIVE_SCAN,
                    ):
                        self._polarity = element.get(XMLAttribute.NAME)
                        break
        return self._polarity

    @property
    def precursor_mz(self) -> float | None:
        """Get precursor m/z value for SRM/MRM chromatograms."""
        if self._precursor_mz is None and self.element is not None:
            precursor = self.element.find(f".//{self.ns}precursor")
            if precursor is not None:
                isolation_window = precursor.find(f".//{self.ns}isolationWindow")
                if isolation_window is not None:
                    for element in isolation_window.iter():
                        if (
                            element.tag.endswith("}cvParam")
                            and element.get(XMLAttribute.ACCESSION)
                            == ChromatogramMSAccession.ISOLATION_WINDOW_TARGET_MZ
                        ):
                            value = element.get("value")
                            if value is not None:
                                self._precursor_mz = float(value)
                            break
        return self._precursor_mz

    @property
    def product_mz(self) -> float | None:
        """Get product m/z value for SRM/MRM chromatograms."""
        if self._product_mz is None and self.element is not None:
            product = self.element.find(f".//{self.ns}product")
            if product is not None:
                isolation_window = product.find(f".//{self.ns}isolationWindow")
                if isolation_window is not None:
                    for element in isolation_window.iter():
                        if (
                            element.tag.endswith("}cvParam")
                            and element.get(XMLAttribute.ACCESSION)
                            == ChromatogramMSAccession.ISOLATION_WINDOW_TARGET_MZ
                        ):
                            value = element.get("value")
                            if value is not None:
                                self._product_mz = float(value)
                            break
        return self._product_mz

    def get_chromatogram_properties(self) -> dict[str, Any]:
        """Get chromatogram properties (id, type, polarity, precursor m/z, product m/z)."""
        return {
            "id": self.ID,
            "chromatogram_type": self.chromatogram_type,
            "polarity": self.polarity,
            "precursor_mz": self.precursor_mz,
            "product_mz": self.product_mz,
        }
