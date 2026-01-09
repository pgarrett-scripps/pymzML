from io import BytesIO, TextIOWrapper
from typing import TextIO
from collections import OrderedDict

from .standardMzml import StandardMzml


class BytesMzml(StandardMzml):
    """mzML file wrapper for in-memory BytesIO objects."""

    def __init__(
        self, binary: BytesIO, encoding: str, build_index_from_scratch: bool = False
    ) -> None:
        # Store the BytesIO object before calling parent __init__
        self.binary: BytesIO = binary
        self.path: str = "<BytesIO>"  # Override path since we don't have a file path
        self.index_regex = None
        self.file_handler: TextIO = self.get_file_handler(encoding)
        self.spectrum_offsets: OrderedDict[str, int] = OrderedDict()
        self.chromatogram_offsets: OrderedDict[str, int] = OrderedDict()
        self._spectrum_keys: list[str] = []
        self._chromatogram_keys: list[str] = []

        # Build index if requested
        if build_index_from_scratch:
            seeker = self.get_binary_file_handler()
            self._build_index_from_scratch(seeker)
            seeker.close()

    def get_binary_file_handler(self) -> BytesIO:
        """Return binary file handler for BytesIO."""
        self.binary.seek(0)
        return self.binary

    def get_file_handler(self, encoding: str) -> TextIO:
        """Return text file handler for BytesIO."""
        return TextIOWrapper(self.binary, encoding=encoding)
