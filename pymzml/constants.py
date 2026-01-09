from enum import StrEnum


class PeakType(StrEnum):
    """Enumeration of peak types."""

    PROFILE = "profile"
    CENTROIDED = "centroided"
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


class TimeUnit(StrEnum):
    """Enumeration of time units."""

    MILLISECOND = "millisecond"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"


class BinaryDataTypeAccession(StrEnum):
    """Enumeration of binary data type accessions."""

    FLOAT_32 = "MS:1000521"  # 32-bit precision little-endian floating point (IEEE-754)
    FLOAT_64 = "MS:1000523"  # 64-bit precision little-endian floating point (IEEE-754)
    INT_32 = "MS:1000519"  # Signed 32-bit little-endian integer
    INT_64 = "MS:1000522"  # Signed 64-bit little-endian integer
    # MS:1000520 (16-bit float) is obsolete and not included
    ASCII_STRING = "MS:1001479"  # null-terminated ASCII string


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


class OBOKey(StrEnum):
    """Enumeration of OBO dictionary keys."""

    ID = "id"
    NAME = "name"
    DEFINITION = "def"


class OBOSection(StrEnum):
    """Enumeration of OBO file sections."""

    TERM = "[Term]"


class FileExtension(StrEnum):
    """Enumeration of file extensions."""

    GZ = ".gz"
    OBO = ".obo"
    MZML = ".mzml"


class XMLTag(StrEnum):
    """Enumeration of XML tag names for parsing."""

    SPECTRUM_OPEN = "<spectrum "
    SPECTRUM_CLOSE = "</spectrum>"
    CHROMATOGRAM_OPEN = "<chromatogram "
    CHROMATOGRAM_CLOSE = "</chromatogram>"
    SPECTRUM_LIST = "<spectrumL"
    CHROMATOGRAM_LIST = "<chromatogramL"


class SpecialID(StrEnum):
    """Enumeration of special identifier strings."""

    UNKNOWN = "unknown"
    HEAD = "Head"
    TAIL = "tail"
    JUNK = "junk"


class ChromatogramMSAccession(StrEnum):
    """Enumeration of MS accessions for chromatogram properties."""

    POSITIVE_SCAN = "MS:1000129"
    NEGATIVE_SCAN = "MS:1000130"
    ISOLATION_WINDOW_TARGET_MZ = "MS:1000827"


class SpectrumMSAccession(StrEnum):
    """Enumeration of MS accessions for spectrum properties."""

    MS_LEVEL = "MS:1000511"
    SCAN_START_TIME = "MS:1000016"
    SELECTED_ION_MZ = "MS:1000744"
    PEAK_INTENSITY = "MS:1000042"
    CHARGE_STATE = "MS:1000041"
    TOTAL_ION_CURRENT = "MS:1000285"


class XMLNamespace(StrEnum):
    """Enumeration of XML namespace identifiers."""

    SCHEMA_LOCATION = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"


class MzMLElement(StrEnum):
    """Enumeration of mzML element tag names (without namespace)."""

    MZML = "mzML"
    CV = "cv"
    FILE_DESCRIPTION = "fileDescription"
    SAMPLE_LIST = "sampleList"
    REFERENCEABLE_PARAM_GROUP_LIST = "referenceableParamGroupList"
    SOFTWARE_LIST = "softwareList"
    INSTRUMENT_CONFIG_LIST = "instrumentConfigurationList"
    DATA_PROCESSING_LIST = "dataProcessingList"
    CV_PARAM = "cvParam"
    SPECTRUM_LIST = "spectrumList"
    CHROMATOGRAM_LIST = "chromatogramList"
    RUN = "run"
    SPECTRUM = "spectrum"
    CHROMATOGRAM = "chromatogram"


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
    BinaryDataTypeAccession.FLOAT_32: "float32",
    BinaryDataTypeAccession.FLOAT_64: "float64",
    BinaryDataTypeAccession.INT_32: "int32",
    BinaryDataTypeAccession.INT_64: "int64",
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
