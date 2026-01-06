"""
Additional functions for converting file etc.

@author M. Kösters
"""


import pymzml.regex_patterns as regex_patterns
import re
import gzip
from typing import Dict, Callable, Union, IO

from .gzip_writer import GzipWriter
from ..constants import FileExtension, SpecialID, XMLTag

def index_gzip(
    pathIn: str,
    pathOut: str,
    max_idx: int = 10000,
    idx_len: int = 8,
    verbose: bool = False,
    comp_str: int = -1,
) -> None:
    """
    Convert an mzml file (can be gzipped) into an indexed, gzipped mzML file.

    Arguments:
        pathIn (str): path to an mzML input File.
        pathOut (str): path were the index gzip will be created.

    Keyword Arguments:
        max_idx (int): number of indexes which can be saved.
        idx_len (int): character len of on key
        verbose (boolean): print progress while parsing input.
        comp_str(int): compression strength of zlib compression,
            needs to  be 1 <= x <= 9
    """
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
            nativeID: Union[int, str] = SpecialID.UNKNOWN
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
    """
    Convert an mzml file (can be gzipped) into an indexed, gzipped mzML file.

    Arguments:
        pathIn (str): path to input File.
        pathOut (str): path were output should be created.

    Keyword Arguments:
        max_idx (int): number of indexes which can be saved.
        idx_len (int): character len of on key
        verbose (boolean): print progress while parsing input.
        comp_str(int): compression strength of zlib compression,
            needs to  be 1 <= x <= 9
    """
    with GzipWriter(
        output_path=pathOut,
        max_idx=max_idx,
        max_idx_len=idx_len,
        max_offset_len=idx_len,
        comp_str=comp_str,
    ) as Writer:
        with gzip.open(pathIn, "rt") as Reader:  # type: ignore
            data = ""
            nativeID: Union[int, str] = SpecialID.UNKNOWN
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


def make_obo_mapping(obo: str, reversed: bool = False) -> Dict[str, str]:
    """
    Create a mapping dictionary from an OBO file.

    Arguments:
        obo (str): path to OBO file
        reversed (bool): if True, reverse the mapping (name -> id instead of id -> name)

    Returns:
        Dict[str, str]: mapping dictionary
    """
    mapping: Dict[str, str] = {}
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


if __name__ == "__main__":
    print(__doc__)
