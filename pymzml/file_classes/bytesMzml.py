"""
Interface for binary streams of uncompressed mzML.

@author: Sylvain Le Bon
"""

from collections import OrderedDict
from io import TextIOWrapper, BytesIO
from typing import TextIO, Pattern

from .. import regex_patterns
from .standardMzml import StandardMzml


class BytesMzml(StandardMzml):
    def __init__(
        self, binary: BytesIO, encoding: str, build_index_from_scratch: bool = False
    ) -> None:
        """
        Initalize Wrapper object for standard mzML files.

        Arguments:
            path (str)     : path to the file
            encoding (str) : encoding of the file
        """
        self.binary: BytesIO = binary
        self.file_handler: TextIO = self.get_file_handler(encoding)
        self.offset_dict: OrderedDict[int | str, int | tuple[int, ...] | None] = OrderedDict()
        self.spec_open: Pattern[bytes] = regex_patterns.SPECTRUM_OPEN_PATTERN
        self.spec_close: Pattern[bytes] = regex_patterns.SPECTRUM_CLOSE_PATTERN
        if build_index_from_scratch is True:
            seeker = self.get_binary_file_handler()
            self._build_index_from_scratch(seeker)
            seeker.close()

    def get_binary_file_handler(self) -> BytesIO:
        self.binary.seek(0)
        return self.binary

    def get_file_handler(self, encoding: str) -> TextIO:
        return TextIOWrapper(self.binary, encoding=encoding)
