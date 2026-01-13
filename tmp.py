import pymzml as pmz
import sys
import logging

# set to debug level to see detailed decoding logs
logging.basicConfig(level=logging.DEBUG)


reader = pmz.Reader("tests/data/example.mzML", build_index_from_scratch=True)
print(reader.TIC)
print(reader.TIC.profile)
print(reader.TIC.time)
print(reader.TIC.i)

sys.exit(0)


print("Reading mzML file using pymzml...")

#reader = pmz.Reader("/home/patrick-garrett/Data/Natalie/Histones2/raw/argc/20250806_ArgC_DDA_HCD-FT_01.mzML.gz")
reader = pmz.Reader("tests/data/example.mzML")
for i, spectrum in enumerate(reader.spectra):
    
    if spectrum.ms_level != 1:
        continue

    print(f"[{i}] Spectrum ID: {spectrum.ID}, MS Level: {spectrum.ms_level}, Number of Peaks: {len(spectrum.peaks())}")
    # TIC
    print(f"    TIC: {spectrum.TIC}")
    print(f"    ID: {spectrum.ID}")
    print(f"    controller_type: {spectrum.controller_type}")
    print(f"    controller_number: {spectrum.controller_number}")
    print(f"    scan: {spectrum.scan}")
    print(f"    index: {spectrum.index}")
    print(f"    ms_level: {spectrum.ms_level}")
    print(f"    scan_unit: {spectrum.scan_unit}")
    print(f"    scan_time: {spectrum.scan_time}")
    print(f"    selected_precursors: {spectrum.selected_precursors}")
    print(f"    accessions: {spectrum.accessions}")
    print(f"    get_element_by_accession: {str(spectrum.get_element_by_accession('MS:1000504'))}")
    print(f"    ns: {spectrum.ns}")
    print(f"    sampled_noise_baseline: {spectrum.sampled_noise_baseline}")

reader.spectra[9]  # Access by index


sys.exit(0)

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




reader = pmz.Reader("tests/data/mini.chrom.mzML")
for i, chromatogram in enumerate(reader.chromatograms):
    
    if not isinstance(chromatogram, pmz.Chromatogram):
        raise ValueError(f"Parsed object is not a pymzml Chromatogram, got {type(chromatogram)}")


    print(f"[{i}] Chromatogram ID: {chromatogram.ID}, Number of Peaks: {len(chromatogram.profile)}")

reader.chromatograms[0]  # Access by index
