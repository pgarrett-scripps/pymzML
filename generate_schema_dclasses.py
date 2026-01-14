# generate_all_mzml_schemas.py
from pathlib import Path
import subprocess
import re
import sys

SCHEMAS_DIR = Path("schemas")
OUTPUT_DIR = Path("src/mzml/schemas")

def extract_version(filename: str) -> tuple[str, bool] | None:
    """
    Extract version number from schema filename.
    Returns (version, is_indexed) or None.
    """
    # Match patterns like mzML1.1.0.xsd or mzML1.1.0_idx.xsd
    match = re.search(r'mzML([\d.]+)(_idx)?\.xsd$', filename)
    if match:
        version = match.group(1)
        is_indexed = match.group(2) is not None
        return version, is_indexed
    return None

def version_to_package_name(version: str, indexed: bool = False) -> str:
    """Convert version to valid Python package name."""
    # 1.1.0 -> v1_1_0 or v1_1_0_idx
    base = f"v{version.replace('.', '_')}"
    return f"{base}_idx" if indexed else base

def find_schemas() -> dict[tuple[str, bool], Path]:
    """Find all schema files and extract versions."""
    schemas = {}
    
    for xsd_file in SCHEMAS_DIR.glob("*.xsd"):
        result = extract_version(xsd_file.name)
        if result:
            version, is_indexed = result
            schemas[(version, is_indexed)] = xsd_file
            idx_suffix = " (indexed)" if is_indexed else ""
            print(f"Found schema: {version}{idx_suffix} -> {xsd_file.name}")
    
    return schemas

def generate_schema(version: str, xsd_path: Path, indexed: bool = False) -> bool:
    """Generate dataclasses for a specific schema version."""
    pkg_name = version_to_package_name(version, indexed)
    package = f"mzml.schemas.{pkg_name}"
    
    idx_label = " (indexed)" if indexed else ""
    print(f"\nGenerating {version}{idx_label} ({pkg_name})...")
    
    try:
        # Use uv run to ensure xsdata is available
        result = subprocess.run(
            [
                "uv", "run",
                "xsdata", "generate",
                str(xsd_path),
                "--package", package,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✓ Generated {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate {version}{idx_label}")
        print(f"  Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Error: 'uv' command not found")
        print("  Please ensure uv is installed and in PATH")
        sys.exit(1)

def create_version_registry(schemas: dict[tuple[str, bool], Path]) -> None:
    """Create __init__.py with version registry."""
    output_init = OUTPUT_DIR / "__init__.py"
    
    # Separate regular and indexed schemas
    regular_versions = sorted(
        [v for (v, idx) in schemas.keys() if not idx],
        reverse=True
    )
    indexed_versions = sorted(
        [v for (v, idx) in schemas.keys() if idx],
        reverse=True
    )
    
    imports = []
    version_map_entries = []
    indexed_map_entries = []
    
    # Regular schemas
    for version in regular_versions:
        pkg_name = version_to_package_name(version, False)
        imports.append(
            f"from mzml.schemas.{pkg_name} import MzML as MzML_{pkg_name}"
        )
        version_map_entries.append(f'    "{version}": MzML_{pkg_name},')
    
    # Indexed schemas
    for version in indexed_versions:
        pkg_name = version_to_package_name(version, True)
        imports.append(
            f"from mzml.schemas.{pkg_name} import IndexedMzML as IndexedMzML_{pkg_name}"
        )
        indexed_map_entries.append(f'    "{version}": IndexedMzML_{pkg_name},')
    
    content = f'''"""Auto-generated schema version registry."""
from typing import Type
import xml.etree.ElementTree as ET
from xsdata.formats.dataclass.parsers import XmlParser

# Import all schema versions
{chr(10).join(imports)}

# Version registries
VERSION_MAP = {{
{chr(10).join(version_map_entries)}
}}

INDEXED_VERSION_MAP = {{
{chr(10).join(indexed_map_entries)}
}}

# Latest versions
LATEST_VERSION = "{regular_versions[0]}" if regular_versions else None
LATEST_MZML = MzML_{version_to_package_name(regular_versions[0], False)} if regular_versions else None

def detect_mzml_version(file_path: str) -> tuple[str | None, bool]:
    """
    Detect mzML schema version and whether it's indexed.
    
    Returns:
        (version, is_indexed) tuple
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check if indexed
        is_indexed = root.tag.endswith("indexedmzML")
        
        # Get version from mzML element
        if is_indexed:
            # Find nested mzML element
            mzml_elem = root.find(".//*[@version]")
            version = mzml_elem.attrib.get("version") if mzml_elem else None
        else:
            version = root.attrib.get("version")
        
        return version, is_indexed
    except Exception:
        return None, False

def get_mzml_class(version: str, indexed: bool = False) -> Type:
    """Get MzML class for specific version."""
    version_map = INDEXED_VERSION_MAP if indexed else VERSION_MAP
    
    if version not in version_map:
        available = ', '.join(version_map.keys())
        idx_str = "indexed " if indexed else ""
        raise ValueError(
            f"Unsupported {{idx_str}}mzML version: {{version}}. "
            f"Supported versions: {{available}}"
        )
    return version_map[version]

def parse_mzml(file_path: str, version: str | None = None, indexed: bool | None = None):
    """
    Parse mzML file with auto-detection or explicit version.
    
    Args:
        file_path: Path to mzML file
        version: Optional version string. If None, auto-detect from file.
        indexed: Optional indexed flag. If None, auto-detect from file.
    
    Returns:
        Parsed MzML or IndexedMzML object
    
    Examples:
        >>> # Auto-detect version and type
        >>> mzml = parse_mzml("data.mzML")
        >>> 
        >>> # Explicit version
        >>> mzml = parse_mzml("data.mzML", version="1.1.0")
        >>>
        >>> # Explicit indexed file
        >>> mzml = parse_mzml("data.mzML", version="1.1.0", indexed=True)
    """
    if version is None or indexed is None:
        detected_version, detected_indexed = detect_mzml_version(file_path)
        if version is None:
            version = detected_version
        if indexed is None:
            indexed = detected_indexed
    
    if not version:
        raise ValueError("Could not detect mzML version from file")
    
    mzml_class = get_mzml_class(version, indexed)
    parser = XmlParser()
    return parser.parse(file_path, mzml_class)

__all__ = [
    "VERSION_MAP",
    "INDEXED_VERSION_MAP",
    "LATEST_VERSION",
    "LATEST_MZML",
    "detect_mzml_version",
    "get_mzml_class",
    "parse_mzml",
{chr(10).join(f'    "MzML_{version_to_package_name(v, False)}",' for v in regular_versions)}
{chr(10).join(f'    "IndexedMzML_{version_to_package_name(v, True)}",' for v in indexed_versions)}
]
'''
    
    output_init.parent.mkdir(parents=True, exist_ok=True)
    output_init.write_text(content)
    print(f"\n✓ Created version registry: {output_init}")

def main():
    """Generate dataclasses for all mzML schemas."""
    print("=" * 60)
    print("mzML Schema Dataclass Generator")
    print("=" * 60)
    
    # Find all schemas
    schemas = find_schemas()
    
    regular_count = sum(1 for (_, idx) in schemas.keys() if not idx)
    indexed_count = sum(1 for (_, idx) in schemas.keys() if idx)
    
    print(f"\nFound {len(schemas)} schemas:")
    print(f"  - Regular: {regular_count}")
    print(f"  - Indexed: {indexed_count}")
    
    if not schemas:
        print("No schemas found!")
        return
    
    # Generate each schema
    print("\n" + "=" * 60)
    print("Generating dataclasses...")
    print("=" * 60)
    
    success_count = 0
    failed = []
    
    for (version, indexed), xsd_path in sorted(schemas.items()):
        if generate_schema(version, xsd_path, indexed):
            success_count += 1
        else:
            idx_label = " (indexed)" if indexed else ""
            failed.append(f"{version}{idx_label}")
    
    # Create version registry
    if success_count > 0:
        print("\n" + "=" * 60)
        print("Creating version registry...")
        print("=" * 60)
        create_version_registry(schemas)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Successfully generated: {success_count}/{len(schemas)}")
    
    if failed:
        print(f"✗ Failed: {len(failed)}")
        for version in failed:
            print(f"  - {version}")
    
    print("\nGenerated schemas are in: src/mzml/schemas/")
    print("\nUsage:")
    print("  from mzml.schemas import parse_mzml")
    print('  mzml = parse_mzml("file.mzML")  # Auto-detects version and type')
    print('  mzml = parse_mzml("indexed.mzML")  # Works with indexed files too')

if __name__ == "__main__":
    main()