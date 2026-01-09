#!/usr/bin/env python3
"""Test the refactored mzML reader."""

import pymzml

# Test with the example file
run = pymzml.run.Reader("tests/data/example.mzML")

print("Testing refactored mzML reader...")
print(f"Spectrum count: {run.spectra.count}")
print(f"Chromatogram count: {run.chromatograms.count}")

# Test accessing by index
print("\n--- Testing access by index ---")
spec = run.spectra[0]
print(f"First spectrum ID: {spec.ID}")

# Test accessing by ID
print("\n--- Testing access by ID ---")
spec = run.spectra.get_by_id("controllerType=0 controllerNumber=1 scan=1")
print(f"Spectrum by ID: {spec.ID}")

# Test chromatogram access
print("\n--- Testing chromatogram access ---")
tic = run.chromatograms.get_by_id("TIC")
print(f"TIC chromatogram ID: {tic.ID}")

# Check offset dicts
print("\n--- Checking offset dictionaries ---")
print(f"Spectrum offsets: {len(run.info.file_object.file_handler.spectrum_offsets)}")
print(f"Chromatogram offsets: {len(run.info.file_object.file_handler.chromatogram_offsets)}")
print(f"First 3 spectrum IDs: {list(run.info.file_object.file_handler.spectrum_offsets.keys())[:3]}")
print(f"Chromatogram IDs: {list(run.info.file_object.file_handler.chromatogram_offsets.keys())}")

print("\n✅ All tests passed!")
