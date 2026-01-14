import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from typing import Any, Iterator, Literal, NamedTuple

from .constants import MzMLElement, XMLNamespace
from .regex_patterns import MZML_VERSION_PATTERN


class CVElement(NamedTuple):
    """Named tuple for controlled vocabulary elements."""

    id: str
    full_name: str
    version: str
    uri: str


class CVParam(NamedTuple):
    """Named tuple for controlled vocabulary elements."""

    cv_ref: str
    accession: str
    name: str
    value: str


class HasCVParams:
    """Mixin for classes with cv_params attribute."""

    cv_params: tuple[CVParam, ...]

    def get_cv_param(self, accession: str) -> CVParam | None:
        """Get CV param by accession."""
        return next((p for p in self.cv_params if p.accession == accession), None)


@dataclass(frozen=True, slots=True)
class SourceFile(HasCVParams):
    id: str
    name: str
    location: str
    cv_params: tuple[CVParam, ...]


@dataclass(frozen=True, slots=True)
class FileDescription:
    file_content: tuple[CVParam, ...]
    source_files: tuple[SourceFile, ...]


@dataclass(frozen=True, slots=True)
class ReferenceableParamGroup(HasCVParams):
    id: str
    cv_params: tuple[CVParam, ...]


@dataclass(frozen=True, slots=True)
class Software(HasCVParams):
    id: str
    version: str
    cv_params: tuple[CVParam, ...]


ComponentType = Literal["source", "analyzer", "detector"]


@dataclass(frozen=True, slots=True)
class Component(HasCVParams):
    order: int
    type: ComponentType
    cv_params: tuple[CVParam, ...]


@dataclass(frozen=True, slots=True)
class InstrumentConfiguration:
    id: str
    components: tuple[Component, ...]
    referenceable_param_group_ref: str | None = None
    software_ref: str | None = None

    def get_components_by_type(self, comp_type: ComponentType) -> tuple[Component, ...]:
        """Get all components of specified type."""
        return tuple(c for c in self.components if c.type == comp_type)


@dataclass(frozen=True, slots=True)
class ProcessingMethod(HasCVParams):
    order: int
    software_ref: str
    cv_params: tuple[CVParam, ...]


@dataclass(frozen=True, slots=True)
class DataProcessing:
    id: str
    processing_methods: tuple[ProcessingMethod, ...]


@dataclass(frozen=True, slots=True)
class Run:
    id: str
    default_instrument_configuration_ref: str | None = None
    start_time_stamp: str | None = None
    default_source_file_ref: str | None = None


@dataclass(frozen=True, slots=True)
class MzMLContent:
    """Root mzML content structure."""

    # Required fields
    id: str
    version: str

    # Optional metadata (most files have these)
    cv_list: tuple[CVElement, ...] = ()
    file_description: FileDescription | None = None
    referenceable_param_groups: tuple[ReferenceableParamGroup, ...] = ()
    software_list: tuple[Software, ...] = ()
    instrument_configurations: tuple[InstrumentConfiguration, ...] = ()
    data_processing_list: tuple[DataProcessing, ...] = ()
    run: Run | None = None

    # XML attributes (usually not needed by users)
    xmlns: str | None = None
    xmlns_xsi: str | None = None
    xsi_schema_location: str | None = None


def get_tag(element: ElementTree.Element) -> str:
    return element.tag.split("}")[-1] if "}" in element.tag else element.tag


def _parse_cv_params(element: ElementTree.Element) -> tuple[CVParam, ...]:
    cv_params: list[CVParam] = []
    for child in element:
        if get_tag(child) == "cvParam":
            cv_params.append(
                CVParam(
                    cv_ref=child.attrib.get("cvRef", ""),
                    accession=child.attrib.get("accession", ""),
                    name=child.attrib.get("name", ""),
                    value=child.attrib.get("value", ""),
                )
            )
    return tuple(cv_params)


def _parse_source_file(source_file_element: ElementTree.Element) -> SourceFile:
    return SourceFile(
        id=source_file_element.attrib.get("id", ""),
        name=source_file_element.attrib.get("name", ""),
        location=source_file_element.attrib.get("location", ""),
        cv_params=_parse_cv_params(source_file_element),
    )


def _parse_file_description(description_element: ElementTree.Element) -> FileDescription:
    file_content: tuple[CVParam, ...] = ()
    source_files: list[SourceFile] = []

    for child in description_element:
        tag = get_tag(child)
        if tag == "fileContent":
            file_content = _parse_cv_params(child)
        elif tag == "sourceFileList":
            for sf in child:
                if get_tag(sf) == "sourceFile":
                    source_files.append(_parse_source_file(sf))

    return FileDescription(file_content=file_content, source_files=tuple(source_files))


def _parse_referenceable_param_group(
    referenceable_param_group_element: ElementTree.Element,
) -> ReferenceableParamGroup:
    return ReferenceableParamGroup(
        id=referenceable_param_group_element.attrib.get("id", ""),
        cv_params=_parse_cv_params(referenceable_param_group_element),
    )


def _parse_software(software_element: ElementTree.Element) -> Software:
    return Software(
        id=software_element.attrib.get("id", ""),
        version=software_element.attrib.get("version", ""),
        cv_params=_parse_cv_params(software_element),
    )


def _parse_component(element: ElementTree.Element, order: int) -> Component:
    return Component(
        order=order,
        type=element.tag.split("}")[-1],  # type: ignore
        cv_params=_parse_cv_params(element),
    )


def _parse_instrument_configuration(
    instrument_configuration_element: ElementTree.Element,
) -> InstrumentConfiguration:
    components: list[Component] = []
    rpg_ref = None
    sw_ref = None

    for child in instrument_configuration_element:
        tag = get_tag(child)
        if tag == "componentList":
            for comp in child:
                order = int(comp.attrib.get("order", "0"))
                components.append(_parse_component(comp, order))
        elif tag == "referenceableParamGroupRef":
            rpg_ref = child.attrib.get("ref")
        elif tag == "softwareRef":
            sw_ref = child.attrib.get("ref")

    return InstrumentConfiguration(
        id=instrument_configuration_element.attrib.get("id", ""),
        components=tuple(components),
        referenceable_param_group_ref=rpg_ref,
        software_ref=sw_ref,
    )


def _parse_processing_method(processing_method_element: ElementTree.Element) -> ProcessingMethod:
    return ProcessingMethod(
        order=int(processing_method_element.attrib.get("order", "0")),
        software_ref=processing_method_element.attrib.get("softwareRef", ""),
        cv_params=_parse_cv_params(processing_method_element),
    )


def _parse_data_processing(data_processing_element: ElementTree.Element) -> DataProcessing:
    methods: list[ProcessingMethod] = []
    for child in data_processing_element:
        if get_tag(child) == "processingMethod":
            methods.append(_parse_processing_method(child))

    return DataProcessing(
        id=data_processing_element.attrib.get("id", ""),
        processing_methods=tuple(methods),
    )


class MzMLContentBuilder:
    """Builder that parses mzML metadata from XML iterator."""

    def __init__(self) -> None:
        self._id = ""
        self._version = ""
        self._cv_list: list[CVElement] = []
        self._file_description: FileDescription | None = None
        self._referenceable_param_groups: list[ReferenceableParamGroup] = []
        self._software_list: list[Software] = []
        self._instrument_configurations: list[InstrumentConfiguration] = []
        self._data_processing_list: list[DataProcessing] = []

        # Extra metadata not in MzMLContent
        self.obo_version: str | None = None
        self.run_id: str | None = None
        self.start_time: str | None = None
        self.spectrum_count: int | None = None
        self.chromatogram_count: int | None = None

        self._handlers: dict[str, Any] = {
            MzMLElement.MZML: self._handle_mzml,
            MzMLElement.CV: self._handle_cv,
            MzMLElement.FILE_DESCRIPTION: self._handle_file_description,
            MzMLElement.REFERENCEABLE_PARAM_GROUP_LIST: self._handle_referenceable_param_group_list,
            MzMLElement.SOFTWARE_LIST: self._handle_software_list,
            MzMLElement.INSTRUMENT_CONFIG_LIST: self._handle_instrument_configuration_list,
            MzMLElement.DATA_PROCESSING_LIST: self._handle_data_processing_list,
        }

    def parse_from_iterator(self, mzml_iter: Iterator[tuple[str, ElementTree.Element]]) -> None:
        """Parse metadata from mzML iterator until reaching run element."""
        while True:
            event, element = next(mzml_iter, ("END", "END"))

            if event == "END" and element == "END":
                break

            tag = get_tag(element)

            if event == "start":
                if tag == "mzML":
                    self._handle_mzml(element)
                elif tag == "run":
                    self._handle_run(element)
                    return

            if event == "end" and (handler := self._handlers.get(tag)):
                if tag != "mzML" and tag != "run":
                    handler(element)
                    element.clear()

    def _handle_mzml(self, element: ElementTree.Element) -> None:
        if version := element.attrib.get("version"):
            self._version = version
        else:
            schema_location = element.attrib.get(XMLNamespace.SCHEMA_LOCATION, "")
            if match_result := MZML_VERSION_PATTERN.search(schema_location):
                self._version = match_result.group()
        self._id = element.attrib.get("id", "")

    def _handle_cv(self, element: ElementTree.Element) -> None:
        cv = CVElement(
            id=element.attrib.get("id", ""),
            full_name=element.attrib.get("fullName", ""),
            version=element.attrib.get("version", ""),
            uri=element.attrib.get("URI", ""),
        )
        self._cv_list.append(cv)

        if element.attrib.get("id") == "MS":
            if obo_version := element.attrib.get("version"):
                self.obo_version = obo_version

    def _handle_file_description(self, element: ElementTree.Element) -> None:
        self._file_description = _parse_file_description(element)

    def _handle_referenceable_param_group_list(self, element: ElementTree.Element) -> None:
        for child in element:
            if get_tag(child) == "referenceableParamGroup":
                self._referenceable_param_groups.append(_parse_referenceable_param_group(child))

    def _handle_software_list(self, element: ElementTree.Element) -> None:
        for child in element:
            if get_tag(child) == "software":
                self._software_list.append(_parse_software(child))

    def _handle_instrument_configuration_list(self, element: ElementTree.Element) -> None:
        for child in element:
            if get_tag(child) == "instrumentConfiguration":
                self._instrument_configurations.append(_parse_instrument_configuration(child))

    def _handle_data_processing_list(self, element: ElementTree.Element) -> None:
        for child in element:
            if get_tag(child) == "dataProcessing":
                self._data_processing_list.append(_parse_data_processing(child))

    def _handle_run(self, element: ElementTree.Element) -> None:
        self.run_id = element.attrib.get("id")
        self.start_time = element.attrib.get("startTimeStamp")

    def build(self) -> MzMLContent:
        """Build immutable MzMLContent from parsed data."""
        return MzMLContent(
            id=self._id,
            version=self._version,
            cv_list=tuple(self._cv_list),
            file_description=self._file_description,
            referenceable_param_groups=tuple(self._referenceable_param_groups),
            software_list=tuple(self._software_list),
            instrument_configurations=tuple(self._instrument_configurations),
            data_processing_list=tuple(self._data_processing_list),
        )
