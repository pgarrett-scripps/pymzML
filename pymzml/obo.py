"""OBO file parser for MS accession mapping (MS:xxxxx to names)."""

import contextlib
import gzip
import os
import re
import sys
import urllib.request
from re import Pattern
from typing import Any, ClassVar

from .constants import FileExtension, OBOKey, OBOSection


class OboTranslator:
    """Map MS accessions to names and vice versa for a specific obo version."""

    _obo_instance_cache: ClassVar[dict[str | None, "OboTranslator"]] = {}

    def __init__(self, version: str | None = None) -> None:
        """Initialize OboTranslator with optional version specification."""
        self.version: str | None = self._normalize_version(version)
        self.all_dicts: list[dict[str, Any]] = []
        self.id: dict[str, dict[str, Any]] = {}
        self.name: dict[str, dict[str, Any]] = {}
        self.definition: dict[str, dict[str, Any]] = {}
        self.lookups: list[dict[str, dict[str, Any]]] = [self.id, self.name, self.definition]
        self.MS_tag_regex: Pattern[str] = re.compile(r"MS:[0-9]*")

        # Only parse the OBO when necessary, not upon object construction
        self.__obo_parsed: bool = False

    @classmethod
    def from_cache(cls, version: str | None) -> "OboTranslator":
        normalized_version = cls._normalize_version(version)
        try:
            return cls._obo_instance_cache[normalized_version]
        except KeyError:
            inst = cls._obo_instance_cache[normalized_version] = cls(version)
            return inst

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("OBO translator dictionaries only support assignment via .add")

    def __getitem__(self, key: str) -> Any | None:
        if not self.__obo_parsed:
            self.parseOBO()

        for lookup in self.lookups:
            if key in lookup:
                if self.MS_tag_regex.match(key):
                    with contextlib.suppress(Exception):
                        return lookup[key][OBOKey.NAME]
                return lookup[key]
        return None

    @staticmethod
    def _normalize_version(version: str | None) -> str | None:
        """Normalize version string to 3-part format (e.g., 1.2.0)."""
        if version is not None:
            parts = version.split(".")

            missing_parts = 3 - len(parts)
            if missing_parts > 0:
                version = ".".join(parts + ["0"] * missing_parts)

        return version

    def download_obo(self, version: str | None, obo_file: str) -> None:
        """Download OBO file from GitHub and compress it."""
        uri = f"https://raw.githubusercontent.com/pymzml/psi-ms-CV/v{self.version}/psi-ms.obo"
        urllib.request.urlretrieve(uri, obo_file)

        with open(obo_file, "rb") as fin, gzip.open(obo_file + ".gz", "wb") as fout:
            fout.writelines(fin.readlines())
            os.remove(obo_file)
        return

    def parseOBO(self) -> None:
        """Parse OBO file from obo directory or download if needed."""
        self.__obo_parsed = True

        # TODO: Try to get all the versions, even those without well-defined
        #       version numbers, or get remote hosting of all of the versions
        #       and only download one at will on demand.

        # Modify the root for cx_freeze
        if getattr(sys, "frozen", False):
            obo_root = os.path.dirname(sys.executable)
        else:
            obo_root = os.path.dirname(__file__)

        obo_file = os.path.join(
            obo_root,
            "obo",
            f"psi-ms{'-' + self.version if self.version else ''}{FileExtension.OBO}",
        )
        if os.path.exists(obo_file):
            pass
        elif os.path.exists(obo_file + FileExtension.GZ):
            obo_file = obo_file + FileExtension.GZ
        else:
            self.download_obo(self.version, obo_file)
            obo_file += FileExtension.GZ

        with open(obo_file, "rb") as fin:
            # never rely on file extensions!
            first_two_bytes = fin.read(2)
            # check if file is gzipped by magic bytes
            if first_two_bytes == b"\x1f\x8b":
                open_func = gzip.open
            else:
                raise Exception(
                    "Filename has .gz extension but is missing the gzip magic bytes.\n"
                    "The file may be corrupted or not gzipped."
                )

        with open_func(obo_file, "rt", encoding="utf-8") as obo:
            collections: dict[str, str] = {}
            collect = False
            for line in obo:
                if line.strip() in (OBOSection.TERM, ""):
                    collect = True
                    if not collections:
                        continue
                    self.add(collections)
                    collections = {}
                else:
                    if line.strip() != "" and collect is True:
                        k = line.find(":")
                        collections[line[:k]] = line[k + 1 :].strip()
        return

    def add(self, collection_dict: dict[str, Any]) -> None:
        """Add a mapping dictionary to the translator."""
        if not self.__obo_parsed:
            self.parseOBO()

        self.all_dicts.append(collection_dict)
        if OBOKey.ID in collection_dict:
            self.id[collection_dict[OBOKey.ID]] = self.all_dicts[-1]
        if OBOKey.NAME in collection_dict:
            self.name[collection_dict[OBOKey.NAME]] = self.all_dicts[-1]
        if OBOKey.DEFINITION in collection_dict:
            self.definition[collection_dict[OBOKey.DEFINITION]] = self.all_dicts[-1]

        return

    def checkOBO(self, idTag: str, name: str) -> bool:
        """Check if MS accession tag matches given name."""
        if not self.__obo_parsed:
            self.parseOBO()

        return self.id[idTag][OBOKey.NAME] == name


if __name__ == "__main__":
    print(__doc__)
