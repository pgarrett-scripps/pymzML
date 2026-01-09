import pymzml as pmz
import sys


reader = pmz.Reader("tests/data/mini.chrom.mzML")
for i, chromatogram in enumerate(reader.chromatograms):
    
    if not isinstance(chromatogram, pmz.Chromatogram):
        raise ValueError(f"Parsed object is not a pymzml Chromatogram, got {type(chromatogram)}")


    print(f"[{i}] Chromatogram ID: {chromatogram.ID}, Number of Peaks: {len(chromatogram.peaks())}")

reader.chromatograms[0]  # Access by index

sys.exit(0)


print("Reading mzML file using pymzml...")

reader = pmz.Reader("tests/data/example.mzML")
for i, spectrum in enumerate(reader.spectra):
    
    if not isinstance(spectrum, pmz.Spectrum):
        raise ValueError(f"Parsed object is not a pymzml Spectrum, got {type(spectrum)}")

    if spectrum.ms_level != 1:
        continue

    print(f"[{i}] Spectrum ID: {spectrum.ID}, MS Level: {spectrum.ms_level}, Number of Peaks: {len(spectrum.peaks())}")

reader.spectra[9]  # Access by index


#sys.exit(0)

print("\n--- Testing indexed gzip mzML file ---\n")

reader = pmz.Reader("tests/data/example.mzML.gz")
for spectrum in reader.spectra:
    
    if not isinstance(spectrum, pmz.Spectrum):
        raise ValueError("Parsed object is not a pymzml Spectrum")

    if spectrum.ms_level != 1:
        continue

    print(f"Spectrum ID: {spectrum.ID}, MS Level: {spectrum.ms_level}, Number of Peaks: {len(spectrum.peaks())}")

reader.spectra[9]  # Access by index

print("\nTesting indexed gzip mzML file...\n")

reader = pmz.Reader("tests/data/example.mzML.idx.gz")
for spectrum in reader.spectra:
    
    if not isinstance(spectrum, pmz.Spectrum):
        raise ValueError("Parsed object is not a pymzml Spectrum")

    if spectrum.ms_level != 1:
        continue

    print(f"Spectrum ID: {spectrum.ID}, MS Level: {spectrum.ms_level}, Number of Peaks: {len(spectrum.peaks())}")

reader.spectra[9]  # Access by index


