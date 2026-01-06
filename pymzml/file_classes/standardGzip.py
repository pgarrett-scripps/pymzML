"""
Interface for gzipped mzML files.
"""

import codecs
import gzip
from xml.etree.ElementTree import iterparse

from .. import regex_patterns
from .. import spec
from .. import chromatogram


class StandardGzip(object):
    def __init__(self, path: str, encoding: str) -> None:
        """
        Initalize Wrapper object for gzipped mzML files.

        Arguments:
            path (str)     : path to the file
            encoding (str) : encoding of the file
        """
        self.path: str = path
        self.file_handler = codecs.getreader(encoding)(gzip.open(path))
        self.offset_dict: None = self._build_index()
        return

    def close(self) -> None:
        self.file_handler.close()

    def _build_index(self) -> None:
        """
        Cant build index for standard gzip files
        """
        # raise Exception('Cant build index for gzip files')
        pass

    def read(self, size: int = -1) -> str:
        """
        Read binary data from file handler.

        Keyword Arguments:
            size (int): Number of bytes to read from file, -1 to read to end of file

        Returns:
            data (str): byte string of len size of input data
        """
        return self.file_handler.read(size)

    def __getitem__(self, identifier: int | str) -> spec.Spectrum | chromatogram.Chromatogram:
        """
        Access the item with id 'identifier' in the file by iterating the xml-tree.

        Arguments:
            identifier (str): native id of the item to access

        Returns:
            data (str): text associated with the given identifier
        """
        old_pos = self.file_handler.tell()
        self.file_handler.seek(0, 0)
        mzml_iter = iterparse(self.file_handler, events=["end"])

        for event, element in mzml_iter:
            if event == "end":
                if element.tag.endswith("}spectrum"):
                    spec_id = element.get("id")
                    if spec_id:
                        match = regex_patterns.SPECTRUM_ID_PATTERN.search(spec_id)
                        if match:
                            spec_id_num = int(match.group(1))
                            if spec_id_num == identifier:
                                self.file_handler.seek(old_pos, 0)
                                return spec.Spectrum(element, measured_precision=5e-6)
                elif element.tag.endswith("}chromatogram"):
                    if element.get("id") == identifier:
                        self.file_handler.seek(old_pos, 0)
                        return chromatogram.Chromatogram(element, measured_precision=5e-6)

        # If we get here, identifier was not found
        raise KeyError(f"Identifier '{identifier}' not found in file")


if __name__ == "__main__":
    print(__doc__)
