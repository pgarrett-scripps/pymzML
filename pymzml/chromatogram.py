"""
The chromatogram class offers a python object for mass spectrometry chromatogram data.
The chromatogram object holds the basic information of the chromatogram and offers
methods to interrogate properties of the chromatogram.
Data, i.e. time and intensity decoding is performed on demand
and can be accessed via their properties, e.g. :py:attr:`~pymzml.chromatogram.Chromatogram.peaks`.

The Chromatogram class is used in the :py:class:`~pymzml.run.Reader` class.
There each chromatogram is accessible as a chromatogram object.
"""

from typing import Any
from xml.etree.ElementTree import Element

import numpy as np
from numpy.typing import NDArray

from .msdata import MsData
from .constants import chromatogram_type_accessions


class Chromatogram(MsData):
    """
    Class for Chromatogram access and handling.
    """

    def __init__(
        self,
        element: Element | None,
        measured_precision: float = 5e-6,
        *,
        obo_version: str | None = None,
    ) -> None:
        """
        Arguments:
            element (xml.etree.ElementTree.Element): chromatogram as xml Element

        Keyword Arguments:
            measured_precision (float): in ppm, i.e. 5e-6 equals to 5 ppm.
            obo_version (str, optional): obo version number.
        """
        # Call parent class __init__
        super().__init__(element, measured_precision, obo_version=obo_version)

        # Chromatogram-specific attributes
        # Note: _time, _i, and _profile are inherited from MsData parent class
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
        """
        Returns representative string for a chromatogram object class
        """
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    def __str__(self) -> str:
        """
        Returns representative string for a chromatogram object class
        """
        return f"<__main__.Chromatogram object with native ID {self.ID} at {hex(id(self))}>"

    @property
    def ID(self) -> str | None:
        """
        Access the native id of the chromatogram.

        Returns:
            ID (str): native ID of the chromatogram
        """
        if self._id is None and self.element is not None:
            self._id: str | None = self.element.get("id")
        return self._id

    @property
    def mz(self) -> NDArray[np.float64] | None:
        """
        Chromatogram has no property mz. This property is included for
        compatibility with the Spectrum class.

        Returns:
            time (list): list of time values from the chromatogram
        """
        print("Chromatogram has no property mz.\nReturn retention time instead")
        return self.time

    @property
    def time(self) -> NDArray[np.float64] | None:
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
    def i(self) -> NDArray[np.float64] | None:
        """
        Returns the list of intensity values from the analyzed chromatogram.

        Returns:
            i (list): list of intensity values from the analyzed chromatogram
        """
        if self._i is None:
            params = self._get_encoding_parameters("intensity array")
            self._i = self._decode(*params)
        return self._i

    @property
    def profile(self) -> NDArray[np.float64]:
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
        ...     if isinstance(entry, pymzml.chromatogram.Chromatogram):
        ...         for time, intensity in entry.peaks:
        ...             print(time, intensity)

        Note:
           The peaks property can also be set, e.g. for theoretical data.
           It requires a list of time/intensity tuples.

        """
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
        """
        Return the list of peaks of the chromatogram as tuples (time, intensity).

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
        ...     if isinstance(entry, pymzml.chromatogram.Chromatogram):
        ...         for time, intensity in entry.peaks:
        ...             print(time, intensity)

        Note:
           The peaks property can also be set, e.g. for theoretical data.
           It requires a list of time/intensity tuples.

        """
        return self.profile

    @property
    def chromatogram_type(self) -> str | None:
        """
        Returns the chromatogram type.

        Returns:
            chromatogram_type (str): chromatogram type
        """
        if self._chromatogram_type is None and self.element is not None:
            for element in self.element.iter():
                if element.tag.endswith("}cvParam"):
                    accession = element.get("accession")
                    if accession in chromatogram_type_accessions:
                        self._chromatogram_type = element.get("name")
                        break
        return self._chromatogram_type

    @property
    def polarity(self) -> str | None:
        """
        Returns the polarity of the chromatogram.

        Returns:
            polarity (str): polarity (positive scan or negative scan)
        """
        if self._polarity is None and self.element is not None:
            for element in self.element.iter():
                if element.tag.endswith("}cvParam"):
                    accession = element.get("accession")
                    if accession in ("MS:1000129", "MS:1000130"):
                        self._polarity = element.get("name")
                        break
        return self._polarity

    @property
    def precursor_mz(self) -> float | None:
        """
        Returns the precursor m/z value for SRM/MRM chromatograms.

        Returns:
            precursor_mz (float): precursor m/z value
        """
        if self._precursor_mz is None and self.element is not None:
            precursor = self.element.find(f".//{self.ns}precursor")
            if precursor is not None:
                isolation_window = precursor.find(f".//{self.ns}isolationWindow")
                if isolation_window is not None:
                    for element in isolation_window.iter():
                        if (
                            element.tag.endswith("}cvParam")
                            and element.get("accession") == "MS:1000827"
                        ):
                            value = element.get("value")
                            if value is not None:
                                self._precursor_mz = float(value)
                            break
        return self._precursor_mz

    @property
    def product_mz(self) -> float | None:
        """
        Returns the product m/z value for SRM/MRM chromatograms.

        Returns:
            product_mz (float): product m/z value
        """
        if self._product_mz is None and self.element is not None:
            product = self.element.find(f".//{self.ns}product")
            if product is not None:
                isolation_window = product.find(f".//{self.ns}isolationWindow")
                if isolation_window is not None:
                    for element in isolation_window.iter():
                        if (
                            element.tag.endswith("}cvParam")
                            and element.get("accession") == "MS:1000827"
                        ):
                            value = element.get("value")
                            if value is not None:
                                self._product_mz = float(value)
                            break
        return self._product_mz

    def get_chromatogram_properties(self) -> dict[str, Any]:
        """
        Returns a dictionary with the main properties of the chromatogram.

        Returns:
            properties (dict): dictionary with chromatogram properties
        """
        return {
            "id": self.ID,
            "chromatogram_type": self.chromatogram_type,
            "polarity": self.polarity,
            "precursor_mz": self.precursor_mz,
            "product_mz": self.product_mz,
        }
