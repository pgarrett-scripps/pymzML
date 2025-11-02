#!/usr/bin/env python3
"""
Classes to encode and decode :py:attr:`~pymzml.spec.Spectrum.mz` and
:py:attr:`~pymzml.spec.Spectrum.i` values.

@author M. Kösters, C. Fufezan
"""
import warnings
import zlib
from base64 import b64decode as b64dec
from multiprocessing import Pool
from typing import Tuple, List, Union, Any, Callable

import numpy as np
from numpy.typing import NDArray

# Global PyNump decoder
try:
    # try to import c-accelerated Numpress decoding
    import pynumpress

    MSDecoder = pynumpress
except ImportError:
    # fall back to python-only implementation of numpress decoding
    import pymzml.ms_numpress

    warnings.warn(
        "Cython PyNumpress is not installed; falling back to slower, python-only version",
        ImportWarning,
    )
    MSDecoder = pymzml.ms_numpress.MSNumpress()


def _decode(
    data: bytes,
    comp: List[str],
    d_array_length: Union[str, int],
    f_type: str,
    d_type: str
) -> Tuple[str, Union[NDArray[np.float32], NDArray[np.float64], List[float]]]:
    """
    Decode ms-numpress, b64 and/or zlib compressed data.

    Args:
        data (bytes): compressed data
        comp (List[str]): compression method
        d_array_length (Union[str, int]): length of the uncompressed data array
        f_type (str): float type (32 or 64 bit)
        d_type (str): type of data (mz, i, or time)

    Returns:
        result (Tuple[str, Union[NDArray, List]]): tuple containing the datatype and the
        decompressed data array.
    """
    np_dtype: Union[type[np.float32], type[np.float64], None]
    if f_type == "32-bit float":
        np_dtype = np.float32
    elif f_type == "64-bit float":
        np_dtype = np.float64
    else:
        np_dtype = None

    decoded_data = b64dec(data)
    if "zlib" in comp or "zlib compression" in comp:
        decoded_data = zlib.decompress(decoded_data)

    if (
        "ms-np-linear" in comp
        or "ms-np-pic" in comp
        or "ms-np-slof" in comp
        or "MS-Numpress linear prediction compression" in comp
        or "MS-Numpress short logged float compression" in comp
    ):
        result = []
        # start ms numpress decoder globally?
        if (
            "ms-np-linear" in comp
            or "MS-Numpress linear prediction compression" in comp
        ):
            result = MSDecoder.decodeLinear(decoded_data)
        elif "ms-np-pic" in comp:
            result = MSDecoder.decode_pic(decoded_data)
        elif (
            "ms-np-slof" in comp or "MS-Numpress short logged float compression" in comp
        ):
            result = MSDecoder.decode_slof(decoded_data)
        return (d_type, result)

    array = np.fromstring(decoded_data, np_dtype)  # type: ignore[arg-type]
    return (d_type, array)


class Decoder:
    """
    Decoder class to enable parallel decoding of peaks.

    Keyword Args:
        nb_worker(int): number of pool workers to use. Defaults to 2.
    """

    def __init__(self, nb_workers: int = 2) -> None:
        """ """
        self._mz: Union[None, NDArray[Any], List[float]] = None
        self._i: Union[None, NDArray[Any], List[float]] = None

    # @profile
    def pool_decode(self, data: Any, callback: Callable[..., Any]) -> None:
        """
        Decode mz and i values in parallel.

        Args:
            data: ...

        Keyword Args:
            callback (Callable): Callback function to call if decoding is
                finished. Should be :py:meth:`~pymzml.spec.Spectrum._register`.
        """
        ZE_POOL = Pool(processes=2)

        ZE_POOL.starmap(_decode, data)

    def _error_callback(self, result: Any) -> None:
        """ """
        raise Exception("Failed with error:\n{0}".format(result))


if __name__ == "__main__":
    print(__doc__)
