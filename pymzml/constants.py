from enum import StrEnum


class PeakType(StrEnum):
    """Enumeration of peak types."""

    RAW = "raw"
    CENTROIDED = "centroided"
    REPROFILED = "reprofiled"
    DECONVOLUTED = "deconvoluted"


class NoiseMode(StrEnum):
    """Enumeration of noise estimation modes."""

    MEDIAN = "median"
    MEAN = "mean"
    MAD = "mad"


class DataType(StrEnum):
    """Enumeration of data array types."""

    MZ = "mz"
    INTENSITY = "i"
    TIME = "time"


class BinaryDataType(StrEnum):
    """Enumeration of binary data types for mzML encoding."""

    FLOAT_32 = "32-bit float"
    FLOAT_64 = "64-bit float"
    INT_32 = "32-bit integer"
    INT_64 = "64-bit integer"
    ASCII_STRING = "null-terminated ASCII string"


class CompressionType(StrEnum):
    """Enumeration of compression types for mzML data."""

    ZLIB = "zlib"
    ZLIB_COMPRESSION = "zlib compression"
    NUMPRESS_LINEAR = "ms-np-linear"
    NUMPRESS_PIC = "ms-np-pic"
    NUMPRESS_SLOF = "ms-np-slof"
    NUMPRESS_LINEAR_FULL = "MS-Numpress linear prediction compression"
    NUMPRESS_SLOF_FULL = "MS-Numpress short logged float compression"


class MSAccession(StrEnum):
    """Enumeration of MS ontology accessions."""

    NUMPRESS_LINEAR = "MS:1002312"
    NUMPRESS_PIC = "MS:1002313"
    NUMPRESS_SLOF = "MS:1002314"


class XMLAttribute(StrEnum):
    """Enumeration of common XML attribute names."""

    ACCESSION = "accession"
    NAME = "name"
    DEFAULT_ARRAY_LENGTH = "defaultArrayLength"


class XMLElement(StrEnum):
    """Enumeration of common XML element names."""

    BINARY_DATA_ARRAY_LIST = "binaryDataArrayList"
    BINARY_DATA_ARRAY = "binaryDataArray"
    CV_PARAM = "cvParam"
    BINARY = "binary"


class EncodingFormat(StrEnum):
    """Enumeration of encoding formats."""

    LATIN1 = "latin-1"
    UTF8 = "utf-8"
    XML = "xml"


class SpectrumType(StrEnum):
    """Enumeration of spectrum types."""

    PROFILE = "profile spectrum"
    CENTROID = "centroid spectrum"


PROTON_MASS = 1.00727646677
ISOTOPE_AVERAGE_DIFFERENCE = 1.002

# Numpress compression types set for fast lookup
NUMPRESS_COMPRESSIONS = frozenset(
    {
        CompressionType.NUMPRESS_LINEAR,
        CompressionType.NUMPRESS_PIC,
        CompressionType.NUMPRESS_SLOF,
        CompressionType.NUMPRESS_LINEAR_FULL,
        CompressionType.NUMPRESS_SLOF_FULL,
    }
)

# Data type to numpy dtype mapping
BINARY_DECODE_DTYPES = {
    BinaryDataType.FLOAT_32: "float32",
    BinaryDataType.FLOAT_64: "float64",
    BinaryDataType.INT_32: "int32",
    BinaryDataType.INT_64: "int64",
}


chromatogram_type_accessions = {
    "MS:1000235",
    "MS:1000627",
    "MS:1000628",
    "MS:1000810",
    "MS:1000811",
    "MS:1000812",
    "MS:1000813",
    "MS:1000814",
    "MS:1000815",
    "MS:1001472",
    "MS:1001473",
    "MS:1001474",
    "MS:1001475",
    "MS:1001476",
    "MS:1001477",
    "MS:1001478",
    "MS:1001479",
    "MS:1001480",
}
