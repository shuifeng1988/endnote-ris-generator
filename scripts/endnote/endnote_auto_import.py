#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EndNote Auto Import Script

Automatically imports classified RIS files into EndNote and creates custom groups.
Uses Windows COM interface to control EndNote.

Requirements:
- Windows OS
- EndNote installed
- pywin32 package (pip install pywin32)

Usage:
    python endnote_auto_import.py <ris_directory> [--library <path_to_enl>]

Example:
    python endnote_auto_import.py ./output/out_ris_class
    python endnote_auto_import.py ./output/out_ris_class --library "C:/My Documents/MyLibrary.enl"
"""

import argparse
import pathlib
import json
import sys
import time

try:
    import win32com.client
except ImportError:
    print("ERROR: pywin32 is not installed.")
    print("Please install it with: pip install pywin32")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Automatically import classified RIS files into EndNote with groups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "ris_dir",
        type=str,
        help="Directory containing classified RIS files (e.g., ./output/out_ris_class)"
    )
    parser.add_argument(
        "--library",
        type=str,
        default=None,
        help="Path to EndNote library (.enl file). If not specified, uses the currently open library."
    )
    parser.add_argument(
        "--create_smart_groups",
        action="store_true",
        help="Create Smart Groups instead of Custom Groups (requires EndNote X9+)"
    )
    return parser.parse_args()


def connect_to_endnote():
    """
    Connect to EndNote via COM interface.

    Returns:
        EndNote application object, or None if failed
    """
    print("Connecting to EndNote...")
    try:
        endnote = win32com.client.Dispatch("EndNote.Application")
        print(f"✓ Connected to EndNote (Version: {endnote.Version})")
        return endnote
    except Exception as e:
        print(f"✗ Failed to connect to EndNote: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure EndNote is installed")
        print("2. Try opening EndNote manually first")
        print("3. Check if EndNote is registered in Windows COM")
        return None


def open_or_get_library(endnote, library_path=None):
    """
    Open specified library or get currently open library.

    Args:
        endnote: EndNote application object
        library_path: Path to .enl file, or None to use current library

    Returns:
        Library object, or None if failed
    """
    try:
        if library_path:
            print(f"Opening library: {library_path}")
            library = endnote.OpenLibrary(library_path)
        else:
            print("Using currently open library...")
            # Get the first open library
            if endnote.Libraries.Count > 0:
                library = endnote.Libraries.Item(1)
            else:
                print("✗ No library is currently open")
                print("Please open a library in EndNote or specify --library path")
                return None

        print(f"✓ Library: {library.Name}")
        print(f"  Records: {library.GetRecords().Count}")
        return library
    except Exception as e:
        print(f"✗ Failed to open library: {e}")
        return None


def load_classification_report(ris_dir):
    """
    Load classification report to get category information.

    Args:
        ris_dir: Directory containing RIS files

    Returns:
        Dict with classification info, or None if not found
    """
    report_path = pathlib.Path(ris_dir) / "classification_report.json"

    if not report_path.exists():
        print(f"⚠ Classification report not found: {report_path}")
        print("  Will scan directory for RIS files instead")
        return None

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        print(f"✓ Loaded classification report")
        print(f"  Categories: {report['num_categories']}")
        print(f"  Total documents: {report['total_documents']}")
        return report
    except Exception as e:
        print(f"⚠ Failed to load classification report: {e}")
        return None


def get_ris_files(ris_dir):
    """
    Get all RIS files in directory.

    Args:
        ris_dir: Directory containing RIS files

    Returns:
        List of (category_name, ris_file_path) tuples
    """
    ris_path = pathlib.Path(ris_dir)
    ris_files = []

    for ris_file in ris_path.glob("*.ris"):
        category_name = ris_file.stem  # Filename without extension
        ris_files.append((category_name, str(ris_file.resolve())))

    return sorted(ris_files)


def import_ris_file(library, ris_file_path, category_name):
    """
    Import a RIS file into EndNote library.

    Args:
        library: EndNote library object
        ris_file_path: Path to RIS file
        category_name: Category name for progress display

    Returns:
        Number of records imported, or -1 if failed
    """
    print(f"\n  Importing: {category_name}")
    print(f"    File: {ris_file_path}")

    try:
        # Get record count before import
        before_count = library.GetRecords().Count

        # Import RIS file
        # ImportFile(filename, filter_name, import_option)
        # filter_name: "RefMan (RIS)" for RIS files
        # import_option: 0 = Import, 1 = Import into new library
        library.ImportFile(ris_file_path, "RefMan (RIS)", 0)

        # Wait a bit for import to complete
        time.sleep(0.5)

        # Get record count after import
        after_count = library.GetRecords().Count
        imported_count = after_count - before_count

        print(f"    ✓ Imported {imported_count} records")
        return imported_count

    except Exception as e:
        print(f"    ✗ Import failed: {e}")
        return -1


def create_custom_group(library, group_name, category_keyword):
    """
    Create a Custom Group and add matching references.

    Args:
        library: EndNote library object
        group_name: Name for the group
        category_keyword: Keyword to search for (e.g., "Category: Genomics")

    Returns:
        True if successful, False otherwise
    """
    print(f"\n  Creating group: {group_name}")

    try:
        # Search for references with the category keyword
        # Search(field_name, search_term, match_option, case_sensitive)
        # field_name: "Keywords" for keyword field
        # match_option: 0 = Contains, 1 = Is, 2 = Starts with
        search_results = library.Search(f"Keywords Contains {category_keyword}")

        if search_results.Count == 0:
            print(f"    ⚠ No references found with keyword: {category_keyword}")
            return False

        print(f"    Found {search_results.Count} references")

        # Create custom group
        group_set = library.CustomGroups
        new_group = group_set.Add(group_name)

        # Add references to group
        for i in range(1, search_results.Count + 1):
            ref = search_results.Item(i)
            new_group.AddReference(ref)

        print(f"    ✓ Created group with {search_results.Count} references")
        return True

    except Exception as e:
        print(f"    ✗ Failed to create group: {e}")
        return False


def main():
    args = parse_args()

    print("=" * 80)
    print("EndNote Auto Import Script")
    print("=" * 80)

    # Validate RIS directory
    ris_dir = pathlib.Path(args.ris_dir)
    if not ris_dir.exists():
        print(f"✗ Directory not found: {ris_dir}")
        return 1

    # Connect to EndNote
    endnote = connect_to_endnote()
    if not endnote:
        return 1

    # Open or get library
    library = open_or_get_library(endnote, args.library)
    if not library:
        return 1

    # Load classification report (optional)
    report = load_classification_report(ris_dir)

    # Get RIS files
    ris_files = get_ris_files(ris_dir)
    if not ris_files:
        print(f"✗ No RIS files found in: {ris_dir}")
        return 1

    print(f"\n✓ Found {len(ris_files)} RIS files to import")

    # Ask for confirmation
    print("\n" + "=" * 80)
    print("READY TO IMPORT")
    print("=" * 80)
    print(f"Library: {library.Name}")
    print(f"Files to import: {len(ris_files)}")
    print("\nCategories:")
    for i, (cat_name, _) in enumerate(ris_files, 1):
        print(f"  {i}. {cat_name}")

    response = input("\nProceed with import? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Import cancelled.")
        return 0

    # Import RIS files and create groups
    print("\n" + "=" * 80)
    print("IMPORTING FILES")
    print("=" * 80)

    total_imported = 0
    successful_groups = 0

    for category_name, ris_file_path in ris_files:
        # Import RIS file
        imported_count = import_ris_file(library, ris_file_path, category_name)

        if imported_count > 0:
            total_imported += imported_count

            # Create custom group
            category_keyword = f"Category: {category_name}"
            if create_custom_group(library, category_name, category_keyword):
                successful_groups += 1

    # Summary
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"✓ Total records imported: {total_imported}")
    print(f"✓ Groups created: {successful_groups}/{len(ris_files)}")
    print(f"\nLibrary: {library.Name}")
    print(f"Total records in library: {library.GetRecords().Count}")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Check your EndNote library - all references should be imported")
    print("2. Check 'Custom Groups' in the left panel - groups should be created")
    print("3. You can now organize, edit, and cite your references")
    print("\nNote: If some groups are empty, check the Keywords field in those references")
    print("      to ensure they have the correct 'Category: XXX' keyword.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
