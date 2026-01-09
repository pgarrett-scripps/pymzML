import os
from re import Pattern
import gzip
import re
from collections.abc import Callable
from typing import IO, Match

import numpy as np
from numpy.typing import NDArray

from .. import regex_patterns
from ..constants import FileExtension, NoiseMode, SpecialID, XMLTag
from .gzip_writer import GzipWriter


def index_gzip(
    pathIn: str,
    pathOut: str,
    max_idx: int = 10000,
    idx_len: int = 8,
    verbose: bool = False,
    comp_str: int = -1,
) -> None:
    """Convert mzML file to indexed gzipped format for fast random access."""
    fileOpen: Callable[[str, str], IO[str]]
    if pathIn.endswith(FileExtension.GZ):
        fileOpen = gzip.open  # type: ignore
    elif pathIn.lower().endswith(FileExtension.MZML):
        fileOpen = open
    else:
        raise ValueError(f"Unsupported file format for {pathIn}")

    with GzipWriter(
        output_path=pathOut,
        max_idx=max_idx,
        max_idx_len=idx_len,
        max_offset_len=idx_len,
        comp_str=comp_str,
    ) as Writer:
        with fileOpen(pathIn, "rt") as Reader:  # type: ignore
            data = ""
            nativeID: int | str = SpecialID.UNKNOWN
            for line in Reader:
                line_stripped = line.strip()

                if line_stripped.startswith(XMLTag.SPECTRUM_OPEN):
                    data += line
                    match = re.search(regex_patterns.SPECTRUM_TAG_PATTERN, line)
                    if match:
                        lineID = match.group("index")
                        id_match = regex_patterns.SPECTRUM_ID_PATTERN.search(lineID)
                        if id_match:
                            nativeID = int(id_match.group(1))

                elif line_stripped.startswith(XMLTag.SPECTRUM_CLOSE):
                    data += line
                    Writer.add_data(data, nativeID)
                    if verbose:
                        print(f"NativeID : {nativeID}", end="\r")
                    data = ""
                    nativeID = SpecialID.UNKNOWN

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_OPEN):
                    data += line
                    match = re.search(regex_patterns.CHROMATOGRAM_ID_PATTERN, line)
                    if match:
                        nativeID = match.group(1)
                        if verbose:
                            print("found chromatogram")

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_CLOSE):
                    data += line
                    Writer.add_data(data, nativeID)
                    if verbose:
                        print("found chromatogram")
                        print(f"NativeID: {nativeID}")
                    data = ""
                    nativeID = SpecialID.UNKNOWN

                elif line_stripped.startswith(XMLTag.SPECTRUM_LIST):
                    data += line
                    Writer.add_data(data, SpecialID.HEAD)
                    if verbose:
                        print("NativeID :", SpecialID.HEAD)
                    data = ""

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_LIST):
                    data += line
                    Writer.add_data(data, SpecialID.JUNK)
                    if verbose:
                        print("NativeID :", SpecialID.JUNK)
                    data = ""

                else:
                    data += line

            if data:
                Writer.add_data(data, SpecialID.TAIL)
                if verbose:
                    print("NativeID :", SpecialID.TAIL)
        Writer.write_index()


def index(
    pathIn: str,
    pathOut: str,
    max_idx: int = 10000,
    idx_len: int = 8,
    verbose: bool = False,
    comp_str: int = -1,
) -> None:
    """Convert gzipped mzML file to indexed format for fast random access."""
    with GzipWriter(
        output_path=pathOut,
        max_idx=max_idx,
        max_idx_len=idx_len,
        max_offset_len=idx_len,
        comp_str=comp_str,
    ) as Writer:
        with gzip.open(pathIn, "rt") as Reader:  # type: ignore
            data = ""
            nativeID: int | str = SpecialID.UNKNOWN
            for line in Reader:
                line_stripped = line.strip()

                if line_stripped.startswith(XMLTag.SPECTRUM_OPEN):
                    data += line
                    match = re.search(regex_patterns.SPECTRUM_TAG_PATTERN, line)
                    if match:
                        lineID = match.group("index")
                        id_match = regex_patterns.SPECTRUM_ID_PATTERN.search(lineID)
                        if id_match:
                            nativeID = int(id_match.group(0))

                elif line_stripped.startswith(XMLTag.SPECTRUM_CLOSE):
                    data += line
                    Writer.add_data(data, nativeID)
                    data = ""
                    nativeID = SpecialID.UNKNOWN

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_OPEN):
                    data += line
                    match = re.search(regex_patterns.CHROMATOGRAM_ID_PATTERN, line)
                    if match:
                        nativeID = match.group(1)

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_CLOSE):
                    data += line
                    Writer.add_data(data, nativeID)
                    if verbose:
                        print("found chromo")
                        print(f"NativeID : {nativeID}", end="\r")
                    data = ""
                    nativeID = SpecialID.UNKNOWN

                elif line_stripped.startswith(XMLTag.SPECTRUM_LIST):
                    data += line
                    Writer.add_data(data, SpecialID.HEAD)
                    if verbose:
                        print("NativeID :", SpecialID.HEAD)
                    data = ""

                elif line_stripped.startswith(XMLTag.CHROMATOGRAM_LIST):
                    data += line
                    Writer.add_data(data, SpecialID.JUNK)
                    if verbose:
                        print("NativeID :", SpecialID.JUNK)
                    data = ""

                else:
                    data += line

            if data:
                Writer.add_data(data, SpecialID.TAIL)
                if verbose:
                    print("NativeID :", SpecialID.TAIL)
        Writer.write_index()


def make_obo_mapping(obo: str, reversed: bool = False) -> dict[str, str]:
    """Create ID-to-name or name-to-ID mapping from OBO file."""
    mapping: dict[str, str] = {}
    id: str = ""
    with open(obo) as obo_file:
        for line in obo_file:
            if line.startswith("id: "):
                id = line.split()[-1]
            elif line.startswith("name: "):
                mapping[id] = " ".join(line.split()[1:])
    if reversed:
        mapping = {y: x for x, y in mapping.items()}
    return mapping


def filter_range(
    arr: NDArray[np.float64],
    mz_range: tuple[float | None, float | None],
) -> NDArray[np.float64]:
    """Filter peaks to specified m/z range."""

    # Handle None values in mz_range
    min_mz = mz_range[0] if mz_range[0] is not None else -np.inf
    max_mz = mz_range[1] if mz_range[1] is not None else np.inf

    mask = np.logical_and(arr[:, 0] >= min_mz, arr[:, 0] <= max_mz)
    peaks = arr[mask]
    return peaks


def filter_noise(
    arr: NDArray[np.float64],
    mode: str | NoiseMode = NoiseMode.MEDIAN,
    noise_level: float | None = None,
    signal_to_noise_threshold: float = 1.0,
) -> NDArray[np.float64]:
    """Remove noise from peaks based on signal-to-noise threshold."""
    # Convert string to enum if needed
    if isinstance(mode, str):  # type: ignore
        mode = NoiseMode(mode)

    if noise_level is None:
        noise_level = estimated_noise_level(arr, mode=mode)

    peaks = arr[arr[:, 1] / noise_level >= signal_to_noise_threshold]

    return peaks


def estimated_noise_level(
    arr: NDArray[np.float64], mode: str | NoiseMode = NoiseMode.MEDIAN
) -> float:
    """Estimate noise level using specified mode (median, mean, or MAD)."""
    # Convert string to enum if needed
    if isinstance(mode, str):  # type: ignore
        mode = NoiseMode(mode)

    if len(arr) == 0:
        return 0.0

    if mode == NoiseMode.MEDIAN:
        return float(np.median(arr[:, 1]))
    elif mode == NoiseMode.MAD:
        median = estimated_noise_level(arr, mode=NoiseMode.MEDIAN)
        return float(np.median(np.abs(arr[:, 1] - median)))
    elif mode == NoiseMode.MEAN:
        return float(np.mean(arr[:, 1]))
    else:
        print(f"Unknown noise level estimation mode: {mode}")
        return 0.0
