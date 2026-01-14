from dataclasses import dataclass, field
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://psi.hupo.org/schema_revision/mzML_0.99.11"


@dataclass
class CvparamType:
    """This element holds additional data or annotation.

    Only controlled values are allowed here.

    :ivar cv_ref: A reference to the CV 'id' attribute as defined in the
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
        term associated with the value, if any (e.g., 'UO:0000266' for
        'electron volt').
    :ivar unit_name: An optional CV name for the unit accession number,
        if any (e.g., 'electron volt' for 'UO:0000266' ).
    """

    class Meta:
        name = "CVParamType"

    cv_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "cvRef",
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

    :ivar id: The short label to be used as a reference tag with which
        to refer to this particular Controlled Vocabulary source
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

    id: Optional[str] = field(
        default=None,
        metadata={
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
class ReferenceableParamGroupRefType:
    """
    A reference to a previously defined ParamGroup, which is a reusable container
    of one or more cvParams.

    :ivar ref: Reference to the id attribute in a
        referenceableParamGroup.
    """

    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SoftwareParamType:
    """
    :ivar cv_ref: A reference to the CV 'id' attribute as defined in the
        cvList in this mzML file.
    :ivar accession: The accession number for this CV term.
    :ivar name: The preferred name in the CV for the accession number of
        this CV term.
    :ivar version: The software version.
    """

    cv_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "cvRef",
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
class SoftwareRefType:
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
class SourceFileRefType:
    """
    :ivar ref: This attribute must reference the 'id' of the appropriate
        sourceFile.
    """

    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class UserParamType:
    """Uncontrolled user parameters (essentially allowing free text).

    Before using these, one should verify whether there is an
    appropriate CV term available, and if so, use the CV term instead

    :ivar name: The name for the parameter.
    :ivar type_value: The datatype of the parameter, where appropriate
        (e.g.: xsd:float).
    :ivar value: The value for the parameter, where appropriate.
    :ivar unit_accession: An optional CV accession number for the unit
        term associated with the value, if any (e.g., 'UO:0000266' for
        'electron volt').
    :ivar unit_name: An optional CV name for the unit accession number,
        if any (e.g., 'electron volt' for 'UO:0000266' ).
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
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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

    referenceable_param_group_ref: list[ReferenceableParamGroupRefType] = (
        field(
            default_factory=list,
            metadata={
                "name": "referenceableParamGroupRef",
                "type": "Element",
                "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            },
        )
    )
    cv_param: list[CvparamType] = field(
        default_factory=list,
        metadata={
            "name": "cvParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    user_param: list[UserParamType] = field(
        default_factory=list,
        metadata={
            "name": "userParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )


@dataclass
class ReferenceableParamGroupType:
    """
    A collection of CVParam and UserParam elements that can be referenced from
    elsewhere in this mzML document by using the 'paramGroupRef' element in that
    location to reference the 'id' attribute value of this element.

    :ivar cv_param:
    :ivar user_param:
    :ivar id: The identifier with which to reference this
        ReferenceableParamGroup.
    """

    cv_param: list[CvparamType] = field(
        default_factory=list,
        metadata={
            "name": "cvParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    user_param: list[UserParamType] = field(
        default_factory=list,
        metadata={
            "name": "userParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class ScanWindowType:
    """
    :ivar cv_param: Two or more CV parameters defining the selection
        window.
    """

    cv_param: list[CvparamType] = field(
        default_factory=list,
        metadata={
            "name": "cvParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "min_occurs": 2,
        },
    )


@dataclass
class SoftwareType:
    """
    Software information.

    :ivar software_param: A description of the software, based on CV
        information and a software version.
    :ivar id: An identifier for this software that is unique across all
        SoftwareTypes.
    """

    software_param: Optional[SoftwareParamType] = field(
        default=None,
        metadata={
            "name": "softwareParam",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class SourceFileRefListType:
    """
    :ivar source_file_ref: Reference to a previously defined sourceFile.
    :ivar count: This number of source files referenced in this list.
    """

    source_file_ref: list[SourceFileRefType] = field(
        default_factory=list,
        metadata={
            "name": "sourceFileRef",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class AcquisitionType(ParamGroupType):
    """
    Scan or acquisition from original raw file used to create this peak list, as
    specified in sourceFile.

    :ivar number: A number for this acquisition.
    :ivar spectrum_ref: For acquisitions that are local to this
        document, this attribute must reference the 'id' attribute of
        the appropriate spectrum.
    :ivar source_file_ref: For acquisitions that are external to this
        document, this attribute must reference the 'id' attribute of a
        sourceFile representing that external document.
    :ivar external_native_id: For acquisitions that are external to this
        document which can be referenced by nativeID, this string must
        correspond to the 'nativeID' attribute of a spectrum in the
        external document indicated by 'sourceFileRef'.
    :ivar external_spectrum_id: For acquisitions that are external to
        this document which cannot be referenced by nativeID, this
        string must correspond to the 'id' attribute of a spectrum in
        the external document indicated by 'sourceFileRef'.
    """

    number: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
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
    source_file_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "sourceFileRef",
            "type": "Attribute",
        },
    )
    external_native_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "externalNativeID",
            "type": "Attribute",
        },
    )
    external_spectrum_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "externalSpectrumID",
            "type": "Attribute",
        },
    )


@dataclass
class BinaryDataArrayType(ParamGroupType):
    """The structure into which encoded binary data goes.

    Byte ordering is always little endian (Intel style). Computers using
    a different endian style must convert to/from little endian when
    writing/reading mzML

    :ivar binary: The actual base64 encoded binary data.
    :ivar array_length: This optional attribute may override the
        'defaultArrayLength' defined in SpectrumType. The two default
        arrays (m/z and intensity) should NEVER use this override
        option, and should therefore adhere to the 'defaultArrayLength'
        defined in SpectrumType. Parsing software can thus safely choose
        to ignore arrays of lengths different from the one defined in
        the 'defaultArrayLength' SpectrumType element.
    :ivar data_processing_ref: This optional attribute may reference the
        'id' attribute of the appropriate dataProcessing.
    :ivar encoded_length: The encoded length of the binary data array.
    """

    binary: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
            "format": "base64",
        },
    )
    array_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "arrayLength",
            "type": "Attribute",
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
class ProcessingMethodType(ParamGroupType):
    """
    :ivar order: This attributes allows a series of consecutive steps to
        be placed in the correct order.
    """

    order: Optional[int] = field(
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class ScanWindowListType:
    """
    :ivar scan_window: Definition of a selection window.
    :ivar count: The number of selection windows defined in this list.
    """

    scan_window: list[ScanWindowType] = field(
        default_factory=list,
        metadata={
            "name": "scanWindow",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class SelectedIonListType:
    """
    The list of selected precursor ions.

    :ivar selected_ion:
    :ivar count: The number of selected precursor ions defined in this
        list.
    """

    selected_ion: list[ParamGroupType] = field(
        default_factory=list,
        metadata={
            "name": "selectedIon",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class SoftwareListType:
    """
    List and descriptions of software used to acquire and/or process the data in
    this mzML file.

    :ivar software: A piece of software.
    :ivar count: The number of softwares defined in this mzML file.
    """

    software: list[SoftwareType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class SourceFileType(ParamGroupType):
    """
    Description of the source file, including location and type.

    :ivar id: An identifier for this file.
    :ivar name: Name of the source file, without reference to location
        (either URI or local path).
    :ivar location: URI-formatted location where the file was retrieved.
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
            "required": True,
        },
    )
    location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class TargetListType:
    """
    Target list (or 'inclusion list') configured prior to the run.

    :ivar target:
    :ivar count: The number of TargetType elements in this list.
    """

    target: list[ParamGroupType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class AcquisitionSettingsType(ParamGroupType):
    """
    Description of the acquisition settings of the instrument prior to the start of
    the run.

    :ivar source_file_ref_list: List with the source files containing
        the acquisition settings.
    :ivar target_list: Target list (or 'inclusion list') configured
        prior to the run.
    :ivar id: A unique identifier for this acquisition setting.
    :ivar instrument_configuration_ref: This attribute must reference
        the 'id' of the appropriate instrument configuration.
    """

    source_file_ref_list: Optional[SourceFileRefListType] = field(
        default=None,
        metadata={
            "name": "sourceFileRefList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    target_list: Optional[TargetListType] = field(
        default=None,
        metadata={
            "name": "targetList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    instrument_configuration_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "instrumentConfigurationRef",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class BinaryDataArrayListType:
    """
    List of binary data arrays.

    :ivar binary_data_array:
    :ivar count: The number of binary data arrays defined in this list.
    """

    binary_data_array: list[BinaryDataArrayType] = field(
        default_factory=list,
        metadata={
            "name": "binaryDataArray",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "min_occurs": 2,
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "sequence": 1,
        },
    )
    analyzer: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "sequence": 1,
        },
    )
    detector: list[ComponentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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

    processing_method: list[ProcessingMethodType] = field(
        default_factory=list,
        metadata={
            "name": "processingMethod",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class PrecursorType:
    """
    The method of precursor ion selection and activation.

    :ivar isolation_window: This element captures the isolation (or
        'selection') window configured to isolate one or more
        precursors.
    :ivar selected_ion_list: This list of precursor ions that were
        selected.
    :ivar activation: The type and energy level used for activation.
    :ivar spectrum_ref: Reference to the id attribute of the spectrum
        from which the precursor was selected.
    """

    isolation_window: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "name": "isolationWindow",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    selected_ion_list: Optional[SelectedIonListType] = field(
        default=None,
        metadata={
            "name": "selectedIonList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    activation: Optional[ParamGroupType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class ScanType(ParamGroupType):
    """
    The instrument's 'run time' parameters; common to the whole of this spectrum.

    :ivar scan_window_list: Container for a list of select windows.
    :ivar instrument_configuration_ref: This attribute must reference
        the 'id' attribute of the appropriate instrument configuration.
    """

    scan_window_list: Optional[ScanWindowListType] = field(
        default=None,
        metadata={
            "name": "scanWindowList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    instrument_configuration_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "instrumentConfigurationRef",
            "type": "Attribute",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class AcquisitionSettingsListType:
    """
    List with the descriptions of the acquisition settings applied prior to the
    start of data acquisition.

    :ivar acquisition_settings:
    :ivar count: The number of AcquisitionType elements in this list.
    """

    acquisition_settings: list[AcquisitionSettingsType] = field(
        default_factory=list,
        metadata={
            "name": "acquisitionSettings",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class ChromatogramType(ParamGroupType):
    """
    A single chromatogram.

    :ivar binary_data_array_list:
    :ivar id: A unique identifier for this chromatogram.
    :ivar native_id: The native identifier for the spectrum, used by the
        acquisition software.
    :ivar index: The zero-based index for this chromatogram in the
        chromatogram list.
    :ivar default_array_length: Default length of binary data arrays
        contained in this element.
    :ivar data_processing_ref: This attribute can optionally reference
        the 'id' of the appropriate dataProcessing.
    """

    binary_data_array_list: Optional[BinaryDataArrayListType] = field(
        default=None,
        metadata={
            "name": "binaryDataArrayList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
    native_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "nativeID",
            "type": "Attribute",
            "required": True,
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    default_array_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "defaultArrayLength",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    source_file_list: Optional[SourceFileListType] = field(
        default=None,
        metadata={
            "name": "sourceFileList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    contact: list[ParamGroupType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )


@dataclass
class InstrumentConfigurationType(ParamGroupType):
    """Description of a particular hardware configuration of a mass spectrometer.

    Each configuration must have one (and only one) of the three
    different components used for an analysis. For hybrid instruments,
    such as an LTQ-FT, there must be one configuration for each
    permutation of the components that is used in the document. For
    software configuration, use a ReferenceableParamGroup element.

    :ivar component_list:
    :ivar software_ref:
    :ivar id: An identifier for this instrument configuration.
    """

    component_list: Optional[ComponentListType] = field(
        default=None,
        metadata={
            "name": "componentList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    software_ref: Optional[SoftwareRefType] = field(
        default=None,
        metadata={
            "name": "softwareRef",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class ChromatogramListType:
    """
    List of chromatograms.

    :ivar chromatogram:
    :ivar count: The number of chromatograms defined in this mzML file.
    """

    chromatogram: list[ChromatogramType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
class InstrumentConfigurationListType:
    """
    List and descriptions of instrument configurations.

    :ivar instrument_configuration:
    :ivar count: The number of instrument configurations present in this
        list.
    """

    instrument_configuration: list[InstrumentConfigurationType] = field(
        default_factory=list,
        metadata={
            "name": "instrumentConfiguration",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    precursor_list: Optional[PrecursorListType] = field(
        default=None,
        metadata={
            "name": "precursorList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    scan: Optional[ScanType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )


@dataclass
class SpectrumType(ParamGroupType):
    """
    The structure that captures the generation of a peak list (including the
    underlying acquisitions)

    :ivar spectrum_description:
    :ivar binary_data_array_list:
    :ivar id: A unique identifier for this spectrum. It should be
        expected that external files may use this identifier together
        with the mzML filename or accession to reference a particular
        spectrum.
    :ivar native_id: The native identifier for the spectrum, used by the
        acquisition software.
    :ivar index: The zero-based, consecutive index of  the spectrum in
        the SpectrumList.
    :ivar default_array_length: Default length of binary data arrays
        contained in this element.
    :ivar data_processing_ref: This attribute can optionally reference
        the 'id' of the appropriate dataProcessing.
    :ivar source_file_ref: This attribute can optionally  reference the
        'id' of the appropriate sourceFile.
    """

    spectrum_description: Optional[SpectrumDescriptionType] = field(
        default=None,
        metadata={
            "name": "spectrumDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    binary_data_array_list: Optional[BinaryDataArrayListType] = field(
        default=None,
        metadata={
            "name": "binaryDataArrayList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    native_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "nativeID",
            "type": "Attribute",
            "required": True,
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    default_array_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "defaultArrayLength",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
    A run in mzML should correspond to a single, consecutive and coherent set of
    scans on an instrument.

    :ivar source_file_ref_list: Container for a list of source file
        references.
    :ivar spectrum_list: All mass spectra and the acquisitions
        underlying them are described and attached here. Subsidiary data
        arrays are also both described and attached here.
    :ivar chromatogram_list: All chromatograms for thsi run.
    :ivar id: A unique identifier for this run.
    :ivar default_instrument_configuration_ref: This attribute must
        reference the 'id' of the default instrument configuration. If a
        scan does not reference an instrument configuration, it
        implicitly refers to this configuration.
    :ivar sample_ref: This attribute must reference the 'id' of the
        appropriate sample.
    :ivar start_time_stamp: The optional start timestamp of the run, in
        UT.
    """

    source_file_ref_list: Optional[SourceFileRefListType] = field(
        default=None,
        metadata={
            "name": "sourceFileRefList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    spectrum_list: Optional[SpectrumListType] = field(
        default=None,
        metadata={
            "name": "spectrumList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    chromatogram_list: Optional[ChromatogramListType] = field(
        default=None,
        metadata={
            "name": "chromatogramList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    default_instrument_configuration_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "defaultInstrumentConfigurationRef",
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
    :ivar instrument_configuration_list:
    :ivar software_list:
    :ivar data_processing_list:
    :ivar acquisition_settings_list:
    :ivar run:
    :ivar accession: An optional accession number for the mzML document.
    :ivar version: The version of this mzML document.
    :ivar id: An optional id for the mzML document. It is recommended to
        use LSIDs when possible.
    """

    class Meta:
        name = "mzMLType"

    cv_list: Optional[CvlistType] = field(
        default=None,
        metadata={
            "name": "cvList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    file_description: Optional[FileDescriptionType] = field(
        default=None,
        metadata={
            "name": "fileDescription",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    sample_list: Optional[SampleListType] = field(
        default=None,
        metadata={
            "name": "sampleList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    instrument_configuration_list: Optional[
        InstrumentConfigurationListType
    ] = field(
        default=None,
        metadata={
            "name": "instrumentConfigurationList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    software_list: Optional[SoftwareListType] = field(
        default=None,
        metadata={
            "name": "softwareList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    data_processing_list: Optional[DataProcessingListType] = field(
        default=None,
        metadata={
            "name": "dataProcessingList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
            "required": True,
        },
    )
    acquisition_settings_list: Optional[AcquisitionSettingsListType] = field(
        default=None,
        metadata={
            "name": "acquisitionSettingsList",
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
        },
    )
    run: Optional[RunType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://psi.hupo.org/schema_revision/mzML_0.99.11",
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
        namespace = "http://psi.hupo.org/schema_revision/mzML_0.99.11"
