from __future__ import annotations
import pathlib
from typing import Dict, Any, List

from zr.utils import looks_like_supplement

PDF_EXT = {".pdf"}
PPT_EXT = {".ppt", ".pptx"}
WORD_EXT = {".doc", ".docx"}

def choose_primary_in_folder(
    folder: pathlib.Path,
    provider,
    scan_doi_pages: int,
    max_pages: int,
    log
) -> Dict[str, Any]:
    """
    Primary selection rules (EndNote restore):

    If folder is actually a file (single-file record):
    - Use that file as primary
    - No attachments

    If folder is a directory:
    1) If folder has any PDF -> PDF priority
    2) If multiple PDFs:
       - prefer PDFs with DOI
       - if multiple DOI PDFs: use LLM to choose MAIN/FULLTEXT vs supplement
    3) If no PDF: PPT/PPTX > DOC/DOCX > others
    """
    # Handle single-file records
    if folder.is_file():
        log.info(f"Single-file record: {folder.name}")
        return {
            "primary": folder,
            "primary_reason": "single_file_record",
            "attachments": [folder],
            "pdf_candidates": []
        }

    # Handle directory records (existing logic)
    files = [p for p in sorted(folder.glob("*")) if p.is_file()]
    if not files:
        return {"primary": None, "primary_reason": "empty_folder", "attachments": [], "pdf_candidates": []}

    pdfs = [p for p in files if p.suffix.lower() in PDF_EXT]
    ppts = [p for p in files if p.suffix.lower() in PPT_EXT]
    docs = [p for p in files if p.suffix.lower() in WORD_EXT]
    others = [p for p in files if p not in pdfs + ppts + docs]

    # ---------------------------
    # 1) PDF exists -> PDF priority
    # ---------------------------
    if pdfs:
        cand = []
        for p in pdfs:
            doi_hit = provider.quick_doi_hit(p, scan_pages=scan_doi_pages)
            cand.append({"path": p, "doi_hit": doi_hit})

        doi_pdfs = [c["path"] for c in cand if c["doi_hit"]]

        # 1.1 exactly one DOI PDF
        if len(doi_pdfs) == 1:
            primary = doi_pdfs[0]
            attachments = [primary] + [p for p in files if p != primary]
            return {
                "primary": primary,
                "primary_reason": "single_doi_pdf",
                "attachments": attachments,
                "pdf_candidates": cand
            }

        # 1.2 multiple DOI PDFs -> ask LLM choose main/fulltext
        if len(doi_pdfs) >= 2:
            primary = None
            try:
                primary = provider.choose_main_pdf(
                    doi_pdfs,
                    max_pages=max_pages,
                    scan_pages=scan_doi_pages
                )
            except Exception as e:
                log.warning(f"LLM choose_main_pdf failed, fallback heuristic. err={e!r}")

            if primary is None:
                # fallback: avoid supplement keywords; then prefer larger file size
                sorted_p = sorted(
                    doi_pdfs,
                    key=lambda p: (looks_like_supplement(p.name), -p.stat().st_size)
                )
                primary = sorted_p[0]
                reason = "fallback_main_pdf"
            else:
                reason = "llm_main_pdf"

            attachments = [primary] + [p for p in files if p != primary]
            return {
                "primary": primary,
                "primary_reason": reason,
                "attachments": attachments,
                "pdf_candidates": cand
            }

        # 1.3 no DOI PDFs -> still pick a best-looking PDF (avoid supplement; larger size)
        sorted_p = sorted(
            pdfs,
            key=lambda p: (looks_like_supplement(p.name), -p.stat().st_size)
        )
        primary = sorted_p[0]
        attachments = [primary] + [p for p in files if p != primary]
        return {
            "primary": primary,
            "primary_reason": "pdf_no_doi",
            "attachments": attachments,
            "pdf_candidates": cand
        }

    # ---------------------------
    # 2) No PDF -> PPT > WORD > others
    # ---------------------------
    if ppts:
        primary = ppts[0]
        attachments = [primary] + [p for p in files if p != primary]
        return {"primary": primary, "primary_reason": "ppt_primary", "attachments": attachments, "pdf_candidates": []}

    if docs:
        primary = docs[0]
        attachments = [primary] + [p for p in files if p != primary]
        return {"primary": primary, "primary_reason": "word_primary", "attachments": attachments, "pdf_candidates": []}

    # Others: still generate a record, use one file as "primary"
    primary = others[0] if others else files[0]
    attachments = [primary] + [p for p in files if p != primary]
    return {"primary": primary, "primary_reason": "other_primary", "attachments": attachments, "pdf_candidates": []}

