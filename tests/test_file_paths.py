import os
from enum import StrEnum

DATA_FOLDER = os.path.join(
    *[
        os.path.dirname(__file__),
        # 'tests',
        "data",
    ]
)


class DataFiles(StrEnum):
    EXAMPLE = "example.mzML"
    EXAMPLE_GZ = "example.mzML.gz"
    EXAMPLE_IDX_GZ = "example.mzML.idx.gz"
    MINI_CHROM = "mini.chrom.mzML"
    MINI_CHROM_GZ = "mini.chrom.mzML.gz"
    MINI_CHROM_IDX_GZ = "mini.chrom.mzML.idx.gz"
    MINI_NUMPRESS_CHROM = "mini_numpress.chrom.mzML"
    MINI_NUMPRESS_CHROM_GZ = "mini_numpress.chrom.mzML.gz"
    MINI_NUMPRESS_CHROM_IDX_GZ = "mini_numpress.chrom.mzML.idx.gz"
    BSA1_GZ = "BSA1.mzML.gz"
    EXAMPLE_INVALID_OBO_VERSION = "example_invalid_obo_version.mzML"
    EXAMPLE_NO_OBO_VERSION = "example_no_obo_version.mzML"

def get_data_file_paths(file: DataFiles) -> str:
    return os.path.join(DATA_FOLDER, file.value)


paths = [get_data_file_paths(file) for file in DataFiles]