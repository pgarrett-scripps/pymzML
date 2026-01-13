import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from typing import Any, Iterator

from .file_interface import FileInterface


@dataclass
class MzMLMetadata:
    """Metadata about an mzML file."""

    file_name: str
    encoding: str
    file_object: FileInterface
    obo_version: str | None = None
    mzml_version: str | None = None
    spectrum_count: int | None = None
    chromatogram_count: int | None = None

    # XML Elements
    file_description_element: ElementTree.Element | None = None
    sample_list_element: ElementTree.Element | None = None
    referenceable_param_group_list_element: ElementTree.Element | None = None
    software_list_element: ElementTree.Element | None = None
    instrument_configuration_list_element: ElementTree.Element | None = None
    data_processing_list_element: ElementTree.Element | None = None
    run_element: ElementTree.Element | None = None

    # Run info
    run_id: str | None = None
    start_time: str | None = None
    instrument_name: str | None = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def keys(self) -> list[str]:
        return [f.name for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def values(self) -> list[Any]:
        return [getattr(self, f.name) for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def items(self) -> list[tuple[str, Any]]:
        return [(f.name, getattr(self, f.name)) for f in self.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    @property
    def has_file_description(self) -> bool:
        return self.file_description_element is not None

    @property
    def has_sample_list(self) -> bool:
        return self.sample_list_element is not None

    @property
    def has_referenceable_param_group_list(self) -> bool:
        return self.referenceable_param_group_list_element is not None

    @property
    def has_software_list(self) -> bool:
        return self.software_list_element is not None

    @property
    def has_instrument_configuration_list(self) -> bool:
        return self.instrument_configuration_list_element is not None

    @property
    def has_data_processing_list(self) -> bool:
        return self.data_processing_list_element is not None

    def next(self) -> Any:
        """Get next item using iterator."""
        return next(iter(self))
