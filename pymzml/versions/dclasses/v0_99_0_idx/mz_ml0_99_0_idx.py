from dataclasses import dataclass, field
from typing import Optional

from mzml.schemas.v0_99_0_idx.mz_ml0_99_0 import MzMl

__NAMESPACE__ = "http://psi.hupo.org/schema_revision/mzML_0.99.0"


@dataclass
class IndexedmzMl:
    """
    Comment describing your root element.

    :ivar mz_ml:
    :ivar index: Index for non sequential data access
    :ivar index_offset: offset of the index element (if 0 no index
        present)
    :ivar file_content_type:
    :ivar file_checksum:
    """

    class Meta:
        name = "indexedmzML"
        namespace = "http://psi.hupo.org/schema_revision/mzML_0.99.0"

    mz_ml: Optional[MzMl] = field(
        default=None,
        metadata={
            "name": "mzML",
            "type": "Element",
            "required": True,
        },
    )
    index: Optional["IndexedmzMl.Index"] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    index_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "indexOffset",
            "type": "Element",
            "nillable": True,
        },
    )
    file_content_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileContentType",
            "type": "Element",
            "required": True,
        },
    )
    file_checksum: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileChecksum",
            "type": "Element",
            "required": True,
        },
    )

    @dataclass
    class Index:
        """
        :ivar offset: Offset of the element identified by name (index
            attribute) and id
        :ivar name: name of the element the index entries are pointing
            to (e.g: scan)
        """

        offset: list["IndexedmzMl.Index.Offset"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )
        name: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "required": True,
            },
        )

        @dataclass
        class Offset:
            """
            :ivar value:
            :ivar id:
            :ivar scan_number: This is a unique identifier for the
                elements of type "name" present in the index (e.g.: for
                an element of type scan, this will be the scan number)
            """

            value: Optional[int] = field(
                default=None,
                metadata={
                    "required": True,
                },
            )
            id: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Attribute",
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
