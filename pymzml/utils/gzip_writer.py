"""
Writer class for indexed gzipped files
"""

import struct
import time
import zlib
from collections import OrderedDict
from typing import BinaryIO
from types import TracebackType


class GzipWriter:
    """

    Generalized Gzip writer class with random access to indexed offsets.

    Keyword Arguments:
        file (string)        : Filename for the resulting file
        max_idx (int)        : max number of indices which can be saved in
                                this file
        max_idx_len (int)    : maximal length of the index in bytes, must
                                be between 1 and 255
        max_offset_len (int) : maximal length of the offset in bytes
        output_path (str)    : path to the output file

    """

    def __init__(
        self,
        file: str | None = None,
        max_idx: int = 10000,
        max_idx_len: int = 8,
        max_offset_len: int = 8,
        output_path: str = "./test.dat.igzip",
        comp_str: int = -1,
    ) -> None:
        self.file: str | None = file
        self.Lock: bool = False
        self._format_version: int = 1  # max 255!!!
        self.file_name: str = output_path
        self.max_idx_num: int = max_idx
        self.max_idx_len: int = max_idx_len
        self.max_offset_len: int = max_offset_len
        self.generic_header: OrderedDict[str, bytes] = OrderedDict(
            [
                ("MAGIC_BYTE_1", b"\x1f"),
                ("MAGIC_BYTE_2", b"\x8b"),
                ("COMPRESSION", b"\x08"),
                ("FLAGS", b"\x00"),
                ("DATE", b"\x00\x00\x00\x00"),
                ("XFL", b"\x02"),
                ("OS", b"\x03"),
            ]
        )
        self.index: OrderedDict[int | str, int] = OrderedDict()
        self.first_header_set: bool = False
        self._file_out: BinaryIO | None = None
        self._encoding: str = "latin-1"
        # magic bytes. FU+version
        self.index_magic_bytes: bytes = b"FU" + struct.pack("<B", self._format_version)
        self.crc32: int = 0
        self.isize: int = 0
        self.comp_str: int = comp_str
        self.index_offset: int = 0

    def __del__(self) -> None:
        """
        Close the file object properly after this object is deleted
        """
        try:
            if self._file_out is not None:
                self._file_out.close()
        except Exception:
            pass

    def close(self) -> None:
        """
        Close the internal file object.
        """
        if self._file_out is not None:
            self._file_out.close()

    @property
    def file_out(self) -> BinaryIO:
        """
        Output filehandler
        """
        if self._file_out is None:
            self._file_out = open(self.file_name, "wb")
        return self._file_out

    @property
    def encoding(self) -> str:
        """
        Returns the encoding used for this file
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding: str) -> None:
        """
        Set the file encoding for the output file.
        """
        assert isinstance(encoding, str), "encoding must be a string"
        self._encoding = encoding

    def _write_gen_header(self, index: bool = False, flags: list[str] | None = None) -> int:
        """
        Write a valid gzip header with creation time, user defined flag fields
        and allocated index.

        Keyword Arguments:
            Index (bool)           : whether to or not to write an
                                        index into this header.
            FLAGS (list, optional) : list of flags (FTEXT, FHCRC, FEXTRA,
                                        FNAME) to set for this header.

        Returns:
            offset (int): byte offset of the file pointer
        """
        _flags: list[str] = []
        if flags is None:
            _flags = []
        else:
            _flags = flags
        FTEXT, FHCRC, FEXTRA, FNAME = 1, 2, 4, 8  # extra field bit flags
        current_time = int(time.time())
        time_byte = struct.pack("<L", current_time)
        self.generic_header["DATE"] = time_byte
        if index:
            self.generic_header["FLAGS"] = b"\x10"
        if _flags:
            if "FTEXT" in _flags:
                self.generic_header["FLAGS"] = bytes([self.generic_header["FLAGS"][0] | FTEXT])

            if "FHCRC" in _flags:
                header_crc32 = 0
                self.generic_header["FLAGS"] = bytes([self.generic_header["FLAGS"][0] | FHCRC])
                for byte in self.generic_header.values():
                    header_crc32 = zlib.crc32(byte, header_crc32)

            if "FEXTRA" in _flags:
                self.generic_header["FLAGS"] = bytes([self.generic_header["FLAGS"][0] | FEXTRA])

            if "FNAME" in _flags:
                self.generic_header["FLAGS"] = bytes([self.generic_header["FLAGS"][0] | FNAME])

        for value in self.generic_header.values():
            self.file_out.write(value)
        if "FEXTRA" in _flags:
            # WRITE EXTRA FIELD
            pass

        if "FNAME" in _flags:
            # WRITE FNAME FIELD
            _ = self.file_name.split("/")[-1]

        if index:
            self.generic_header["FLAGS"] = b"\x00"
            self.file_out.write(self.index_magic_bytes)
            self.file_out.write(struct.pack("<B", self.max_idx_len))
            self.file_out.write(struct.pack("<B", self.max_offset_len))
            self.index_offset = self.file_out.tell()
            self._allocate_index_bytes()

        if "FHCRC" in _flags:
            # WRITE checksum for header
            pass

        return self.file_out.tell()

    def _allocate_index_bytes(self) -> None:
        """
        Allocate 'self.max_index_num' bytes of length 'self.max_idx_len'
        in the header for inserting the index later on.
        """
        id_placeholder = self.max_idx_len * b"\x01"
        offset_placeholder = self.max_offset_len * b"\x01"
        for _ in range(self.max_idx_num):
            self.file_out.write(id_placeholder)
            self.file_out.write(offset_placeholder)
        self.file_out.write(b"\x00")

    def _write_data(self, data: str | bytes | bytearray | memoryview) -> None:
        """
        Write data into file-stream.

        Arguments:
            data (str): uncompressed data
        """
        Compressor = zlib.compressobj(
            self.comp_str, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0
        )
        # compress data and flush (includes writing crc32 and isize)
        if isinstance(data, str):
            data = data.encode(self._encoding)
        elif isinstance(data, memoryview):
            data = data.tobytes()
        elif isinstance(data, bytearray):
            data = bytes(data)
        elif not isinstance(data, bytes):  # type: ignore
            # fallback: convert to str then encode with configured encoding
            data = str(data).encode(self._encoding)
        self.crc32 = zlib.crc32(data)
        self.isize = len(data) % 2**32
        comp_data = Compressor.compress(data) + Compressor.flush()
        self.file_out.write(comp_data)
        self.file_out.write(struct.pack("<L", self.crc32))
        self.file_out.write(struct.pack("<L", self.isize))

    def add_data(self, data: str | bytes, identifier: int | str) -> bool | None:
        """
        Create a new gzip member with compressed 'data' indexed with 'index'.

        Arguments:
            data (str)         : uncompressed data to write to file
            index (str or int) : unique index for the data
        """
        if self.Lock:
            raise Exception("Cant add any more data if index is already written")

        if len(self.index) + 1 > self.max_idx_num:
            print(
                """
                WARNING: Reached maximum number of indexed data blocks
                '({0}), cannot add any more data!
                """.format(self.max_idx_num)
            )
            return False

        if not self.first_header_set:
            self._write_gen_header(index=True)
            self.first_header_set = True
        else:
            # do we need this?
            self._write_gen_header(index=False)

        self.index[identifier] = self.file_out.tell()
        self._write_data(data)
        return None

    def _write_identifier(self, identifier: int | str) -> None:
        """
        Convert and write the identifier into output file.

        Arguments:
            identifier (str or int): identifier to write into index
        """
        id_format = "{0:\xac>" + str(self.max_idx_len) + "}"
        identifier_str = str(identifier)
        identifier_bytes = id_format.format(identifier_str).encode("latin-1")
        self.file_out.write(identifier_bytes)

    def _write_offset(self, offset: int) -> None:
        """
        Convert and write offset to output file.

        Arguments:
            offset (int): offset which will be formatted and written
                into file index
        """
        offset_format = "{0:\xac>" + str(self.max_offset_len) + "}"
        offset_str = str(offset)
        offset_bytes = offset_format.format(offset_str).encode("latin-1")
        self.file_out.write(offset_bytes)

    def write_index(self) -> None:
        """
        Only called after all the data is written, i.e. all calls to
        :func:`~GSGW.add_data` have been done.

        Seek back to the beginning of the file and write the index into the
        allocated comment bytes (see _write_gen_header(Index=True)).
        """
        self.Lock = True
        self.file_out.seek(self.index_offset)
        for identifier, offset in self.index.items():
            self._write_identifier(identifier)
            self._write_offset(offset)

    def __enter__(self) -> "GzipWriter":
        """
        Enable the with syntax for this class (entry point).
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Destructor when using this class with 'with .. as'."""
        if self._file_out is not None:
            self._file_out.close()


if __name__ == "__main__":
    print(__doc__)
