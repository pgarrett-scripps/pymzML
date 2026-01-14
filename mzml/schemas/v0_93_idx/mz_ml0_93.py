from dataclasses import dataclass, field
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://psi.hupo.org/schema_revision/mzML_0.93"


@dataclass
class CvparamType:
    """This element holds additional data or annotation.

    Only controlled values are allowed here.

    :ivar cv_label: The short tag for the resource as defined in the
        cvList in this mzML file.
    :ivar accession: The accession number of the referred-to term in the
        named resource (e.g.: PSI-MS:000012).
    :ivar value: The value for the parameter; may be absent if not
        appropriate, or a numeric or symbolic value, or may itself be CV
        (legal values for a parameter should be enumerated and defined
        in the ontology).
    :ivar name: The actual name for the parameter, from the referred-to
        controlled vocabulary. This should be the preferred name
        associated with the specified accession number.
    :ivar unit_accession:
    :ivar unit_name:
    """

    class Meta:
        name = "CVParamType"

    cv_label: Optional[str] = field(
        default=None,
        metadata={
            "name": "cvLabel",
            "type": "Attribute",
            "required": True,
        },
    )
    accession: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    unit_accession: Optional[str] = field(
        default=None,
        metadata={
            "name": "unitAccession",
            "type": "Attribute",
        },
    )
    unit_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "unitName",
            "type": "Attribute",
        },
    )


@dataclass
class Cvtype:
    """
    Information about an ontology/CV source and a short 'lookup' tag to refer to.

    :ivar cv_label: The short label to be used as a reference tag with
        which to refer to this particulart Controlled Vocabulary source
        description, from an instance of the cvLabel attribute, where it
        appears (i.e. in things of type paramType).
    :ivar full_name: The usual name for the resource (e.g. The PSI-MS
        Controlled Vocabulary).
    :ivar version: The version of the CV from which the referred-to
        terms are drawn.
    :ivar uri: The URI for the resource.
    """

    class Meta:
        name = "CVType"

    cv_label: Optional[str] = field(
        default=None,
        metadata={
            "name": "cvLabel",
            "type": "Attribute",
            "required": True,
        },
    )
    full_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "fullName",
            "type": "Attribute",
            "required": True,
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "URI",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ContactType:
    """
    Audit information concerning the means by which the originator/owner of this
    mzML file can be identified, and contacted if necessary.

    :ivar name: Contact person name, or role name (e.g. "Group leader of
        team 42") of the individual responsible for this dataset.
    :ivar institution: Academic or corporate organisation with which the
        contact person or role is associated.
    :ivar uri:
    """

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    institution: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "URI",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )


@dataclass
class FileChecksumType:
    """
    Checksum to verify the file.
    """

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class InstrumentSoftwareRefType:
    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ParamGroupRefType:
    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SoftwareType:
    """
    Software information (the software that produced the peak list).
    """


@dataclass
class UserParamType:
    """
    Uncontrolled user parameters (vocabulary).

    :ivar name: The actual name for the parameter.
    :ivar type_value:
    :ivar value: The value for the parameter, where appropriate.
    """

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class CvlistType:
    """
    List and descriptions of CV.

    :ivar cv:
    :ivar count: The number of CV definitionsin this mzML file.
    """

    class Meta:
        name = "CVListType"

    cv: list[Cvtype] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ParamGroupType:
    """
    Structure allowing the use of a controlled (cvParam) or uncontrolled vocabulary
    (userParam), or a reference to a predefined set of these in this mzML file
    (paramGroupRef).
    """

    param_group_ref: list[ParamGroupRefType] = field(
        default_factory=list,
        metadata={
            "name": "paramGroupRef",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    cv_param: list[CvparamType] = field(
        default_factory=list,
        metadata={
            "name": "cvParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    user_param: list[UserParamType] = field(
        default_factory=list,
        metadata={
            "name": "userParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )


@dataclass
class SoftwareListType:
    """
    List and descriptions of software used to acquire and/or process the data in
    this mzML file.

    :ivar software:
    :ivar count: The number of softwares defined in this mzML file.
    """

    software: list["SoftwareListType.Software"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )

    @dataclass
    class Software(SoftwareType):
        software_param: Optional["SoftwareListType.Software.SoftwareParam"] = (
            field(
                default=None,
                metadata={
                    "name": "softwareParam",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
                    "required": True,
                },
            )
        )
        id: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "required": True,
            },
        )

        @dataclass
        class SoftwareParam:
            cv_label: Optional[str] = field(
                default=None,
                metadata={
                    "name": "cvLabel",
                    "type": "Attribute",
                    "required": True,
                },
            )
            accession: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "required": True,
                },
            )
            name: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "required": True,
                },
            )
            version: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "required": True,
                },
            )


@dataclass
class SourceFileType:
    """
    Description of the source file, including location and type.

    :ivar file_checksum: Checksum to verify the file
    :ivar id:
    :ivar source_file_name: Name of the source file, without reference
        to location (either URI or local path).
    :ivar source_file_location: URI-formatted full path to file, without
        actual file name appended.
    :ivar source_file_type: Type of the file if appropriate, else a
        description of the software or reference resource used.
    """

    file_checksum: Optional[FileChecksumType] = field(
        default=None,
        metadata={
            "name": "fileChecksum",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    source_file_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileName",
            "type": "Attribute",
            "required": True,
        },
    )
    source_file_location: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileLocation",
            "type": "Attribute",
            "required": True,
        },
    )
    source_file_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileType",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class AcquisitionType(ParamGroupType):
    """
    Scan or acquisition from original raw file used to create this peak list, as
    specified in sourceFile.
    """

    acq_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "acqNumber",
            "type": "Attribute",
            "required": True,
        },
    )
    spectrum_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "spectrumRef",
            "type": "Attribute",
            "required": True,
        },
    )
    source_file_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileRef",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class BinaryDataArrayType(ParamGroupType):
    """
    The structure into which encoded binary data goes.
    """

    binary: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
            "format": "base64",
        },
    )
    array_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "arrayLength",
            "type": "Attribute",
            "required": True,
        },
    )
    data_processing_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataProcessingRef",
            "type": "Attribute",
        },
    )
    data_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataType",
            "type": "Attribute",
            "required": True,
        },
    )
    compression_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "compressionType",
            "type": "Attribute",
            "required": True,
        },
    )
    encoded_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "encodedLength",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ComponentType(ParamGroupType):
    order: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class DataProcessingType:
    """
    Description of the software, and the way in which it was used to generate the
    peak list.

    :ivar processing_method: Description of the default peak processing
        method. This element describes the base method used in the
        generation of a particular mzML file. Variable methods should be
        described in the appropriate acquisition section - if no
        acquisition-specific details are found, then this information
        serves as the default.
    :ivar id:
    :ivar software_ref:
    """

    processing_method: list["DataProcessingType.ProcessingMethod"] = field(
        default_factory=list,
        metadata={
            "name": "processingMethod",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    software_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareRef",
            "type": "Attribute",
            "required": True,
        },
    )

    @dataclass
    class ProcessingMethod(ParamGroupType):
        order: Optional[int] = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )


@dataclass
class PrecursorType:
    """
    The method of precursor ion selection and activation.

    :ivar ion_selection: This captures the type of ion selection being
        performed, and trigger m/z (or m/z's), neutral loss criteria
        etc. for tandem-MS or data dependent scans.
    :ivar activation: The type and energy level used for activation.
    :ivar spectrum_ref: Reference to the id attribute of the spectrum
        from which the precursor was selected.
    """

    ion_selection: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "name": "ionSelection",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    activation: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    spectrum_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "spectrumRef",
            "type": "Attribute",
        },
    )


@dataclass
class ReferenceableParamGroupType(ParamGroupType):
    """
    ParamGroup that can be referenced from elsewhere in this mzML document by using
    the 'paramGroupRef' element in that location to reference the 'id' attribute
    value of this element.
    """

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SampleType(ParamGroupType):
    """
    Expansible description of the sample used to generate the dataset, named in
    sampleName.
    """

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ScanType(ParamGroupType):
    """
    The instrument's 'run time' parameters; common to the whole of this spectrum.
    """

    instrument_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "instrumentRef",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SourceFileListType:
    """
    List and descriptions of source files.

    :ivar source_file:
    :ivar count: Number of sources files used in generating the instance
        document.
    """

    source_file: list[SourceFileType] = field(
        default_factory=list,
        metadata={
            "name": "sourceFile",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class AcquisitionListType:
    """
    List and descriptions of acquisitions .

    :ivar acquisition:
    :ivar count: the number of acquisitions defined in this mzML file.
    :ivar method_of_combination: The method (most usually summing or
        some form of averaging) by which the acquisitions were combined
        to make the spectrum.
    """

    acquisition: list[AcquisitionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    method_of_combination: Optional[str] = field(
        default=None,
        metadata={
            "name": "methodOfCombination",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ComponentListType:
    """
    List with the different components used in the mass spectrometer.
    """

    source: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "sequence": 1,
        },
    )
    analyzer: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "sequence": 1,
        },
    )
    detector: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "sequence": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class DataProcessingListType:
    """
    List and descriptions of data processing applied to this data.
    """

    data_processing: list[DataProcessingType] = field(
        default_factory=list,
        metadata={
            "name": "dataProcessing",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class FileDescriptionType:
    """
    Information pertaining to the entire mzML file (i.e. not specific to any part
    of the data set) is stored here.

    :ivar file_content: This summarizes the different types of spectra
        that can be expected in the file. This is expected to aid
        processing software in skipping files that do not contain
        appropriate spectrum types for it.
    :ivar source_file_list:
    :ivar contact:
    """

    file_content: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "name": "fileContent",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    source_file_list: Optional[SourceFileListType] = field(
        default=None,
        metadata={
            "name": "sourceFileList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    contact: list[ContactType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )


@dataclass
class PrecursorListType:
    """
    List and descriptions of precursors to the spectrum currently being described.
    """

    precursor: list[PrecursorType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ReferenceableParamGroupListType:
    """
    List and descriptions of ReferenceableParamGroups.

    :ivar referenceable_param_group:
    :ivar count: The number of ParamGroups defined in this mzML file.
    """

    referenceable_param_group: list[ReferenceableParamGroupType] = field(
        default_factory=list,
        metadata={
            "name": "referenceableParamGroup",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SampleListType:
    """
    List and descriptions of samples.

    :ivar sample:
    :ivar count: The number of Samples defined in this mzML file.
    """

    sample: list[SampleType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class InstrumentType(ParamGroupType):
    """
    Description of the components of the mass spectrometer used.
    """

    component_list: Optional[ComponentListType] = field(
        default=None,
        metadata={
            "name": "componentList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    instrument_software_ref: Optional[InstrumentSoftwareRefType] = field(
        default=None,
        metadata={
            "name": "instrumentSoftwareRef",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SpectrumDescriptionType(ParamGroupType):
    """
    Description of the parameters for the mass spectrometer for a given acquisition
    (or list of acquisitions).
    """

    acquisition_list: Optional[AcquisitionListType] = field(
        default=None,
        metadata={
            "name": "acquisitionList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    precursor_list: Optional[PrecursorListType] = field(
        default=None,
        metadata={
            "name": "precursorList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    scan: Optional["SpectrumDescriptionType.Scan"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )

    @dataclass
    class Scan(ScanType):
        selection_window_list: Optional[
            "SpectrumDescriptionType.Scan.SelectionWindowList"
        ] = field(
            default=None,
            metadata={
                "name": "selectionWindowList",
                "type": "Element",
                "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
                "required": True,
            },
        )

        @dataclass
        class SelectionWindowList:
            selection_window: list[
                "SpectrumDescriptionType.Scan.SelectionWindowList.SelectionWindow"
            ] = field(
                default_factory=list,
                metadata={
                    "name": "selectionWindow",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
                    "min_occurs": 1,
                },
            )
            count: Optional[int] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "required": True,
                },
            )

            @dataclass
            class SelectionWindow:
                cv_param: list[CvparamType] = field(
                    default_factory=list,
                    metadata={
                        "name": "cvParam",
                        "type": "Element",
                        "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
                        "min_occurs": 2,
                    },
                )


@dataclass
class InstrumentListType:
    """
    List and descriptions of instruments.
    """

    instrument: list[InstrumentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SpectrumType:
    """
    The structure that captures the generation of a peak list (including the
    underlying acquisitions)
    """

    spectrum_description: Optional[SpectrumDescriptionType] = field(
        default=None,
        metadata={
            "name": "spectrumDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    binary_data_array: list[BinaryDataArrayType] = field(
        default_factory=list,
        metadata={
            "name": "binaryDataArray",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    scan_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "scanNumber",
            "type": "Attribute",
            "required": True,
        },
    )
    data_processing_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataProcessingRef",
            "type": "Attribute",
        },
    )
    source_file_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileRef",
            "type": "Attribute",
        },
    )
    spectrum_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "spectrumType",
            "type": "Attribute",
            "required": True,
        },
    )
    ms_level: Optional[int] = field(
        default=None,
        metadata={
            "name": "msLevel",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SpectrumListType:
    """
    List and descriptions of spectra.

    :ivar spectrum:
    :ivar count: The number of spectra defined in this mzML file.
    """

    spectrum: list[SpectrumType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class RunType(ParamGroupType):
    """
    :ivar source_file_ref_list:
    :ivar spectrum_list: All mass spectra and the acquisitions
        underlying them are described and attached here. Subsidiary data
        arrays are also both described and attached here.
    :ivar id:
    :ivar instrument_ref:
    :ivar sample_ref:
    :ivar time_stamp:
    """

    source_file_ref_list: Optional["RunType.SourceFileRefList"] = field(
        default=None,
        metadata={
            "name": "sourceFileRefList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    spectrum_list: Optional[SpectrumListType] = field(
        default=None,
        metadata={
            "name": "spectrumList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    instrument_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "instrumentRef",
            "type": "Attribute",
            "required": True,
        },
    )
    sample_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "sampleRef",
            "type": "Attribute",
        },
    )
    time_stamp: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "timeStamp",
            "type": "Attribute",
        },
    )

    @dataclass
    class SourceFileRefList:
        source_file_ref: list["RunType.SourceFileRefList.SourceFileRef"] = (
            field(
                default_factory=list,
                metadata={
                    "name": "sourceFileRef",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
                },
            )
        )
        count: Optional[int] = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

        @dataclass
        class SourceFileRef:
            ref: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                },
            )


@dataclass
class RunListType:
    """
    List and descriptions of Runs.
    """

    run: list[RunType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "min_occurs": 1,
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MzMltype:
    """This schema can capture the use of a mass spectrometer, the data generated,
    and the initial processing of that data (to the level of the peak list).

    Peak lists are processed data from a mass spectrometry experiment.
    There can be multiple peak lists in an mzML file, which might be
    related via a separation, or just in sequence from an automated run.
    Any one peak list (mass spectrum) may also be composed of a number
    of acquisitions, which can be described individually herein.
    """

    class Meta:
        name = "mzMLType"

    file_description: Optional[FileDescriptionType] = field(
        default=None,
        metadata={
            "name": "fileDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    cv_list: Optional[CvlistType] = field(
        default=None,
        metadata={
            "name": "cvList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    referenceable_param_group_list: Optional[
        ReferenceableParamGroupListType
    ] = field(
        default=None,
        metadata={
            "name": "referenceableParamGroupList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    sample_list: Optional[SampleListType] = field(
        default=None,
        metadata={
            "name": "sampleList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
        },
    )
    instrument_list: Optional[InstrumentListType] = field(
        default=None,
        metadata={
            "name": "instrumentList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    software_list: Optional[SoftwareListType] = field(
        default=None,
        metadata={
            "name": "softwareList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    data_processing_list: Optional[DataProcessingListType] = field(
        default=None,
        metadata={
            "name": "dataProcessingList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    run_list: Optional[RunListType] = field(
        default=None,
        metadata={
            "name": "runList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.93",
            "required": True,
        },
    )
    accession: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MzMl(MzMltype):
    """This schema can capture the use of a mass spectrometer, the data generated,
    and the initial processing of that data (to the level of the peak list).

    Peak lists are processed data from a mass spectrometry experiment.
    There can be multiple peak lists in an mzML file, which might be
    related via a separation, or just in sequence from an automated run.
    Any one peak list (mass spectrum) may also be composed of a number
    of acquisitions, which can be described individually herein.
    """

    class Meta:
        name = "mzML"
        namespace = "http://psi.hupo.org/schema_revision/mzML_0.93"
