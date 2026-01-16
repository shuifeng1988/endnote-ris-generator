"""
EndNote RIS export module with relative paths
Modified from zr.ris_export to use relative paths for EndNote compatibility
"""
from __future__ import annotations
import json
import pathlib
import shutil
from typing import List, Optional, Dict, Any


def ris_escape(s: str) -> str:
    """Escape special characters in RIS fields"""
    return " ".join(str(s).replace("\n", " ").split()).strip()


def _record_title_fallback(folder: pathlib.Path, primary: Optional[pathlib.Path]) -> str:
    """
    Generate fallback title for record.

    For single-file records: use filename
    For folder records: use primary filename or folder name
    """
    if folder.is_file():
        # Single file record: use filename as title
        return folder.stem.replace("_", " ").replace("-", " ").strip()

    # Folder record
    if primary:
        return primary.stem.replace("_", " ").replace("-", " ").strip()
    return f"Untitled ({folder.name})"


def copy_attachments_to_pdf_dir(attachments: List[pathlib.Path],
                                 pdf_dir: pathlib.Path,
                                 folder: pathlib.Path) -> List[pathlib.Path]:
    """
    Copy attachments to pdf directory and return absolute paths

    Args:
        attachments: List of attachment file paths
        pdf_dir: Output pdf directory
        folder: Source folder (for generating unique names)

    Returns:
        List of absolute paths to copied files
    """
    copied_paths = []

    for attachment in attachments:
        if not attachment.exists():
            continue

        # Generate unique filename
        # Use folder name + original filename to avoid conflicts
        if folder.is_file():
            # Single file record
            dest_name = attachment.name
        else:
            # Folder record: prefix with folder name
            dest_name = f"{folder.name}_{attachment.name}"

        dest_path = pdf_dir / dest_name

        # Handle duplicates
        counter = 1
        while dest_path.exists():
            stem = attachment.stem
            suffix = attachment.suffix
            if folder.is_file():
                dest_name = f"{stem}_{counter}{suffix}"
            else:
                dest_name = f"{folder.name}_{stem}_{counter}{suffix}"
            dest_path = pdf_dir / dest_name
            counter += 1

        # Copy file
        try:
            shutil.copy2(attachment, dest_path)
            # Return absolute path
            copied_paths.append(dest_path.resolve())
        except Exception as e:
            print(f"Warning: Failed to copy {attachment}: {e}")

    return copied_paths


def write_record_outputs(
    out_dir: pathlib.Path,
    folder: pathlib.Path,
    record_id: str,
    primary: Optional[pathlib.Path],
    primary_reason: str,
    attachments: List[pathlib.Path],
    meta: Dict[str, Any],
    log,
):
    """
    Write RIS and intermediate JSON for a record
    Modified to use relative paths for EndNote compatibility
    """
    out_ris = out_dir / "out_ris"
    out_int = out_dir / "out_intermediate"
    pdf_dir = out_dir / "pdf"

    out_ris.mkdir(parents=True, exist_ok=True)
    out_int.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Generate base name for output files
    if folder.is_file():
        # Single file record: use filename
        base_name = f"{folder.stem}_{record_id[:8]}"
    else:
        # Folder record: use folder name
        base_name = f"{folder.name}_{record_id[:8]}"

    # Copy attachments to pdf directory and get absolute paths
    attachment_abs_paths = copy_attachments_to_pdf_dir(attachments, pdf_dir, folder)

    # intermediate json
    intermediate = {
        "record_id": record_id,
        "folder": str(folder),
        "primary": str(primary) if primary else None,
        "primary_reason": primary_reason,
        "attachments": [str(p) for p in attachments],
        "attachment_absolute_paths": [str(p) for p in attachment_abs_paths],
        "meta": meta,
    }
    (out_int / f"{base_name}.json").write_text(
        json.dumps(intermediate, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # ris with absolute paths
    ris_text = to_ris_folder_record(
        meta,
        attachment_abs_paths,
        _record_title_fallback(folder, primary),
        primary_reason
    )
    (out_ris / f"{base_name}.ris").write_text(ris_text, encoding="utf-8")


def to_ris_folder_record(meta: Dict[str, Any],
                         attachment_paths: List[pathlib.Path],
                         record_title: str,
                         primary_reason: str,
                         category: Optional[str] = None) -> str:
    """
    Generate RIS format with absolute file paths for EndNote

    Args:
        meta: Metadata dictionary
        attachment_paths: List of absolute paths to attachment files
        record_title: Fallback title
        primary_reason: Reason for primary file selection
        category: Optional category name to add as keyword for EndNote grouping

    Returns:
        RIS format string
    """
    # record_type: if meta provides, map minimal; else GEN
    ty = meta.get("record_type") or "GEN"
    lines = [f"TY  - {ty}"]

    title = meta.get("title") or record_title
    if title:
        lines.append(f"TI  - {ris_escape(title)}")

    # authors: EndNote supports multiple AU lines (one per author)
    authors = meta.get("authors") or []
    if authors:
        for author in authors:
            if author:
                lines.append(f"AU  - {ris_escape(author)}")

    if meta.get("year"):
        lines.append(f"PY  - {meta['year']}")
    if meta.get("journal"):
        lines.append(f"JO  - {ris_escape(meta['journal'])}")
    if meta.get("volume"):
        lines.append(f"VL  - {ris_escape(meta['volume'])}")
    if meta.get("issue"):
        lines.append(f"IS  - {ris_escape(meta['issue'])}")
    if meta.get("pages"):
        lines.append(f"SP  - {ris_escape(meta['pages'])}")
    if meta.get("doi"):
        lines.append(f"DO  - {ris_escape(meta['doi'])}")
    if meta.get("url"):
        lines.append(f"UR  - {ris_escape(meta['url'])}")

    # abstract -> N2 (common)
    if meta.get("abstract"):
        lines.append(f"N2  - {ris_escape(meta['abstract'])}")

    # keywords: add category as keyword for EndNote Smart Groups
    # KW field can have multiple entries (one per keyword)
    existing_keywords = meta.get("keywords", [])
    if isinstance(existing_keywords, str):
        existing_keywords = [kw.strip() for kw in existing_keywords.split(";") if kw.strip()]

    # Add existing keywords
    for kw in existing_keywords:
        if kw:
            lines.append(f"KW  - {ris_escape(kw)}")

    # Add category as keyword (with prefix for easy identification)
    if category:
        lines.append(f"KW  - Category: {ris_escape(category)}")

    # notes: include primary reason only (don't mention attachments to avoid confusion)
    lines.append(f"N1  - Primary: {ris_escape(primary_reason)}")

    # attachments: use L1 field with file:// protocol for local files
    # EndNote recognizes file:// URLs for local attachments
    for abs_path in attachment_paths:
        # Convert Windows path to file:// URL
        # Example: C:\path\file.pdf -> file:///C:/path/file.pdf
        path_str = str(abs_path).replace("\\", "/")
        file_url = f"file:///{path_str}"
        lines.append(f"L1  - {file_url}")

    lines.append("ER  -")
    return "\n".join(lines) + "\n"
