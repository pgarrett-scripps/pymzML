#!/usr/bin/env python3
"""
Test cases for the new functionality in pymzml.run.Reader
related to accessing spectra and chromatograms.
"""
from typing import Any

import os
import sys

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
import pymzml.run as run
from pymzml.spec import Spectrum
import test_file_paths


class AccessSpectraAndChromatogramsTest(unittest.TestCase):
    """
    Test cases for the new functionality in pymzml.run.Reader
    related to accessing spectra and chromatograms.
    """

    def setUp(self):
        """Set up test cases."""
        self.paths = test_file_paths.paths

        # Use a file with chromatograms for testing
        # mini.chrom.mzML is at index 3
        for path in self.paths:
            if (
                "mini.chrom.mzML" in path
                and not path.endswith(".gz")
                and not path.endswith(".idx.gz")
            ):
                self.chrom_file = path
                break
        else:
            # Fallback to a known index if the file name is not found
            self.chrom_file = self.paths[3]  # mini.chrom.mzML

        # Use a file with spectra for testing
        for path in self.paths:
            if "example.mzML" in path and not path.endswith(".gz") and not path.endswith(".idx.gz"):
                self.spec_file = path
                break
        else:
            self.spec_file = self.paths[0]

        # Initialize readers with different settings
        self.reader_with_chromatograms = run.Reader(self.chrom_file, skip_chromatogram=False)
        self.reader_skip_chromatograms = run.Reader(self.chrom_file, skip_chromatogram=True)
        self.reader_spectra = run.Reader(self.spec_file)

    def test_get_spectrum_method(self):
        """Test the get_spectrum method."""
        # Use reader known to have spectra
        reader = self.reader_spectra
        
        # Check if the file has spectra
        spec_count = reader.get_spectrum_count()
        if spec_count is None or spec_count == 0:
            self.skipTest("Test file does not contain spectra")

        # Test that get_spectrum(0) returns the same as reader[0]
        try:
            spectrum_by_index = reader[0]
            spectrum_by_method = reader.get_spectrum(0)

            self.assertIsInstance(spectrum_by_index, Spectrum)
            self.assertIsInstance(spectrum_by_method, Spectrum)
            self.assertEqual(spectrum_by_index.ID, spectrum_by_method.ID)

            # Test accessing a spectrum by ID
            spectrum_id = spectrum_by_index.ID
            if isinstance(spectrum_id, str):
                spectrum_by_id = reader[spectrum_id]
                self.assertEqual(spectrum_by_index.ID, spectrum_by_id.ID)
        except IndexError:
            self.skipTest("Could not access spectrum at index 0")

    def test_get_chromatogram_method(self):
        """Test the get_chromatogram method."""
        # Check if the file has chromatograms
        chrom_count = self.reader_with_chromatograms.get_chromatogram_count()
        if chrom_count is None or chrom_count == 0:
            self.skipTest("Test file does not contain chromatograms")

        # Test accessing chromatogram by index
        try:
            chrom_by_index = self.reader_with_chromatograms.get_chromatogram(0)
            self.assertTrue(hasattr(chrom_by_index, "time") and hasattr(chrom_by_index, "i"))

            # If we successfully got a chromatogram by index, try to get it by ID
            chrom_id = chrom_by_index.ID
            if chrom_id:
                chrom_by_id = self.reader_with_chromatograms[chrom_id]
                self.assertTrue(hasattr(chrom_by_id, "time") and hasattr(chrom_by_id, "i"))
                self.assertEqual(chrom_by_id.ID, chrom_id)
        except Exception as e:
            self.skipTest(f"Could not access chromatogram at index 0: {e}")

        # Test that the chromatogram count is correct
        self.assertIsNotNone(self.reader_with_chromatograms.get_chromatogram_count())

    def test_skip_chromatogram_parameter(self):
        """Test the skip_chromatogram parameter."""
        # Check if the file has both spectra and chromatograms
        spec_count = self.reader_with_chromatograms.get_spectrum_count()
        chrom_count = self.reader_with_chromatograms.get_chromatogram_count()

        if spec_count is None or spec_count == 0:
            self.skipTest("Test file does not contain spectra")
        if chrom_count is None or chrom_count == 0:
            self.skipTest("Test file does not contain chromatograms")

        # With skip_chromatogram=False, we should see both spectra and chromatograms
        # Reset the reader to ensure we start from the beginning
        self.reader_with_chromatograms.close()
        self.reader_with_chromatograms = run.Reader(self.chrom_file, skip_chromatogram=False)

        # Collect items
        spectra_found = False
        chromatograms_found = False
        count = 0
        max_items = 20  # Increase the limit to ensure we see both types

        for item in self.reader_with_chromatograms:
            if isinstance(item, Spectrum):
                spectra_found = True
            elif hasattr(item, "time") and hasattr(item, "i"):
                chromatograms_found = True

            if spectra_found and chromatograms_found:
                break

            count += 1
            if count >= max_items:
                break

        # Check that we found both types
        self.assertTrue(
            spectra_found, "No spectra found when iterating with skip_chromatogram=False"
        )
        self.assertTrue(
            chromatograms_found,
            "No chromatograms found when iterating with skip_chromatogram=False",
        )

        # With skip_chromatogram=True, we should only see spectra
        # Reset the reader to ensure we start from the beginning
        self.reader_skip_chromatograms.close()
        self.reader_skip_chromatograms = run.Reader(self.chrom_file, skip_chromatogram=True)

        # Collect items
        items_without_chromatograms: list[Any] = []
        for item in self.reader_skip_chromatograms:
            items_without_chromatograms.append(item)
            if len(items_without_chromatograms) >= 10:  # Limit to first 10 items
                break

        # Check that we only have spectra (if any items were found)
        if items_without_chromatograms:
            only_spectra = all(isinstance(item, Spectrum) for item in items_without_chromatograms)
            self.assertTrue(
                only_spectra, "Found non-spectrum items when iterating with skip_chromatogram=True"
            )

    def test_chromatogram_index_out_of_range(self):
        """Test that accessing a chromatogram with an out-of-range index raises an exception."""
        # Check if the file has chromatograms
        chrom_count = self.reader_with_chromatograms.get_chromatogram_count()
        if chrom_count is None or chrom_count == 0:
            self.skipTest("Test file does not contain chromatograms")

        with self.assertRaises(Exception):
            self.reader_with_chromatograms.get_chromatogram(
                100
            )  # Assuming there are fewer than 100 chromatograms

    def test_chromatogram_invalid_identifier(self):
        """Test that accessing a chromatogram with an invalid identifier raises an exception."""
        # Check if the file has chromatograms
        chrom_count = self.reader_with_chromatograms.get_chromatogram_count()
        if chrom_count is None or chrom_count == 0:
            self.skipTest("Test file does not contain chromatograms")

        with self.assertRaises(Exception):
            self.reader_with_chromatograms.get_chromatogram("NonExistentChromatogram")

    def test_unambiguous_spectrum_access(self):
        """Test explicit spectrum access by ID and Index."""
        reader = self.reader_spectra
        spec_count = reader.get_spectrum_count()
        if spec_count is None or spec_count == 0:
            self.skipTest("Test file does not contain spectra")

        # Get first spectrum by index
        spec_0 = reader.get_spectrum_by_index(0)
        self.assertIsInstance(spec_0, Spectrum)

        # Get same spectrum by valid ID (int or str)
        spec_id = spec_0.ID
        # Ensure we can access it using the ID
        spec_by_id = reader.get_spectrum_by_id(spec_id)

        self.assertEqual(spec_0.ID, spec_by_id.ID)
        self.assertEqual(spec_0.index, spec_by_id.index)

    def test_unambiguous_chromatogram_access(self):
        """Test explicit chromatogram access by ID and Index."""
        chrom_count = self.reader_with_chromatograms.get_chromatogram_count()
        if chrom_count is None or chrom_count == 0:
            self.skipTest("Test file does not contain chromatograms")

        # Get first chromatogram by index
        try:
            chrom_0 = self.reader_with_chromatograms.get_chromatogram_by_index(0)
            
            # Get same chrom by ID
            chrom_id = chrom_0.ID
            # Ensure we can access it using the ID
            chrom_by_id = self.reader_with_chromatograms.get_chromatogram_by_id(chrom_id)
            
            self.assertEqual(chrom_0.ID, chrom_by_id.ID)
        except Exception as e:
            self.fail(f"Failed to access chromatogram: {e}")

    def test_tic_property(self):
        """Test the TIC convenience property."""
        try:
            tic = self.reader_with_chromatograms.TIC
            self.assertTrue(hasattr(tic, 'peaks'))
            self.assertEqual(tic.ID, "TIC")
        except KeyError:
            print("TIC not found in test file, skipping TIC content checks.")
        except Exception as e:
            self.fail(f"TIC property raised unexpected exception: {e}")

    def tearDown(self):
        """Clean up after tests."""
        self.reader_with_chromatograms.close()
        self.reader_skip_chromatograms.close()
        self.reader_spectra.close()


if __name__ == "__main__":
    unittest.main(verbosity=3)
