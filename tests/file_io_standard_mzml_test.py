#!/usr/bin/env python3
"""
Part of pymzml test cases
"""

import unittest
import test_file_paths

import pymzml as pmz

class StandardMzmlTest(unittest.TestCase):
    """ """

    def setUp(self):
        """ """
        paths = test_file_paths.paths
        self.standard_mzml = pmz.StandardMzml(paths[0], "latin-1")

    def tearDown(self):
        """ """
        self.standard_mzml.close()

    def test_getitem(self):
        """ """
        id = 8
        spec = self.standard_mzml.get_spectrum_by_index(id)
        self.assertIsInstance(spec, pmz.MzmlXMLElement)
        self.assertEqual(spec.element_type, pmz.ElementType.SPECTRUM)

        chrom = self.standard_mzml.TIC
        self.assertIsInstance(chrom, pmz.MzmlXMLElement)
        self.assertEqual(chrom.element_type, pmz.ElementType.CHROMATOGRAM)



if __name__ == "__main__":
    unittest.main(verbosity=3)
