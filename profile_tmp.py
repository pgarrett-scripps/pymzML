import cProfile
import pstats
import pymzml as pmz
import sys

def main():
    print("Reading mzML file using pymzml...")

    reader = pmz.Reader("/home/patrick-garrett/Data/Natalie/Histones2/raw/argc/20250806_ArgC_DDA_HCD-FT_01.mzML.gz")
    for i, spectrum in enumerate(reader.spectra):
        
        if spectrum.ms_level != 1:
            continue

        print(f"[{i}] Spectrum ID: {spectrum.ID}, MS Level: {spectrum.ms_level}, Number of Peaks: {len(cpeaks) if (cpeaks := spectrum.peaks()) is not None else 0}")
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


if __name__ == "__main__":
    with cProfile.Profile() as pr:
        main()
    
    stats = pstats.Stats(pr)
    stats.strip_dirs()
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(20) # Print top 20 lines
