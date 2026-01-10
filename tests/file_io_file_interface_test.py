#!/usr/bin/env python3
"""
Part of pymzml test cases
"""

from pymzml.file_interface import FileInterface
from pymzml.file_classes.standardGzip import StandardGzip
from pymzml.file_classes.standardMzml import StandardMzml, BytesMzml
import unittest
import test_file_paths


class FileInterfaceTest(unittest.TestCase):
    """ """

    def setUp(self):
        """ """
        self.paths = test_file_paths.paths
        test_file = self.paths[1]
        self.file_interface = FileInterface(test_file, "latin-1")

    def tearDown(self):
        """ """
        self.file_interface.close()

    def test_init(self):
        """ """
        self.assertIsNotNone(self.file_interface.file_handler)

    def test_open(self):
        """ """
        self.assertIsInstance(self.file_interface.file_handler, StandardMzml)
        self.file_interface.close()
        self.file_interface = FileInterface(self.paths[0], "latin-1")
        self.assertIsInstance(self.file_interface.file_handler, StandardMzml)
        self.file_interface.close()

        # extract gzip = false
        self.file_interface = FileInterface(self.paths[1], "latin-1", extract_gzip=False)
        self.assertIsInstance(self.file_interface.file_handler, StandardGzip)
        self.file_interface.close()

        # extract with in_memory
        self.file_interface = FileInterface(self.paths[1], "latin-1", in_memory=True)
        self.assertIsInstance(self.file_interface.file_handler, BytesMzml)
        self.file_interface.close()
        
        # extract gzip = false
        self.file_interface = FileInterface(self.paths[1], "latin-1", in_memory=True, extract_gzip=False)
        self.assertIsInstance(self.file_interface.file_handler, BytesMzml)
        self.file_interface.close()



if __name__ == "__main__":
    unittest.main(verbosity=3)
