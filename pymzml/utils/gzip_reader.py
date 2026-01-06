"""
Reader class for indexed gzipped files
"""

import struct
import zlib
from collections import OrderedDict
from typing import BinaryIO
from types import TracebackType


class GzipReader:
    """
    Generalized Gzip reader class which enables random access in files
    written with the :class:`~pymzml.utils.GSGW.GSGW` class.

    Keyword Arguments:
        file (str): path to file to read
    """

    def __init__(self, file: str) -> None:
        self.file_in: BinaryIO = open(file, "rb")
        self.filename: str = file
        self.magic_bytes: bytes = b"\x1f\x8b"
        self.indexed: bool = True
        self.random_access: bool = False
        self.ascii_file: bool = False
        self.fname: bytes | None = None
        self.index: OrderedDict[int | str, int] = OrderedDict()
        self.cm: int = 0
        self.flg: int = 0
        self.mtime: int = 0
        self.xfl: int = 0
        self.os: int = 0
        self.idx_len: int = 0
        self.offset_len: int = 0

        if not self._check_magic_bytes():
            raise Exception("not a gzip file (wrong magic bytes)")

        self._read_basic_header()
        if self.flg & 1 != 0:  # FTEXT flag
            self.ascii_file = True
        if self.flg & 2 != 0:  # FHCRC flag
            _ = self.file_in.read(2)
        if self.flg & 4 != 0:  # FEXTRA flag
            xlen = struct.unpack("<H", self.file_in.read(2))[0]
            self.file_in.seek(xlen, 1)
        if self.flg & 8 != 0:  # FNAME flag
            self.fname = self._read_until_zero()
        if self.flg & 16 == 0:  # FCOMMENT flag NOT SET
            self.indexed = False
        else:
            self._read_index()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def seek(self, offset: int) -> None:
        """
        Seek to byte offset in input file.

        Arguments:
            offset (int): byte offset to seek to in FileIn

        Returns:
            None
        """
        self.file_in.seek(offset)

    def read_block(self, index: int | str) -> bytes:
        """
        Read and return the data block with the unique index `index`

        Arguments:
            index(int or str): identifier associated with a specific block

        Returns:
            data (str): indexed text block as string
        """
        start: int = self.index[index]
        try:
            end = self.index[int(index) + 1]
        except (KeyError, ValueError, TypeError):
            end = self.file_in.seek(0, 2)
        self.file_in.seek(start)
        readSize = end - start
        comp_data = self.file_in.read(readSize)
        data = zlib.decompress(comp_data, -zlib.MAX_WBITS)
        return data

    def _check_magic_bytes(self) -> bool:
        """
        Check if file is a gzip file.
        """
        mb = self.file_in.read(2)
        return mb == self.magic_bytes

    def _read_basic_header(self) -> None:
        """
        Read and save compression method, bitflags, changetime,
        compression speed and os.
        """
        self.file_in.seek(2)
        vals = struct.unpack("<BBLBB", self.file_in.read(8))
        self.cm = vals[0]
        self.flg = vals[1]
        self.mtime = vals[2]
        self.xfl = vals[3]
        self.os = vals[4]

    def _read_until_zero(self) -> bytes:
        """
        Read input until \x00 is reached
        """
        buf = b""
        c = self.file_in.read(1)
        while c != b"\x00":
            buf += c
            c = self.file_in.read(1)
        return buf

    def _read_index(self) -> None:
        """
        Read and save offset dict from indexed gzip file
        """
        self.file_in.seek(10)
        mb = self.file_in.read(3)
        if mb != b"FU\x01":  # All hail MK!
            print("No index in comment field found. No random access possible")
            self.indexed = False
            return

        lengths = struct.unpack("<BB", self.file_in.read(2))
        self.idx_len = lengths[0]
        self.offset_len = lengths[1]
        ID_block = b""
        while b"\x00" not in ID_block:
            ID_block = self.file_in.read(self.idx_len)
            OffsetBlock = self.file_in.read(self.offset_len)
            try:
                try:
                    Identifier: int | str = int(ID_block.decode("latin-1").strip("¬"))
                except (ValueError, UnicodeDecodeError):
                    Identifier = ID_block.decode("latin-1").strip("¬")
                Offset = int(OffsetBlock.decode("latin-1").strip("¬"))
                self.index[Identifier] = Offset
            except (ValueError, UnicodeDecodeError):
                break
        self.file_in.seek(0)

    def read(self, size: int = -1) -> bytes:
        """
        Read the content of the in File in binary mode

        Keyword Arguments:
            size (int, optional): number of bytes to read, -1 for everything

        Returns:
            data (bytes): parsed bytes from input file
        """
        return self.file_in.read(size)

    def __enter__(self) -> "GzipReader":
        """
        Enable the with syntax for this class (entry point)
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        destructor when using this class with 'with .. as '
        """
        self.file_in.close()

    def close(self) -> None:
        """
        Close the internal Filehandler
        """
        self.file_in.close()


if __name__ == "__main__":
    print(__doc__)
