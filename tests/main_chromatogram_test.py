import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import pymzml.run as run
import numpy as np
import unittest
import test_file_paths


class ChromatogramTest(unittest.TestCase):
    def assertPeaksIdentical(self, peaks1, peaks2, msg=None):
        self.assertEqual(len(peaks1), len(peaks2))  # , msg='List have different number of peaks!')
        for x in range(len(peaks1)):
            self.assertCountEqual(peaks1[x], peaks2[x], msg=msg)

    def setUp(self):
        self.paths = test_file_paths.paths
        path = test_file_paths.get_data_file_paths(test_file_paths.DataFiles.EXAMPLE)
        self.run_np = run.Reader(path)
        self.chrom = self.run_np.TIC
        assert self.chrom is not None
        
    def test_i(self):
        self.chrom.profile = [(1, 10), (2, 20), (3, 30)]
        peaks = self.chrom.profile
        print(peaks)
        self.assertPeaksIdentical(peaks, [(1, 10), (2, 20), (3, 30)])

    def test_profile(self):
        profile = self.chrom.profile
        time = self.chrom.time
        intensity = self.chrom.intensity
        self.assertIsNotNone(time)
        self.assertIsNotNone(intensity)
        self.assertIsNotNone(profile)
        if np:
            self.assertIsInstance(profile, np.ndarray)
        else:
            self.assertIsInstance(profile, list)


if __name__ == "__main__":
    unittest.main(verbosity=3)
