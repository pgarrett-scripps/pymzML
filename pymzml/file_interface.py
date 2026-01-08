#!/usr/bin/env python3
"""Interface for different mzML file formats."""

from io import BytesIO
from pathlib import Path
from re import Pattern
from typing import Any

from pymzml.file_classes import bytesMzml, indexedGzip, standardGzip, standardMzml
from pymzml.utils import gzip_reader


class FileInterface:
    """Interface to different mzML formats."""

    def __init__(
        self,
        path: str | Path | BytesIO,
        encoding: str,
        build_index_from_scratch: bool = False,
        index_regex: Pattern[bytes] | None = None,
    ) -> None:
        """Initialize FileInterface with path and encoding options."""
        self.build_index_from_scratch: bool = build_index_from_scratch
        self.encoding: str = encoding
        self.index_regex: Pattern[bytes] | None = index_regex
        self.file_handler: (
            standardMzml.StandardMzml
            | standardGzip.StandardGzip
            | indexedGzip.IndexedGzip
            | bytesMzml.BytesMzml
        ) = self._open(path)
        self.offset_dict: dict[Any, Any] = self.file_handler.offset_dict or {}  # type: ignore

    def close(self) -> None:
        """Close the internal file handler."""
        self.file_handler.close()

    def _open(
        self, path_or_file: str | Path | BytesIO
    ) -> (
        standardMzml.StandardMzml
        | standardGzip.StandardGzip
        | indexedGzip.IndexedGzip
        | bytesMzml.BytesMzml
    ):
        """Open appropriate file handler based on file type and format."""
        if isinstance(path_or_file, BytesIO):
            return bytesMzml.BytesMzml(path_or_file, self.encoding, self.build_index_from_scratch)
        if isinstance(path_or_file, Path):
            path_or_file = str(path_or_file)
        if path_or_file.endswith(".gz"):
            if self._indexed_gzip(path_or_file):
                return indexedGzip.IndexedGzip(path_or_file, self.encoding)
            else:
                return standardGzip.StandardGzip(path_or_file, self.encoding)
        return standardMzml.StandardMzml(
            path_or_file,
            self.encoding,
            self.build_index_from_scratch,
            index_regex=self.index_regex,
        )

    def _indexed_gzip(self, path: str) -> bool:
        """Check if file is an indexed gzip file."""
        indexed = False
        indexed = gzip_reader.GzipReader(path).indexed
        return indexed

    def read(self, size: int = -1) -> bytes | str:
        """Read binary data from file handler (size=-1 reads to end)."""
        return self.file_handler.read(size)

    def get_spectrum_by_id(self, spectrum_id: int | str) -> Any:
        """Get spectrum by its native ID."""
        return self.file_handler.get_spectrum_by_id(spectrum_id)

    def get_spectrum_by_index(self, index: int) -> Any:
        """Get spectrum by 0-based index."""
        return self.file_handler.get_spectrum_by_index(index)

    def get_chromatogram_by_id(self, chromatogram_id: str) -> Any:
        """Get chromatogram by its native ID."""
        return self.file_handler.get_chromatogram_by_id(chromatogram_id)

    def get_chromatogram_by_index(self, index: int) -> Any:
        """Get chromatogram by 0-based index."""
        return self.file_handler.get_chromatogram_by_index(index)

    def __getitem__(self, identifier: str | int) -> Any:
        """Access item by native ID or index."""
        return self.file_handler[identifier]
