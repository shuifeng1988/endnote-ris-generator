from __future__ import annotations
import json
import pathlib
from typing import List, Optional, Dict, Any
from zr.utils import attachment_uri, ris_escape

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
    out_ris = out_dir / "out_ris"
    out_int = out_dir / "out_intermediate"
    out_ris.mkdir(parents=True, exist_ok=True)
    out_int.mkdir(parents=True, exist_ok=True)

    # Generate base name for output files
    if folder.is_file():
        # Single file record: use filename
        base_name = f"{folder.stem}_{record_id[:8]}"
    else:
        # Folder record: use folder name
        base_name = f"{folder.name}_{record_id[:8]}"

    # intermediate json
    intermediate = {
        "record_id": record_id,
        "folder": str(folder),
        "primary": str(primary) if primary else None,
        "primary_reason": primary_reason,
        "attachments": [str(p) for p in attachments],
        "meta": meta,
    }
    (out_int / f"{base_name}.json").write_text(
        json.dumps(intermediate, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # ris
    ris_text = to_ris_folder_record(meta, attachments, _record_title_fallback(folder, primary), primary_reason)
    (out_ris / f"{base_name}.ris").write_text(ris_text, encoding="utf-8")

def to_ris_folder_record(meta: Dict[str, Any], attachments: List[pathlib.Path], record_title: str, primary_reason: str) -> str:
    # record_type: if meta provides, map minimal; else GEN
    ty = meta.get("record_type") or "GEN"
    lines = [f"TY  - {ty}"]

    title = meta.get("title") or record_title
    if title:
        lines.append(f"TI  - {ris_escape(title)}")

    # authors one line
    authors = meta.get("authors") or []
    if authors:
        one_line = ", ".join([ris_escape(a) for a in authors if a])
        if one_line.strip():
            lines.append(f"AU  - {one_line}")

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

    # notes: include attachments list & primary reason
    note_parts = [f"EndNote folder={record_title}", f"primary_reason={primary_reason}"]
    if attachments:
        note_parts.append("attachments=" + "; ".join([attachment_uri(p) for p in attachments]))
    lines.append(f"N1  - {ris_escape(' | '.join(note_parts))}")

    # attachments: multiple L1 (primary first)
    for p in attachments:
        lines.append(f"L1  - {attachment_uri(p)}")

    lines.append("ER  -")
    return "\n".join(lines) + "\n"

