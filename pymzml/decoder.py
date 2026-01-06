#!/usr/bin/env python3
"""
MS-Numpress decoder for :py:attr:`~pymzml.spec.Spectrum.mz` and
:py:attr:`~pymzml.spec.Spectrum.i` values.

@author M. Kösters, C. Fufezan
"""

import numpy as np
from numpy.typing import NDArray


class MSDecoder:
    """
    Lazy-loading decoder for MS-Numpress compressed data.

    Attempts to use the compiled pynumpress library. Import happens on first use
    to avoid import errors during module initialization.
    """

    _pynumpress = None
    _import_attempted = False

    @classmethod
    def _get_decoder(cls):
        """Get the pynumpress decoder, importing it if necessary."""
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
        """
        Decode MS-Numpress linear prediction compressed data.

        Args:
            data: Compressed data as bytes or numpy array

        Returns:
            Decoded data as numpy array
        """
        decoder = cls._get_decoder()
        result = decoder.decodeLinear(data)  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def decode_pic(cls, data: NDArray[np.uint8] | bytes) -> NDArray[np.float64]:
        """
        Decode MS-Numpress positive integer compressed data.

        Args:
            data: Compressed data as bytes or numpy array

        Returns:
            Decoded data as numpy array
        """
        decoder = cls._get_decoder()
        result = decoder.decodePic(data)  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def decode_slof(cls, data: NDArray[np.uint8] | bytes) -> NDArray[np.float64]:
        """
        Decode MS-Numpress short logged float compressed data.

        Args:
            data: Compressed data as bytes or numpy array

        Returns:
            Decoded data as numpy array
        """
        decoder = cls._get_decoder()
        result = decoder.decodeSlof(data)  # type: ignore
        return np.asarray(result, dtype=np.float64)

    @classmethod
    def encode_linear(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """
        Encode data using MS-Numpress linear prediction compression.

        Args:
            data: Data to compress as numpy array or list

        Returns:
            Compressed data as bytearray
        """
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodeLinear(data)  # type: ignore

    @classmethod
    def encode_pic(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """
        Encode data using MS-Numpress positive integer compression.

        Args:
            data: Data to compress as numpy array or list

        Returns:
            Compressed data as bytearray
        """
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodePic(data)  # type: ignore

    @classmethod
    def encode_slof(cls, data: NDArray[np.float64] | list[float]) -> bytearray:
        """
        Encode data using MS-Numpress short logged float compression.

        Args:
            data: Data to compress as numpy array or list

        Returns:
            Compressed data as bytearray
        """
        decoder = cls._get_decoder()
        if isinstance(data, list):
            data = np.array(data, dtype=np.float64)
        return decoder.encodeSlof(data)  # type: ignore
