from enum import StrEnum
from typing import NamedTuple
from xml.etree.ElementTree import Element


class ElementType(StrEnum):
    SPECTRUM = "spectrum"
    CHROMATOGRAM = "chromatogram"


class MzmlXMLElement(NamedTuple):
    element: Element
    element_type: ElementType
