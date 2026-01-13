# PyMZML

This fork is a major refactor of pymzml. Most functionality is preserved so it should serve as a drop in replacement for the most part.

- Removed all depriciated code
- Added strict type annoations
- UV backend
- Makefile
- strict numpy dependancy
  - allows for faster centroiding
- Python 3.11 style code (StrEnum, Match / Case ...)
- Ddatalasses used where applicable (most notable replacing the info dictionary)
- Improved readability / maintanability
- Namespace support (import pymzml as pmz)
- Removed plotting functionality 
- docs & examples added to README

## General information

This a fork of [pymzml](https://github.com/pymzml/pymzML) (a package to parse mzML data in Python based on cElementTree)

pymzml Copyright 2010-2024 by:

- M. Kösters,
- J. Leufken,
- T. Bald,
- A. Niehues,
- S. Schulze,
- K. Sugimoto,
- R.P. Zahedi,
- M. Hippler,
- S.A. Leidel,
- C. Fufezan,

## Quick Start Tutorial

### Installation

```bash
pip install pymzml-turbo
```

### Basic Usage

Import the package:

```python
import pymzml as pmz
```

### Reading mzML Files

```python
# Open an mzML file
# skip_chromatogram = True by default
run = pmz.Reader("data.mzML")

# Access run information
print(f"File: {run.info.file_name}")
print(f"Spectra count: {run.info.spectrum_count}")
print(f"Start time: {run.info.start_time}")
```

### Iterating Through Spectra

```python
# Iterate through all spectra
for spectrum in run.spectra:
    print(f"Spectrum {spectrum.ID}, MS level {spectrum.ms_level}")
    print(f"Retention time: {spectrum.scan_time_in_minutes():.2f} min")
    print(f"Number of peaks: {len(spectrum.peaks('raw'))}")
```

### Accessing Specific Spectra

Accessing spectra via `run.spectra[identifier]` interprets integers first as Native IDs, then as indices. This can be ambiguous if a spectrum has Native ID "5" but you want the 6th spectrum (index 5).

For unambiguous access, use the specific methods:

```python
# Unambiguous access by Native ID (str or int)
spectrum = run.spectra.get_by_id("spectrum_id_1")
spectrum = run.spectra.get_by_id(100)

# Unambiguous access by 0-based Index
spectrum = run.spectra.get_by_index(0)  # First spectrum
```

### Working with Peaks

```python
# Get peaks from a spectrum
peaks = spectrum.peaks('centroided')  # Returns list of (mz, intensity) tuples

# Access m/z and intensity arrays separately
mz_array = spectrum.mz
intensity_array = spectrum.i

# Find specific peaks
target_mz = 820.77
found_peaks = spectrum.has_peak(target_mz)
if found_peaks:
    for mz, intensity in found_peaks:
        print(f"Found peak at m/z {mz:.4f} with intensity {intensity:.2f}")

# Get highest intensity peaks
top_peaks = spectrum.highest_peaks(5)  # Top 5 peaks
for mz, intensity in top_peaks:
    print(f"m/z: {mz:.4f}, intensity: {intensity:.2f}")
```

### Working with Chromatograms

```python
# Access TIC (Total Ion Chromatogram)
tic = run.TIC
print(f"TIC has {len(tic.peaks())} data points")

# Get chromatogram data
for time, intensity in tic.peaks():
    print(f"Time: {time:.2f}, Intensity: {intensity:.2f}")

# Access by index (explicitly 0-based index)
chromatogram = run.chromatograms.get_by_index(0)
```

### Extracting Ion Chromatograms (XIC/EIC)

```python
# Extract intensities for a specific m/z across time
target_mz = 445.12
time_intensities = []

for spectrum in run.spectra:
    if spectrum.ms_level == 1:
        peaks = spectrum.has_peak(target_mz)
        if peaks:
            for mz, intensity in peaks:
                time_intensities.append(
                    (spectrum.scan_time_in_minutes(), intensity, mz)
                )

# Print results
for rt, intensity, mz in time_intensities:
    print(f"RT: {rt:.3f} min, Intensity: {intensity:.2e}, m/z: {mz:.5f}")
```

### Working with Precursors (MS2)

```python
# Access precursor information from MS2 spectra
for spectrum in run:
    if spectrum.ms_level == 2:
        precursors = spectrum.selected_precursors
        if precurso.spectra:
    if spectrum.ms_level == 2:
        precursors = spectrum.selected_precursors
        if precursors:
            for precursor in precursors:
                print(f"Precursor m/z: {precursor['mz']:.4f}")
                print(f"Precursor intensity: {precursor.get('i', 'N/A')}")
                print(f"Charge state: {precursor.get('charge', 'N/A')}")
```

### Spectrum Comparison

```python
# Compare two spectra using cosine similarity
spectra = []
for spectrum in run.spectratra) >= 2:
            break

# Calculate similarity (returns value between 0 and 1)
similarity = spectra[0].similarity_to(spectra[1])
print(f"Cosine similarity: {similarity:.4f}")

# Perfect match with itself
self_similarity = spectra[0].similarity_to(spectra[0])
print(f"Self-similarity: {self_similarity:.4f}")  # Should be 1.0
```

### Advanced: Custom Precision

```python
# Define different mass precisions for MS1 and MS2
run = pmz.Reader(
    "data.mzML",
    MS_precisions={
        1: 5e-6,  # 5 ppm for MS1
        2: 5e-4   # 500 ppm for MS2
    }
)

# This affects peak matching functions like has_peak()
```

### Working with Compressed Files

```python
# pymzml-turbo automatically handles gzipped files
run = pmz.Reader("data.mzML.gz")

# Works exactly the same as uncompressed files
for spectrum in run:
    print(spectrum.ID)
```
.spectra:
    print(spectrum.ID)
```

### Complete Example

```python
import pymzml as pmz

# Open file
run = pmz.Reader("data.mzML")

# Print file summary
print(f"File: {run.info.file_name}")
print(f"Total spectra: {run.info.spectrum_count}")
print()

# Analyze MS1 spectra
ms1_count = 0
total_peaks = 0

for spectrum in run.spectra:
    if spectrum.ms_level == 1:
        ms1_count += 1
        peaks = spectrum.peaks('centroided')
        total_peaks += len(peaks)
        
        # Get base peak (highest intensity)
        if peaks:
            base_peak = max(peaks, key=lambda x: x[1])
            print(f"Spectrum {spectrum.ID}:")
            print(f"  RT: {spectrum.scan_time_in_minutes():.2f} min")
            print(f"  Base peak: m/z {base_peak[0]:.4f}, intensity {base_peak[1]:.2e}")

print(f"\nTotal MS1 spectra: {ms1_count}")
print(f"Average peaks per MS1: {total_peaks / ms1_count:.1f}")
```

### Context Manager

```python
# Context manager ensures proper cleanup
with pmz.Reader("data.mzML") as run:
    for spectrum in run.spectra

