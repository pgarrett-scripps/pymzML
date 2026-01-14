from pymzml.versions.parser import parse_mzml, detect_mzml_version, MzMLVersion
import os

path = "tests/data/example.mzML"
abs_path = os.path.abspath(path)
print(f"Parsing {path}...")

# Test detect_mzml_version first
print("\nTesting version detection:")
ver = detect_mzml_version(abs_path)
print(f"Detected version enum: {ver}")

if ver:
    print(f"  Is Indexed: {ver.is_indexed}")
    print(f"  Version XYZ: {ver.version_xyz}")
    print(f"  Module Name: {ver.module_name}")
    print(f"  Class Name: {ver.class_name}")

if ver is None:
    print("Failed to detect version!")
    exit(1)

# Test parse_mzml
try:
    obj = parse_mzml(abs_path)
    print(f"\nSuccessfully parsed object of type: {type(obj).__name__}")
    
    # Check if we can access some data
    if hasattr(obj, 'mz_ml'):
        print(f"MzML ID: {obj.mz_ml.id}")
        print(f"MzML Version: {obj.mz_ml.version}")
    elif hasattr(obj, 'id'): # If it parsed straight to MzML
         print(f"MzML ID: {obj.id}")
         print(f"MzML Version: {obj.version}")
    
except Exception as e:
    print(f"Parsing failed: {e}")
    raise

