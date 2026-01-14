from dataclasses import dataclass, field
from typing import Optional

from mzml.schemas.v1_0_0_idx.mz_ml1_0_0 import MzMl

__NAMESPACE__ = "http://psi.hupo.org/schema_revision/mzML_1.0.0"


@dataclass
class IndexedmzMl:
    """
    Container element for mzML which allows the addition  of an index.

    :ivar mz_ml:
    :ivar index_list: List of indices.
    :ivar index_list_offset: File pointer offset (in bytes) of the
        'indexList' element.
    :ivar file_checksum: SHA-1 checksum from beginning of file to end of
        'fileChecksum' open tag.
    """

    class Meta:
        name = "indexedmzML"
        namespace = "http://psi.hupo.org/schema_revision/mzML_1.0.0"

    mz_ml: Optional[MzMl] = field(
        default=None,
        metadata={
            "name": "mzML",
            "type": "Element",
            "required": True,
        },
    )
    index_list: Optional["IndexedmzMl.IndexList"] = field(
        default=None,
        metadata={
            "name": "indexList",
            "type": "Element",
            "required": True,
        },
    )
    index_list_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "indexListOffset",
            "type": "Element",
            "nillable": True,
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
    class IndexList:
        """
        :ivar index: Index element containing one or more offsets for
            random data access for the entity described in the 'name'
            attribute.
        :ivar count: Number of indices in this list.
        """

        index: list["IndexedmzMl.IndexList.Index"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
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
        class Index:
            """
            :ivar offset: File pointer offset (in bytes) of the element
                identified by the 'id' attribute.
            :ivar name: The name of the entity the index entries are
                pointing to.
            """

            offset: list["IndexedmzMl.IndexList.Index.Offset"] = field(
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
                :ivar id_ref: Reference to the 'id' attribute of the
                    indexed element.
                :ivar native_id: The native identifier for the spectrum,
                    used by the acquisition software.
                :ivar spot_id: The identifier for the spot from which
                    this spectrum was derived, if a MALDI or similar
                    run.
                """

                value: Optional[int] = field(
                    default=None,
                    metadata={
                        "required": True,
                    },
                )
                id_ref: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "idRef",
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
                spot_id: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "spotID",
                        "type": "Attribute",
                    },
                )
