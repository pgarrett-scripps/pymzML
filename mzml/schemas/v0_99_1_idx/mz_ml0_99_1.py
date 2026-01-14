from dataclasses import dataclass, field
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://psi.hupo.org/schema_revision/mzML_0.99.1"


@dataclass
class CvparamType:
    """This element holds additional data or annotation.

    Only controlled values are allowed here.

    :ivar cv_label: The short tag for the resource as defined in the
        cvList in this mzML file.
    :ivar accession: The accession number of the referred-to term in the
        named resource (e.g.: MS:000012).
    :ivar value: The value for the parameter; may be absent if not
        appropriate, or a numeric or symbolic value, or may itself be CV
        (legal values for a parameter should be enumerated and defined
        in the ontology).
    :ivar name: The actual name for the parameter, from the referred-to
        controlled vocabulary. This should be the preferred name
        associated with the specified accession number.
    :ivar unit_accession: An optional CV accession number for the unit
        term associated with the value, if any (e.g., 'MS:1000137' for
        'electron volt').
    :ivar unit_name: An optional CV name for the unit accession number,
        if any (e.g., 'electron volt' for 'MS:1000137' ).
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
    Information about an ontology or CV source and a short 'lookup' tag to refer
    to.

    :ivar cv_label: The short label to be used as a reference tag with
        which to refer to this particular Controlled Vocabulary source
        description (e.g., from the cvLabel attribute, in CVParamType
        elements).
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
class InstrumentSoftwareRefType:
    """
    Reference to a previously defined software element.

    :ivar ref: This attribute must be used to reference the 'id'
        attribute of a software element.
    """

    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class ParamGroupRefType:
    """
    A reference to a previously defined ParamGroup, which is a reusable container
    of one or more cvParams.

    :ivar ref: Reference to the id attribute in a previously defined
        ParamGroup.
    """

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
    Software information.
    """


@dataclass
class UserParamType:
    """Uncontrolled user parameters (essentially allowing free text).

    Before using these, one should verify whether there is an
    appropriate CV term available, and if so, use the CV term instead

    :ivar name: The name for the parameter.
    :ivar type_value: The type of the parameter, where appropriate.
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
    Container for one or more controlled vocabulary definitions.

    :ivar cv:
    :ivar count: The number of CV definitionsin this mzML file.
    """

    class Meta:
        name = "CVListType"

    cv: list[Cvtype] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    cv_param: list[CvparamType] = field(
        default_factory=list,
        metadata={
            "name": "cvParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    user_param: list[UserParamType] = field(
        default_factory=list,
        metadata={
            "name": "userParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )


@dataclass
class SoftwareListType:
    """
    List and descriptions of software used to acquire and/or process the data in
    this mzML file.

    :ivar software: A piece of software.
    :ivar count: The number of softwares defined in this mzML file.
    """

    software: list["SoftwareListType.Software"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
        """
        :ivar software_param: A description of the software, based on CV
            information and a software version.
        :ivar id: An identifier for this software that is unique across
            all SoftwareTypes.
        """

        software_param: Optional["SoftwareListType.Software.SoftwareParam"] = (
            field(
                default=None,
                metadata={
                    "name": "softwareParam",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            """
            :ivar cv_label: The CV label for this CV term.
            :ivar accession: The accession number for this CV term.
            :ivar name: The preferred name in the CV for the accession
                number of this CV term.
            :ivar version: The software version.
            """

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
class AcquisitionType(ParamGroupType):
    """
    Scan or acquisition from original raw file used to create this peak list, as
    specified in sourceFile.

    :ivar acq_number: A number for this acquisition.
    :ivar spectrum_ref: This attribute must reference the 'id' attribute
        of the appropriate SpectrumType.
    :ivar source_file_ref: This attribute must reference the 'id'
        attribute of the appropriate SourceFileType.
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
    """The structure into which encoded binary data goes.

    Byte ordering is always little endian (Intel style). Computers using
    a different endian style must convert to/from little endian when
    writing/reading mzML

    :ivar binary: The actual encoded binary data.
    :ivar array_length: The original length of the data array.
    :ivar data_processing_ref: This optional attribute may reference the
        'id' attribute of the appropriate DataProcessingType.
    :ivar encoded_length: The encoded length of the binary data array.
    """

    binary: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
    """
    :ivar order: This attribute must be used to indicate the order in
        which the components are encountered from source to detector
        (e.g., in a Q-TOF, the quadrupole would have the lower order
        number, and the TOF the higher number of the two).
    """

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
    Description of the way in which a particular software was used.

    :ivar processing_method: Description of the default peak processing
        method. This element describes the base method used in the
        generation of a particular mzML file. Variable methods should be
        described in the appropriate acquisition section - if no
        acquisition-specific details are found, then this information
        serves as the default.
    :ivar id: A unique identifier for this data processing that is
        unique across all DataProcessingTypes.
    :ivar software_ref: This attribute must reference the 'id' of the
        appropriate SoftwareType.
    """

    processing_method: list["DataProcessingType.ProcessingMethod"] = field(
        default_factory=list,
        metadata={
            "name": "processingMethod",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
        """
        :ivar order: This attributes allows a series of consecutive
            steps to be placed in the correct order.
        """

        order: Optional[int] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "required": True,
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    activation: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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

    :ivar id: The identifier with which to reference this
        ReferenceableParamGroup.
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

    :ivar id: A unique identifier across the samples with which to
        reference this sample description.
    :ivar name: An optional name for the sample description, mostly
        intended as a quick mnemonic.
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

    :ivar instrument_ref: This attribute must reference the 'id'
        attribute of the appropriate InstrumentType.
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
class SourceFileType(ParamGroupType):
    """
    Description of the source file, including location and type.

    :ivar id: An identifier for this file.
    :ivar source_file_name: Name of the source file, without reference
        to location (either URI or local path).
    :ivar source_file_location: URI-formatted full path to file, without
        actual file name appended.
    """

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


@dataclass
class AcquisitionListType(ParamGroupType):
    """
    List and descriptions of acquisitions .

    :ivar acquisition:
    :ivar count: the number of acquisitions defined in this mzML file.
    """

    acquisition: list[AcquisitionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
class ComponentListType:
    """List with the different components used in the mass spectrometer.

    At least one source, one mass analyzer and one detector need to be
    specified.

    :ivar source: A source component.
    :ivar analyzer: A mass analyzer (or mass filter) component.
    :ivar detector: A detector component.
    :ivar count: The number of components in this list.
    """

    source: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "sequence": 1,
        },
    )
    analyzer: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "sequence": 1,
        },
    )
    detector: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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

    :ivar data_processing:
    :ivar count: The number of DataProcessingTypes in this mzML file.
    """

    data_processing: list[DataProcessingType] = field(
        default_factory=list,
        metadata={
            "name": "dataProcessing",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
class PrecursorListType:
    """
    List and descriptions of precursors to the spectrum currently being described.

    :ivar precursor:
    :ivar count: The number of precursors in this list.
    """

    precursor: list[PrecursorType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
    Container for a list of referenceableParamGroups.

    :ivar referenceable_param_group:
    :ivar count: The number of ParamGroups defined in this mzML file.
    """

    referenceable_param_group: list[ReferenceableParamGroupType] = field(
        default_factory=list,
        metadata={
            "name": "referenceableParamGroup",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
class SourceFileListType:
    """
    List and descriptions of the source files this mzML document was generated or
    derived from.

    :ivar source_file:
    :ivar count: Number of source files used in generating the instance
        document.
    """

    source_file: list[SourceFileType] = field(
        default_factory=list,
        metadata={
            "name": "sourceFile",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    source_file_list: Optional[SourceFileListType] = field(
        default=None,
        metadata={
            "name": "sourceFileList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    contact: list[ParamGroupType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )


@dataclass
class InstrumentType(ParamGroupType):
    """
    Description of the components of the mass spectrometer used.

    :ivar component_list:
    :ivar instrument_software_ref:
    :ivar id: An identifier for this instrument that is unique across
        all instruments.
    """

    component_list: Optional[ComponentListType] = field(
        default=None,
        metadata={
            "name": "componentList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    instrument_software_ref: Optional[InstrumentSoftwareRefType] = field(
        default=None,
        metadata={
            "name": "instrumentSoftwareRef",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    precursor_list: Optional[PrecursorListType] = field(
        default=None,
        metadata={
            "name": "precursorList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    scan: Optional["SpectrumDescriptionType.Scan"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )

    @dataclass
    class Scan(ScanType):
        """
        :ivar selection_window_list: Container for a list of select
            windows.
        """

        selection_window_list: Optional[
            "SpectrumDescriptionType.Scan.SelectionWindowList"
        ] = field(
            default=None,
            metadata={
                "name": "selectionWindowList",
                "type": "Element",
                "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
                "required": True,
            },
        )

        @dataclass
        class SelectionWindowList:
            """
            :ivar selection_window: Definition of a selection window.
            :ivar count: The number of selection windows defined in this
                list.
            """

            selection_window: list[
                "SpectrumDescriptionType.Scan.SelectionWindowList.SelectionWindow"
            ] = field(
                default_factory=list,
                metadata={
                    "name": "selectionWindow",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
                """
                :ivar cv_param: Two or more CV parameters defining the
                    selection window.
                """

                cv_param: list[CvparamType] = field(
                    default_factory=list,
                    metadata={
                        "name": "cvParam",
                        "type": "Element",
                        "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
                        "min_occurs": 2,
                    },
                )


@dataclass
class InstrumentListType:
    """
    List and descriptions of instruments.

    :ivar instrument:
    :ivar count: The number of instruments present in this list.
    """

    instrument: list[InstrumentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
class SpectrumType(ParamGroupType):
    """
    The structure that captures the generation of a peak list (including the
    underlying acquisitions)

    :ivar spectrum_description:
    :ivar binary_data_array:
    :ivar id: A unique identifier for this spectrum. It should be
        expected that external files may use this identifier together
        with the mzML filename or accession to reference a particular
        spectrum.
    :ivar scan_number: The scan number for this spectrum.
    :ivar data_processing_ref: This attribute can optionally reference
        the 'id' of the appropriate DataProcessingType.
    :ivar source_file_ref: This attribute can optionally  reference the
        'id' of the appropriate SourceFileType.
    :ivar ms_level: This attribute must give the MS level as an integer
        (e.g., '1' for MS, '2' for MS/MS, etc.).
    """

    spectrum_description: Optional[SpectrumDescriptionType] = field(
        default=None,
        metadata={
            "name": "spectrumDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    binary_data_array: list[BinaryDataArrayType] = field(
        default_factory=list,
        metadata={
            "name": "binaryDataArray",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
    The definition and specification of a mass spectrometry  run.

    :ivar source_file_ref_list: Container for a list of source file
        references.
    :ivar spectrum_list: All mass spectra and the acquisitions
        underlying them are described and attached here. Subsidiary data
        arrays are also both described and attached here.
    :ivar id: A unique identifier for this run.
    :ivar instrument_ref: This attribute must reference the 'id' of the
        appropriate InstrumentType.
    :ivar sample_ref: This attribute must reference the 'id' of the
        appropriate SampleType.
    :ivar start_time_stamp: The optional start timestamp of the run, in
        UT.
    """

    source_file_ref_list: Optional["RunType.SourceFileRefList"] = field(
        default=None,
        metadata={
            "name": "sourceFileRefList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    spectrum_list: Optional[SpectrumListType] = field(
        default=None,
        metadata={
            "name": "spectrumList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
    start_time_stamp: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "startTimeStamp",
            "type": "Attribute",
        },
    )

    @dataclass
    class SourceFileRefList:
        """
        :ivar source_file_ref: Reference to a previously defined
            sourceFile.
        :ivar count: This number of source files referenced in this
            list.
        """

        source_file_ref: list["RunType.SourceFileRefList.SourceFileRef"] = (
            field(
                default_factory=list,
                metadata={
                    "name": "sourceFileRef",
                    "type": "Element",
                    "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
                },
            )
        )
        count: Optional[int] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "required": True,
            },
        )

        @dataclass
        class SourceFileRef:
            """
            :ivar ref: This attribute must reference the 'id' of the
                appropriate sourceFile.
            """

            ref: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "required": True,
                },
            )


@dataclass
class MzMltype:
    """
    This is the root element for the Proteomics Standards Initiative (PSI) mzML
    schema, which is intended to capture the use of a mass spectrometer, the data
    generated, and the initial processing of that data (to the level of the peak
    list).

    :ivar cv_list:
    :ivar file_description:
    :ivar referenceable_param_group_list:
    :ivar sample_list:
    :ivar instrument_list:
    :ivar software_list:
    :ivar data_processing_list:
    :ivar run:
    :ivar accession: An optional accession number for the mzML document.
    :ivar version: The version of this mzML document.
    :ivar id: An id for the mzML document.
    """

    class Meta:
        name = "mzMLType"

    cv_list: Optional[CvlistType] = field(
        default=None,
        metadata={
            "name": "cvList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    file_description: Optional[FileDescriptionType] = field(
        default=None,
        metadata={
            "name": "fileDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    sample_list: Optional[SampleListType] = field(
        default=None,
        metadata={
            "name": "sampleList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
        },
    )
    instrument_list: Optional[InstrumentListType] = field(
        default=None,
        metadata={
            "name": "instrumentList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    software_list: Optional[SoftwareListType] = field(
        default=None,
        metadata={
            "name": "softwareList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    data_processing_list: Optional[DataProcessingListType] = field(
        default=None,
        metadata={
            "name": "dataProcessingList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
            "required": True,
        },
    )
    run: Optional[RunType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.1",
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
    """
    This is the root element for the Proteomics Standards Initiative (PSI) mzML
    schema, which is intended to capture the use of a mass spectrometer, the data
    generated, and the initial processing of that data (to the level of the peak
    list).
    """

    class Meta:
        name = "mzML"
        namespace = "http://psi.hupo.org/schema_revision/mzML_0.99.1"
