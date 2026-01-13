#!/usr/bin/env python3
"""MS-Numpress decoder for compressed m/z and intensity values."""

import zlib

import numpy as np
from numpy.typing import NDArray

from pymzml.constants import MSAccession


def fix_input(data: NDArray[np.uint8] | bytes) -> NDArray[np.uint8]:
    if isinstance(data, bytes):
        return np.frombuffer(data, dtype=np.uint8)
    return data  # type: ignore


class MSDecoder:
    """Lazy-loading decoder for MS-Numpress compressed data via pynumpress."""

    _pynumpress = None
    _import_attempted = False

    @classmethod
    def _get_decoder(cls):
        """Get or import pynumpress decoder on first use."""
        if not cls._import_attempted:
            cls._import_attempted = True
            try:
                import pynumpress  # type: ignore

                cls._pynumpress = pynumpress
            except ImportError as e:
                raise ImportError(
                    "pynumpress is required for numpress-compressed mzML files.\n"
                    "Install it with: pip install pynumpress\n"
                    f"Original error: {e}"
                ) from e

        if cls._pynumpress is None:
            raise ImportError(
                "pynumpress is required for numpress-compressed mzML files.\n"
                "Install it with: pip install pynumpress"
            )

        return cls._pynumpress

    @classmethod
    def decode_linear(cls, data: NDArray[np.uint8] | bytes) -> NDArray[np.float64]:
        """Decode MS-Numpress linear prediction compressed data."""
        decoder = cls._get_decoder()
        result = decoder.decodeLinear(fix_input(data))  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def decode_pic(cls, data: NDArray[np.uint8] | bytes) -> NDArray[np.float64]:
        """Decode MS-Numpress positive integer compressed data."""
        decoder = cls._get_decoder()
        result = decoder.decodePic(fix_input(data))  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def decode_slof(cls, data: NDArray[np.uint8] | bytes) -> NDArray[np.float64]:
        """Decode MS-Numpress short logged float compressed data."""
        decoder = cls._get_decoder()
        result = decoder.decodeSlof(fix_input(data))  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def encode_linear(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """Encode data using MS-Numpress linear prediction compression."""
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodeLinear(data)  # type: ignore

    @classmethod
    def encode_pic(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """Encode data using MS-Numpress positive integer compression."""
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodePic(data)  # type: ignore

    @classmethod
    def encode_slof(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """Encode data using MS-Numpress short logged float compression."""
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodeSlof(data)  # type: ignore

    @classmethod
    def decode_zlib(cls, data: bytes) -> bytes:
        """Decompress zlib-compressed data."""
        return zlib.decompress(data)

    @classmethod
    def encode_zlib(cls, data: bytes) -> bytes:
        """Compress data using zlib."""
        return zlib.compress(data)

    @classmethod
    def decode_numpress(
        cls, data: NDArray[np.uint8] | bytes, compression: MSAccession
    ) -> NDArray[np.float64]:
        """Decode numpress compressed data using golomb-rice encoding."""
        if compression == MSAccession.NUMPRESS_LINEAR:
            return cls.decode_linear(data)
        elif compression == MSAccession.NUMPRESS_PIC:
            return cls.decode_pic(data)
        elif compression == MSAccession.NUMPRESS_SLOF:
            return cls.decode_slof(data)
        raise ValueError(f"Unsupported numpress compression type: {compression}")

    @classmethod
    def encode_numpress(
        cls, data: NDArray[np.float64] | list[float], compression: MSAccession
    ) -> bytearray:
        """Encode data using numpress compression."""
        if compression == MSAccession.NUMPRESS_LINEAR:
            return cls.encode_linear(data)
        elif compression == MSAccession.NUMPRESS_PIC:
            return cls.encode_pic(data)
        elif compression == MSAccession.NUMPRESS_SLOF:
            return cls.encode_slof(data)
        raise ValueError(f"Unsupported numpress compression type: {compression}")

    @classmethod
    def decode_ztsd(cls, data: bytes) -> bytes:
        """Decompress ztsd-compressed data."""
        import zstd

        return zstd.decompress(data)

    @classmethod
    def encode_ztsd(cls, data: bytes) -> bytes:
        """Compress data using ztsd."""
        import zstd

        return zstd.compress(data)
