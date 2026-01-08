import codecs
import gzip
from xml.etree.ElementTree import iterparse

from .. import chromatogram, regex_patterns, spec


class StandardGzip:
    def __init__(self, path: str, encoding: str) -> None:
        self.path: str = path
        self.file_handler = codecs.getreader(encoding)(gzip.open(path))  # noqa: SIM115
        self.offset_dict: None = self._build_index()

    def close(self) -> None:
        self.file_handler.close()

    def _build_index(self) -> None:
        """No index available for standard gzip files (random access not supported)."""
        pass

    def read(self, size: int = -1) -> str:
        """Read data from file. Default (-1) reads entire file."""
        return self.file_handler.read(size)

    def get_spectrum_by_id(self, spectrum_id: int | str) -> spec.Spectrum:
        """Retrieve spectrum by native ID.

        Raises:
            KeyError: If spectrum ID is not found.
        """
        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])

        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}spectrum"):
                spec_id = element.get("id")
                if spec_id:
                    if spec_id == str(spectrum_id):
                         self.file_handler.seek(old_pos, 0)
                         return spec.Spectrum(element)
                    
                    match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_id)
                    if match:
                        spec_id_num = int(match.group(1))
                        if spec_id_num == spectrum_id:
                            self.file_handler.seek(old_pos, 0)
                            return spec.Spectrum(element)

        self.file_handler.seek(old_pos, 0)
        raise KeyError(f"Spectrum ID {spectrum_id} not found in file")

    def get_spectrum_by_index(self, index: int) -> spec.Spectrum:
        """Retrieve spectrum by 0-based index.

        Raises:
            IndexError: If index is out of range.
        """
        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])

        current_index = 0
        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}spectrum"):
                if current_index == index:
                    self.file_handler.seek(old_pos, 0)
                    return spec.Spectrum(element)
                current_index += 1

        self.file_handler.seek(old_pos, 0)
        raise IndexError(f"Index {index} out of range [0, {current_index})")

    def get_chromatogram_by_id(self, chromatogram_id: str) -> chromatogram.Chromatogram:
        """Retrieve chromatogram by native ID."""
        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])

        for event, element in mzml_iter:
            if (
                event == "end"
                and element.tag.endswith("}chromatogram")
                and element.get("id") == chromatogram_id
            ):
                self.file_handler.seek(old_pos, 0)
                return chromatogram.Chromatogram(element, measured_precision=5e-6)
        
        self.file_handler.seek(old_pos, 0)
        raise KeyError(f"Chromatogram ID {chromatogram_id} not found")

    def get_chromatogram_by_index(self, index: int) -> chromatogram.Chromatogram:
        """Retrieve chromatogram by 0-based index."""
        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])
        
        current_index = 0
        for event, element in mzml_iter:
            if event == "end" and element.tag.endswith("}chromatogram"):
                if current_index == index:
                    self.file_handler.seek(old_pos, 0)
                    return chromatogram.Chromatogram(element, measured_precision=5e-6)
                current_index += 1

        self.file_handler.seek(old_pos, 0)
        raise IndexError(f"Chromatogram Index {index} out of range")

    def __getitem__(self, identifier: int | str) -> spec.Spectrum | chromatogram.Chromatogram:
        """Retrieve spectrum or chromatogram by ID or index.

        For integers: tries spectrum ID first, then falls back to 0-based index.
        """
        if isinstance(identifier, int):
            try:
                return self.get_spectrum_by_id(identifier)
            except KeyError:
                try:
                    return self.get_spectrum_by_index(identifier)
                except IndexError:
                    raise KeyError(f"Identifier {identifier} not found in file") from None

        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])

        for event, element in mzml_iter:
            if (
                event == "end"
                and element.tag.endswith("}chromatogram")
                and element.get("id") == identifier
            ):
                self.file_handler.seek(old_pos, 0)
                return chromatogram.Chromatogram(element, measured_precision=5e-6)

        self.file_handler.seek(old_pos, 0)
        raise KeyError(f"Identifier '{identifier}' not found in file")
