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

    FLOAT_32 = "MS:1000521"
    FLOAT_64 = "MS:1000523"
    INT_32 = "MS:1000519"
    INT_64 = "MS:1000522"
    ASCII_STRING = "MS:1001479"


class CompressionTypeAccessions(StrEnum):
    BYTE_SHUFFLED_ZSTD = "MS:1003781"
    MS_NUMPRESS_SHORT_LOGGED_FLOAT = "MS:1002314"
    TRUNCATION_LINEAR_PREDICTION_ZLIB = "MS:1003090"
    ZLIB_COMPRESSION = "MS:1000574"
    NO_COMPRESSION = "MS:1000576"
    DICTIONARY_ENCODED_ZSTD = "MS:1003782"

    # MS-Numpress linear prediction compression followed by zlib compression
    MS_NUMPRESS_LINEAR_PREDICTION_ZLIB = "MS:1002746"
    TRUNCATION_ZLIB = "MS:1003088"
    MS_NUMPRESS_SHORT_LOGGED_FLOAT_ZLIB = "MS:1002748"
    MS_NUMPRESS_LINEAR_PREDICTION_ZSTD = "MS:1003783"
    MS_NUMPRESS_POSITIVE_INTEGER_ZLIB = "MS:1002747"
    MS_NUMPRESS_SHORT_LOGGED_FLOAT_ZSTD = "MS:1003785"
    MS_NUMPRESS_LINEAR_PREDICTION = "MS:1002312"
    MS_NUMPRESS_POSITIVE_INTEGER = "MS:1002313"
    TRUNCATION_DELTA_PREDICTION_ZLIB = "MS:1003089"
    ZSTD_COMPRESSION = "MS:1003780"
    MS_NUMPRESS_POSITIVE_INTEGER_ZSTD = "MS:1003784"


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

    PROFILE = "MS:1000128"
    CENTROID = "MS:1000127"


class XMLTag(StrEnum):
    """Enumeration of XML tag names for parsing."""

    SPECTRUM_OPEN = "<spectrum "
    SPECTRUM_CLOSE = "</spectrum>"
    CHROMATOGRAM_OPEN = "<chromatogram "
    CHROMATOGRAM_CLOSE = "</chromatogram>"
    SPECTRUM_LIST = "<spectrumL"
    CHROMATOGRAM_LIST = "<chromatogramL"


class ScanPolarity(StrEnum):
    """Enumeration of MS accessions for chromatogram properties."""

    POSITIVE_SCAN = "MS:1000129"
    NEGATIVE_SCAN = "MS:1000130"


class SpectrumMSAccession(StrEnum):
    """Enumeration of MS accessions for spectrum properties."""

    MS_LEVEL = "MS:1000511"
    SCAN_START_TIME = "MS:1000016"
    SELECTED_ION_MZ = "MS:1000744"
    PEAK_INTENSITY = "MS:1000042"
    CHARGE_STATE = "MS:1000041"
    TOTAL_ION_CURRENT = "MS:1000285"


class BinaryDataArrayAccession(StrEnum):
    """Enumeration of binary data array accessions."""

    RAW_ION_MOBILITY_ARRAY = "MS:1003007"
    MEAN_ION_MOBILITY_DRIFT_TIME_ARRAY = "MS:1002477"
    DECONVOLUTED_ION_MOBILITY_DRIFT_TIME_ARRAY = "MS:1003156"
    MEAN_INVERSE_REDUCED_ION_MOBILITY_ARRAY = "MS:1003006"
    MEAN_ION_MOBILITY_ARRAY = "MS:1002816"
    DECONVOLUTED_INVERSE_REDUCED_ION_MOBILITY_ARRAY = "MS:1003155"
    RAW_ION_MOBILITY_DRIFT_TIME_ARRAY = "MS:1003153"
    VACUUM_PUMP_PRESSURE = "MS:4000210"
    RAW_INVERSE_REDUCED_ION_MOBILITY_ARRAY = "MS:1003008"
    DECONVOLUTED_ION_MOBILITY_ARRAY = "MS:1003154"
    TIME_ARRAY = "MS:1000595"
    MEAN_CHARGE_ARRAY = "MS:1002478"
    MZ_ARRAY = "MS:1000514"
    SAMPLED_NOISE_INTENSITY_ARRAY = "MS:1002744"
    FLOW_RATE_ARRAY = "MS:1000820"
    CHARGE_ARRAY = "MS:1000516"
    SAMPLED_NOISE_BASELINE_ARRAY = "MS:1002745"
    ION_MOBILITY_ARRAY = "MS:1002893"
    BASELINE_ARRAY = "MS:1002530"
    RESOLUTION_ARRAY = "MS:1002529"
    PRESSURE_ARRAY = "MS:1000821"
    INTENSITY_ARRAY = "MS:1000515"
    MEASURED_ELEMENT = "MS:1002716"
    SCANNING_QUADRUPOLE_POSITION_UPPER_BOUND_MZ_ARRAY = "MS:1003158"
    NON_STANDARD_DATA_ARRAY = "MS:1000786"
    SCANNING_QUADRUPOLE_POSITION_LOWER_BOUND_MZ_ARRAY = "MS:1003157"
    NOISE_ARRAY = "MS:1002742"
    WAVELENGTH_ARRAY = "MS:1000617"
    SIGNAL_TO_NOISE_ARRAY = "MS:1000517"
    MASS_ARRAY = "MS:1003143"
    TEMPERATURE_ARRAY = "MS:1000822"
    SAMPLED_NOISE_MZ_ARRAY = "MS:1002743"


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


# Data type to numpy dtype mapping
BINARY_DECODE_DTYPES: dict[BinaryDataTypeAccession, str] = {
    BinaryDataTypeAccession.FLOAT_32: "float32",
    BinaryDataTypeAccession.FLOAT_64: "float64",
    BinaryDataTypeAccession.INT_32: "int32",
    BinaryDataTypeAccession.INT_64: "int64",
}


class ChromatogramType(StrEnum):
    EMMISION = "MS:1000813"
    SELECTED_ION_MONITORING = "MS:1001472"
    BASEPEAK = "MS:1000628"
    PRECURSOR_ION_CURRENT = "MS:4000025"
    TOTAL_ION_CURRENT = "MS:1000235"
    ABSORPTION = "MS:1000812"
    SELECTED_REACTION_MONITORING = "MS:1001473"
    SELECTED_ION_CURRENT = "MS:1000627"


ISOLATION_WINDOW_TARGET_MZ = "MS:1000827"
