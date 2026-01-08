#!/usr/bin/env python3
"""
Part of pymzml test cases
"""

from pymzml.file_classes.standardMzml import StandardMzml
import unittest
from pymzml.spec import Spectrum
from pymzml.chromatogram import Chromatogram
import test_file_paths


class StandardMzmlTest(unittest.TestCase):
    """ """

    def setUp(self):
        """ """
        paths = test_file_paths.paths
        self.standard_mzml = StandardMzml(paths[0], "latin-1")

    def tearDown(self):
        """ """
        self.standard_mzml.close()

    def test_getitem(self):
        """ """
        id = 8
        spec = self.standard_mzml[id]
        self.assertIsInstance(spec, Spectrum)
        target_ID = spec.ID # type: ignore
        self.assertEqual(id, target_ID)

        id = "TIC"
        chrom = self.standard_mzml[id]
        self.assertIsInstance(chrom, Chromatogram)
        self.assertEqual(id, chrom.ID) # type: ignore

    def test_interpol_search(self):
        """ """
        spec = self.standard_mzml._interpol_search(5) # type: ignore
        self.assertIsInstance(spec, Spectrum)


if __name__ == "__main__":
    unittest.main(verbosity=3)
