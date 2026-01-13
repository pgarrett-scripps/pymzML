from numpy.ma import isin
import sys
import os
import unittest

sys.path.append(os.path.abspath("."))

import pymzml as pmz
import test_file_paths

DECON_DEP: bool
try:
    import ms_deisotope

    DECON_DEP = True
except ImportError:
    DECON_DEP = False


class SpectrumMS2Test(unittest.TestCase):
    """
        BSA test file

    Peptide @
    Scan: 2548
    RT [min] 28.96722412109367
    Selected_precursor [(443.711242675781, 0.0)]

    """

    def setUp(self):
        """ """
        # self.paths = [
        #     os.path.join( DATA_FOLDER, file ) for file in DATA_FILES]
        self.paths = test_file_paths.paths
        path = self.paths[9]
        self.Run = pmz.Reader(path)
        self.spec = self.Run.spectra.get_by_id("spectrum=2548")

    def test_scan_time(self):
        scan_time = self.spec.scan_time_minutes
        scan_time2 = self.spec.scan_time_minutes  # Access again to test caching
        self.assertIsNotNone(scan_time)
        self.assertIsInstance(scan_time, float)
        self.assertEqual(round(scan_time, 4), round(28.96722412109367, 4))
        self.assertEqual(scan_time, scan_time2)

    def test_select_precursors(self):
        selected_precursor = self.spec.selected_precursors
        self.assertIsInstance(selected_precursor[0]["mz"], float)
        self.assertIsInstance(selected_precursor[0]["i"], float)
        self.assertIsInstance(selected_precursor[0]["charge"], int)
        assert selected_precursor[0]["mz"] == 443.711242675781
        assert selected_precursor[0]["i"] == 0.0
        assert selected_precursor[0]["precursor id"] is None

    def test_ion_mode(self):
        assert self.spec.negative_scan == True

    def test_ion_mode_non_existent(self):
        assert self.spec.positive_scan == False

if __name__ == "__main__":
    unittest.main(verbosity=3)
