from __future__ import annotations
import hashlib
import pathlib
import os
from urllib.parse import quote

def folder_id(folder: pathlib.Path) -> str:
    """
    Generate unique ID for a record (folder or single file).

    For folders: hash based on folder path + all file metadata
    For single files: hash based on file path + file metadata
    """
    if folder.is_file():
        # Single file record
        st = folder.stat()
        key = f"{folder.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    else:
        # Folder record
        items = []
        for p in sorted(folder.glob("*")):
            if p.is_file():
                st = p.stat()
                items.append(f"{p.name}|{st.st_size}|{int(st.st_mtime)}")
        key = str(folder.resolve()) + "||" + ";;".join(items)

    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def attachment_uri(p: pathlib.Path) -> str:
    """
    Cross-platform attachment URI.
    - For normal paths: Path.as_uri() works.
    - For UNC paths on Windows: best-effort convert \\server\share\... -> file://server/share/...
    """
    s = str(p)
    if os.name == "nt" and s.startswith("\\\\"):
        # UNC
        unc = s.lstrip("\\").replace("\\", "/")
        return "file://" + quote(unc)
    # normal
    return p.resolve().as_uri()

def ris_escape(s: str) -> str:
    return " ".join(str(s).replace("\n", " ").split()).strip()

def looks_like_supplement(name: str) -> bool:
    n = name.lower()
    bad = ["supp", "supplement", "supporting", "appendix", "si", "table", "fig", "dataset"]
    return any(k in n for k in bad)

