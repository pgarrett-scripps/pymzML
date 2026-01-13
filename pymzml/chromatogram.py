from functools import cached_property
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .constants import (
    ISOLATION_WINDOW_TARGET_MZ,
    BinaryDataArrayAccession,
    ChromatogramType,
    XMLAttribute,
)
from .msdata import MsData


class Chromatogram(MsData):
    def __repr__(self) -> str:
        """String representation of Chromatogram object."""
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    def __str__(self) -> str:
        """String representation of Chromatogram object."""
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    @cached_property
    def ID(self) -> str | None:
        """Get native ID of chromatogram."""
        return self.element.get("id")

    @cached_property
    def time(self) -> NDArray[np.float64] | None:
        """Get time array. Decodes if needed. Can be set for theoretical data."""
        return self.decode_binary_data_array(BinaryDataArrayAccession.TIME_ARRAY)

    @cached_property
    def i(self) -> NDArray[np.float64] | None:
        """Get intensity array. Decodes if needed."""
        return self.decode_binary_data_array(BinaryDataArrayAccession.INTENSITY_ARRAY)

    @property
    def flow_rate(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.FLOW_RATE_ARRAY)

    @property
    def pressure(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.PRESSURE_ARRAY)

    @property
    def vacuum_pump_pressure(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.VACUUM_PUMP_PRESSURE)

    @property
    def temperature(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.TEMPERATURE_ARRAY)

    @property
    def wavelength(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.WAVELENGTH_ARRAY)

    @property
    def mass(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.MASS_ARRAY)

    @property
    def non_standard_data(self) -> NDArray[np.float64] | None:
        return self.decode_binary_data_array(BinaryDataArrayAccession.NON_STANDARD_DATA_ARRAY)

    @cached_property
    def profile(self) -> NDArray[np.float64] | None:
        """Get chromatogram profile as (time, intensity) tuples."""

        if self.time is None or self.i is None:
            return None

        if len(self.time) != len(self.i):
            raise ValueError("Time and intensity arrays have different lengths.")

        return np.column_stack((self.time, self.i))

    @cached_property
    def chromatogram_type(self) -> ChromatogramType | None:
        """Get chromatogram type."""
        for element in self.element.iter():
            if element.tag.endswith("}cvParam"):
                accession = element.get(XMLAttribute.ACCESSION)

                try:
                    return ChromatogramType(accession)
                except ValueError:
                    continue

        return None

    def _get_isolation_window_mz(self, parent_tag: str) -> float | None:
        """Extract target m/z from isolation window of precursor or product."""
        parent = self.element.find(f".//{self.ns}{parent_tag}")
        if parent is None:
            return None

        isolation_window = parent.find(f".//{self.ns}isolationWindow")
        if isolation_window is None:
            return None

        # Find cvParam with target m/z accession
        for elem in isolation_window.iter():
            if (
                elem.tag.endswith("}cvParam")
                and elem.get(XMLAttribute.ACCESSION) == ISOLATION_WINDOW_TARGET_MZ
            ):
                if value := elem.get("value"):
                    return float(value)

        return None

    @cached_property
    def precursor_mz(self) -> float | None:
        """Get precursor m/z value for SRM/MRM chromatograms."""
        return self._get_isolation_window_mz("precursor")

    @property
    def product_mz(self) -> float | None:
        """Get product m/z value for SRM/MRM chromatograms."""
        return self._get_isolation_window_mz("product")

    def get_chromatogram_properties(self) -> dict[str, Any]:
        """Get chromatogram properties (id, type, polarity, precursor m/z, product m/z)."""
        return {
            "id": self.ID,
            "chromatogram_type": self.chromatogram_type,
            "polarity": self.polarity,
            "precursor_mz": self.precursor_mz,
            "product_mz": self.product_mz,
        }
