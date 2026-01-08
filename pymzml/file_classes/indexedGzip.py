import codecs
import gzip
from collections import OrderedDict
from xml.etree.ElementTree import XML

from .. import chromatogram, spec
from ..utils.gzip_reader import GzipReader


class IndexedGzip:
    """mzML reader with pre-built index for efficient random access to gzipped files."""

    def __init__(self, path: str, encoding: str) -> None:
        self.path: str = path
        self.file_handler = codecs.getreader(encoding)(gzip.open(path))  # noqa: SIM115
        self.offset_dict: OrderedDict[int | str, int] = OrderedDict()
        self._build_index()

    def __del__(self) -> None:
        self.Reader.close()
        self.file_handler.close()

    def _build_index(self) -> None:
        self.Reader: GzipReader = GzipReader(self.path)
        self.offset_dict: OrderedDict[int | str, int] = self.Reader.index

    def read(self, size: int = -1) -> str:
        return self.file_handler.read(size)

    def get_spectrum_by_id(self, spectrum_id: int | str) -> spec.Spectrum:
        """Retrieve spectrum by its native ID.

        Raises:
            KeyError: If spectrum ID is not found.
        """
        if spectrum_id not in self.offset_dict:
            raise KeyError(f"Spectrum ID {spectrum_id} not found in file")

        ns_prefix = (
            '<mzML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation='
            '"http://psi.hupo.org/ms/mzml http://psidev.info/files/ms/mzML/xsd/mzML1.1.0.xsd" id="test_Creinhardtii_QE_pH8"'
            ' version="1.1.0" xmlns="http://psi.hupo.org/ms/mzml">'
        )
        ns_suffix = "</mzML>"
        data = self.Reader.read_block(spectrum_id)
        element = XML(ns_prefix + data.decode("utf-8") + ns_suffix)
        if "chromatogram" in element[0].tag:
            raise ValueError(f"ID {spectrum_id} refers to a chromatogram, not a spectrum")
        return spec.Spectrum(list(element)[0], measured_precision=5e-6)

    def get_spectrum_by_index(self, index: int) -> spec.Spectrum:
        """Retrieve spectrum by 0-based index.

        Raises:
            IndexError: If index is out of range.
        """
        numeric_keys = [k for k in self.offset_dict if isinstance(k, int)]
        if not (0 <= index < len(numeric_keys)):
            raise IndexError(f"Index {index} out of range [0, {len(numeric_keys)})")
        spectrum_id = numeric_keys[index]
        return self.get_spectrum_by_id(spectrum_id)

    def get_chromatogram_by_id(self, chromatogram_id: str) -> chromatogram.Chromatogram:
        """Retrieve chromatogram by its native ID."""
        # IndexedGzip generally indexes things by ID.
        # However, the GzipReader index seems to assume integer IDs for spectra.
        # String IDs (chromatograms) handling depends on GzipReader implementation.
        # Assuming GzipReader can handle string keys if they were indexed.
        
        # NOTE: GzipReader in pymzml usually handles numeric spectrum IDs.
        # Checking if it supports arbitrary string lookups for chromatograms.
        if chromatogram_id not in self.offset_dict:
             # Fallback: We might not have indexed chromatograms by string ID
             raise KeyError(f"Chromatogram ID {chromatogram_id} not found in index")

        ns_prefix = (
            '<mzML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation='
            '"http://psi.hupo.org/ms/mzml http://psidev.info/files/ms/mzML/xsd/mzML1.1.0.xsd" id="test_Creinhardtii_QE_pH8" '
            'version="1.1.0" xmlns="http://psi.hupo.org/ms/mzml">'
        )
        ns_suffix = "</mzML>"
        data = self.Reader.read_block(chromatogram_id)
        element = XML(ns_prefix + data.decode("utf-8") + ns_suffix)
        if "chromatogram" not in element[0].tag:
             raise ValueError(f"ID {chromatogram_id} refers to a spectrum, not a chromatogram")
        return chromatogram.Chromatogram(list(element)[0], measured_precision=5e-6)

    def get_chromatogram_by_index(self, index: int) -> chromatogram.Chromatogram:
        """Retrieve chromatogram by 0-based index."""
        chrom_keys = [k for k in self.offset_dict if isinstance(k, str) and k != "TIC"]
        if not (0 <= index < len(chrom_keys)):
            raise IndexError(f"Index {index} out of range [0, {len(chrom_keys)})")
        chrom_id = chrom_keys[index]
        return self.get_chromatogram_by_id(chrom_id)

    def __getitem__(self, identifier: int | str) -> spec.Spectrum | chromatogram.Chromatogram:
        """Retrieve spectrum or chromatogram by ID or index.

        For integers: tries spectrum ID first, then falls back to 0-based index.
        """
        if isinstance(identifier, int):
            try:
                return self.get_spectrum_by_id(identifier)
            except KeyError:
                # Not a valid spectrum ID - try 0-based index
                try:
                    return self.get_spectrum_by_index(identifier)
                except IndexError:
                    raise KeyError(f"Identifier {identifier} not found in file") from None

        # String identifiers (chromatogram IDs)
        # TODO: Use .register_namespace for more elegant XML namespace handling
        ns_prefix = (
            '<mzML xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation='
            '"http://psi.hupo.org/ms/mzml http://psidev.info/files/ms/mzML/xsd/mzML1.1.0.xsd" id="test_Creinhardtii_QE_pH8" '
            'version="1.1.0" xmlns="http://psi.hupo.org/ms/mzml">'
        )
        ns_suffix = "</mzML>"
        data = self.Reader.read_block(identifier)
        element = XML(ns_prefix + data.decode("utf-8") + ns_suffix)
        if "chromatogram" in element[0].tag:
            return chromatogram.Chromatogram(list(element)[0], measured_precision=5e-6)
        else:
            return spec.Spectrum(list(element)[0], measured_precision=5e-6)

    def close(self) -> None:
        """Close the handlers."""
        self.Reader.close()
        self.file_handler.close()
