"""mzML schema version registry."""
from __future__ import annotations
from dataclasses import dataclass
import importlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, TYPE_CHECKING, Union
from enum import StrEnum

from xsdata.formats.dataclass.parsers import XmlParser

if TYPE_CHECKING:
    from .dclasses.v1_1_3_idx import IndexedmzMl as V1_1_3_IndexedmzMl
    from .dclasses.v1_1_2_idx import IndexedmzMl as V1_1_2_IndexedmzMl
    from .dclasses.v1_1_1_idx import IndexedmzMl as V1_1_1_IndexedmzMl
    from .dclasses.v1_1_1 import MzMl as V1_1_1_MzMl
    from .dclasses.v1_1_0_idx import IndexedmzMl as V1_1_0_IndexedmzMl
    from .dclasses.v1_1_0 import MzMl as V1_1_0_MzMl
    from .dclasses.v1_0_0_idx import IndexedmzMl as V1_0_0_IndexedmzMl
    from .dclasses.v1_0_0 import MzMl as V1_0_0_MzMl
    from .dclasses.v0_99_12_idx import IndexedmzMl as V0_99_12_IndexedmzMl
    from .dclasses.v0_99_12 import MzMl as V0_99_12_MzMl
    from .dclasses.v0_99_11_idx import IndexedmzMl as V0_99_11_IndexedmzMl
    from .dclasses.v0_99_11 import MzMl as V0_99_11_MzMl
    from .dclasses.v0_99_10_idx import IndexedmzMl as V0_99_10_IndexedmzMl
    from .dclasses.v0_99_10 import MzMl as V0_99_10_MzMl
    from .dclasses.v0_99_9_idx import IndexedmzMl as V0_99_9_IndexedmzMl
    from .dclasses.v0_99_9 import MzMl as V0_99_9_MzMl
    from .dclasses.v0_99_1_idx import IndexedmzMl as V0_99_1_IndexedmzMl
    from .dclasses.v0_99_1 import MzMl as V0_99_1_MzMl
    from .dclasses.v0_99_0_idx import IndexedmzMl as V0_99_0_IndexedmzMl
    from .dclasses.v0_99_0 import MzMl as V0_99_0_MzMl
    from .dclasses.v0_93_idx import IndexedmzMl as V0_93_IndexedmzMl
    from .dclasses.v0_93 import MzMl as V0_93_MzMl

    MzMLObject = Union[
        V1_1_3_IndexedmzMl,
        V1_1_2_IndexedmzMl,
        V1_1_1_IndexedmzMl,
        V1_1_1_MzMl,
        V1_1_0_IndexedmzMl,
        V1_1_0_MzMl,
        V1_0_0_IndexedmzMl,
        V1_0_0_MzMl,
        V0_99_12_IndexedmzMl,
        V0_99_12_MzMl,
        V0_99_11_IndexedmzMl,
        V0_99_11_MzMl,
        V0_99_10_IndexedmzMl,
        V0_99_10_MzMl,
        V0_99_9_IndexedmzMl,
        V0_99_9_MzMl,
        V0_99_1_IndexedmzMl,
        V0_99_1_MzMl,
        V0_99_0_IndexedmzMl,
        V0_99_0_MzMl,
        V0_93_IndexedmzMl,
        V0_93_MzMl,
    ]
else:
    MzMLObject = Any

class MzMLVersion(StrEnum):
    """Supported mzML versions."""

    # 1.1.3
    V1_1_3_IDX = "1.1.3_idx"

    # 1.1.2
    V1_1_2_IDX = "1.1.2_idx"
    
    # 1.1.1
    V1_1_1 = "1.1.1"
    V1_1_1_IDX = "1.1.1_idx"

    # 1.1.0
    V1_1_0 = "1.1.0"
    V1_1_0_IDX = "1.1.0_idx"
    
    # 1.0.0 
    V1_0_0 = "1.0.0"
    V1_0_0_IDX = "1.0.0_idx"

    # 0.99.12
    V0_99_12 = "0.99.12"
    V0_99_12_IDX = "0.99.12_idx"

    # 0.99.11
    V0_99_11 = "0.99.11"
    V0_99_11_IDX = "0.99.11_idx"

    # 0.99.10
    V0_99_10 = "0.99.10"
    V0_99_10_IDX = "0.99.10_idx"

    # 0.99.9
    V0_99_9 = "0.99.9"
    V0_99_9_IDX = "0.99.9_idx"

    # 0.99.1
    V0_99_1 = "0.99.1"
    V0_99_1_IDX = "0.99.1_idx"

    # 0.99.0
    V0_99_0 = "0.99.0"
    V0_99_0_IDX = "0.99.0_idx"
    
    # 0.93
    V0_93 = "0.93"
    V0_93_IDX = "0.93_idx"

    @property
    def is_indexed(self) -> bool:
        return self.value.endswith("_idx")

    @property
    def version_xyz(self) -> str:
        """Returns version string like '1.1.0' without '_idx' suffix."""
        return self.value.replace("_idx", "")

    @property
    def module_name(self) -> str:
        """Returns python module name suffix like 'v1_1_0' or 'v1_1_0_idx'."""
        clean = self.value.replace(".", "_")
        return f"v{clean}"
    
    @property
    def class_name(self) -> str:
        """Returns the main class name expected in the module."""
        return "IndexedmzMl" if self.is_indexed else "MzMl"


def get_local_name(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag

def detect_mzml_version(file_path: str | Path) -> MzMLVersion | None:
    """
    Detect mzML version from file.
    
    Args:
        file_path: Path to mzML file
        
    Returns:
        MzMLVersion enum member or None if not detected/supported.
    """
    try:
        # Use iterparse to lazily read the beginning of the file
        events = iter(ET.iterparse(str(file_path), events=("start",)))
        _, root = next(events)
        
        tag = get_local_name(root.tag)
        is_indexed = (tag == 'indexedmzML')
        version_str: str | None = None
        
        if is_indexed:
            # For indexed files, the version is typically on the child mzML element
            for _, elem in events:
                if get_local_name(elem.tag) == 'mzML':
                    version_str = elem.attrib.get('version')
                    break
        else:
            version_str = root.attrib.get('version')
            
        if not version_str:
            return None

        # Construct lookup key
        lookup_key = version_str
        if is_indexed:
            lookup_key += "_idx"
            
        # Try to find matching enum
        try:
             return MzMLVersion(lookup_key)
        except ValueError:
             # Fallback or specific handling for version strings needing normalization?
             # e.g. "1.1" -> "1.1.0"? For now, assume strict matching or user can expand Enum.
             return None

    except Exception:
        return None


@dataclass
class ParserResult:
    mzml_object: MzMLObject
    version: MzMLVersion

def parse_mzml(file_path: str | Path) -> ParserResult:
    """
    Parse mzML file using the appropriate versioned parser.
    
    Args:
        file_path: Path to mzML file
    
    Returns:
        Parsed mzML object (MzMl or IndexedmzMl)
        
    Raises:
        ValueError: If version cannot be detected or parser not found.
    """
    version_enum = detect_mzml_version(file_path)
    
    if not version_enum:
        raise ValueError(f"Could not detect supported mzML version for file: {file_path}")
    
    module_name = version_enum.module_name
    class_name = version_enum.class_name
        
    try:
        # Import from pymzml.versions.dclasses.{module_name}
        module = importlib.import_module(f".dclasses.{module_name}", package="pymzml.versions")
        clazz = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"No parser available for version {version_enum.value}. module={module_name}") from e
        
    parser = XmlParser()
    return ParserResult(parser.parse(str(file_path), clazz), version_enum)


