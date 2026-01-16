from __future__ import annotations
import pathlib
from typing import List, Union

# Supported file extensions for direct file records
SUPPORTED_FILE_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md", ".xls", ".xlsx"}


def scan_record_folders(root_dir: pathlib.Path, recursive: bool, include_root_files: bool = True) -> List[pathlib.Path]:
    """
    Scan for record folders and optionally root-level files.

    Args:
        root_dir: Root directory to scan
        recursive: If True, scan recursively
        include_root_files: If True, also treat root-level files as individual records

    Returns:
        List of paths (directories or files) representing records
    """
    records = []

    if recursive:
        # Recursive mode: collect all directories containing files
        dirs = set()
        for p in root_dir.rglob("*"):
            if p.is_file():
                dirs.add(p.parent)
        records.extend([d for d in dirs if d.is_dir()])
    else:
        # Non-recursive mode: only immediate subdirectories
        records.extend([d for d in root_dir.iterdir() if d.is_dir()])

    # Add root-level files as individual records
    if include_root_files:
        root_files = [
            f for f in root_dir.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_FILE_EXTS
        ]
        records.extend(root_files)

    return sorted(records)


def is_file_record(path: pathlib.Path) -> bool:
    """Check if a path represents a single-file record (not a folder)."""
    return path.is_file()

