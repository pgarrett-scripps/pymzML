#!/usr/bin/env python3
"""
Part of pymzml test cases
"""
import pymzml as pmz
import unittest
import test_file_paths


class StandardGzipTest(unittest.TestCase):
    """ " """

    def setUp(self):
        """ """
        paths = test_file_paths.paths
        self.File = pmz.StandardGzip(paths[1], "latin-1")

    def tearDown(self):
        """ """
        self.File.close()

    def test_getitem_5(self):
        """ """
        ID = 5
        spec = self.File.get_spectrum_by_index(ID)  
        self.assertIsInstance(spec, pmz.MzmlXMLElement)

    def test_getitem_tic(self):
        ID = "TIC"
        chrom = self.File.TIC
        self.assertIsInstance(chrom, pmz.MzmlXMLElement)


if __name__ == "__main__":
    unittest.main(verbosity=3)
