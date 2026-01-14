from mzml.schemas import parse_mzml

# Auto-detect version and parse
mzml = parse_mzml("tests/data/example.mzML")

# Access data with full typing
print(f"Version: {mzml.version}")
print(f"ID: {mzml.id}")
print(f"Software count: {mzml.software_list.count}")

# Iterate through software
for software in mzml.software_list.software:
    print(f"Software: {software.id} v{software.version}")
    for param in software.cv_param:
        print(f"  - {param.name}: {param.value}")

# Access spectra
if mzml.run and mzml.run.spectrum_list:
    print(f"Total spectra: {mzml.run.spectrum_list.count}")
    
    # Iterate through spectra (if you want)
    for spectrum in mzml.run.spectrum_list.spectrum:
        print(f"Spectrum {spectrum.index}: {spectrum.id}")