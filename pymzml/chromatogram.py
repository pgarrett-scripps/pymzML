from functools import cached_property
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .constants import ChromatogramMSAccession, XMLAttribute, chromatogram_type_accessions
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
        return self._decode(*self._get_encoding_parameters("time array"))

    @cached_property
    def i(self) -> NDArray[np.float64] | None:
        """Get intensity array. Decodes if needed."""
        return self._decode(*self._get_encoding_parameters("intensity array"))

    @cached_property
    def profile(self) -> NDArray[np.float64]:
        """Get chromatogram profile as (time, intensity) tuples. Can be set for theoretical data."""
        if self.time is None or self.i is None:
            return np.empty((0, 2), dtype=np.float64)

        min_len = min(len(self.time), len(self.i))
        return np.column_stack((self.time[:min_len], self.i[:min_len]))

    def peaks(self) -> NDArray[np.float64]:
        """Return chromatogram peaks as (time, intensity) tuples. Can be set for theoretical data."""
        return self.profile

    @cached_property
    def chromatogram_type(self) -> str | None:
        """Get chromatogram type."""
        for element in self.element.iter():
            if element.tag.endswith("}cvParam"):
                accession = element.get(XMLAttribute.ACCESSION)
                if accession in chromatogram_type_accessions:
                    return element.get(XMLAttribute.NAME)
        return None

    @cached_property
    def polarity(self) -> str | None:
        """Get polarity (positive or negative scan)."""
        for element in self.element.iter():
            if element.tag.endswith("}cvParam"):
                accession = element.get(XMLAttribute.ACCESSION)
                if accession in (
                    ChromatogramMSAccession.POSITIVE_SCAN,
                    ChromatogramMSAccession.NEGATIVE_SCAN,
                ):
                    return element.get(XMLAttribute.NAME)
        return None

    @cached_property
    def precursor_mz(self) -> float | None:
        """Get precursor m/z value for SRM/MRM chromatograms."""
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
                            return float(value)
        return None

    @property
    def product_mz(self) -> float | None:
        """Get product m/z value for SRM/MRM chromatograms."""
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
                            return float(value)
        return None

    def get_chromatogram_properties(self) -> dict[str, Any]:
        """Get chromatogram properties (id, type, polarity, precursor m/z, product m/z)."""
        return {
            "id": self.ID,
            "chromatogram_type": self.chromatogram_type,
            "polarity": self.polarity,
            "precursor_mz": self.precursor_mz,
            "product_mz": self.product_mz,
        }
