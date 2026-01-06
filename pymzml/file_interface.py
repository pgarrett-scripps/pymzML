#!/usr/bin/env python3
"""
Interface for mzML files

@author: Manuel Koesters
"""
from pathlib import Path

from io import BytesIO
from typing import Any
from re import Pattern
from pymzml.file_classes import indexedGzip, standardGzip, standardMzml, bytesMzml
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
        """
        Initialize a object interface to mzML files.

        Arguments:
            path (Union[str, BytesIO]): path to the mzML file or BytesIO object
            encoding (str)             : encoding of the file
            build_index_from_scratch (bool): whether to build the index from scratch or use existing one
            index_regex (Pattern[bytes] | None): regex pattern to find index entries

        """
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
        """
        Open a file like object resp. a wrapper for a file like object.

        Arguments:
            path_or_file (str | BytesIO): path to the mzml file or file object

        Returns:
            file_handler: instance of
            :py:class:`~pymzml.file_classes.standardGzip.StandardGzip`,
            :py:class:`~pymzml.file_classes.indexedGzip.IndexedGzip` or
            :py:class:`~pymzml.file_classes.standardMzml.StandardMzml`,
            based on the file ending of 'path'
        """
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
        """
        Check if the given file is an indexed gzip file or not.

        Arguments:
            path (str): path to the file

        Returns:
            bool : `True` if path is a gzip file with index, else `False`
        """
        indexed = False
        indexed = gzip_reader.GzipReader(path).indexed
        return indexed

    def read(self, size: int = -1) -> bytes | str:
        """
        Read binary data from file handler.

        Keyword Arguments:
            size (int): Number of bytes to read from file, -1 to
            read to end of file

        Returns:
            data (Union[bytes, str]): byte string with defined size of the input data
        """
        return self.file_handler.read(size)

    def __getitem__(self, identifier: str | int) -> Any:
        """
        Access the item with id 'identifier' in the file.

        Arguments:
            identifier (str): native id of the item to access

        Returns:
            data (str): text associated with the given identifier
        """
        return self.file_handler[identifier]
