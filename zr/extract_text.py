from __future__ import annotations
import pathlib
import os
from typing import Dict, Any, List
from zr.ocr import try_ocr_pdf
from zr.ocr_vision import ocr_with_vision_model

def extract_primary_text(primary: pathlib.Path, provider, cfg: dict, folder: pathlib.Path,
                         primary_reason: str, attachments: List[pathlib.Path],
                         out_dir: pathlib.Path, log) -> Dict[str, Any]:
    """
    Extract metadata from primary file (PDF preferred).
    If PDF text is too short, try OCR then re-extract.
    """
    suffix = primary.suffix.lower()

    # Ensure intermediate dirs
    interm_dir = out_dir / "out_intermediate"
    interm_dir.mkdir(parents=True, exist_ok=True)

    # PDF path
    if suffix == ".pdf":
        info = provider.pdf_text_snippet(primary, max_pages=cfg["max_pages"], scan_doi_pages=cfg["scan_doi_pages"])
        text = info["text"] or ""

        # OCR if text is too short
        if cfg["enable_ocr"] and (cfg["ocr_force"] or len(text.strip()) < cfg["min_text_chars"]):
            ocr_text = None
            ocr_method = cfg.get("ocr_method", "tesseract")

            if ocr_method == "vision":
                # Vision-based OCR (GPU or API)
                # Determine OCR provider/model/base_url
                ocr_provider = cfg.get("ocr_provider") or cfg["provider"]
                ocr_model = cfg.get("ocr_model") or cfg["model"]
                ocr_base_url = cfg.get("ocr_base_url") or cfg["base_url"]
                ocr_api_key_env = cfg.get("ocr_api_key_env") or cfg["api_key_env"]

                log.info(f"Using vision OCR: provider={ocr_provider}, model={ocr_model}, base_url={ocr_base_url}")

                ocr_text = ocr_with_vision_model(
                    pdf_path=primary,
                    provider=ocr_provider,
                    model=ocr_model,
                    base_url=ocr_base_url,
                    api_key_env=ocr_api_key_env,
                    max_pages=cfg["max_pages"],
                    timeout=cfg["timeout"],
                    trust_env=cfg["trust_env"],
                    log=log,
                )

            elif ocr_method == "tesseract":
                # Traditional Tesseract OCR (CPU-based)
                log.info("Using Tesseract OCR (CPU-based, slow)")
                ocr_out = interm_dir / "ocr_pdfs" / f"{primary.stem}.ocr.pdf"
                ocr_pdf = try_ocr_pdf(
                    input_pdf=primary,
                    output_pdf=ocr_out,
                    ocrmypdf_path=cfg["ocrmypdf_path"],
                    lang=cfg["ocr_lang"],
                    log=log,
                    force=cfg["ocr_force"],
                )
                if ocr_pdf:
                    info2 = provider.pdf_text_snippet(ocr_pdf, max_pages=cfg["max_pages"], scan_doi_pages=cfg["scan_doi_pages"])
                    ocr_text = info2.get("text", "").strip()

            else:
                log.warning(f"Unknown OCR method: {ocr_method}, skipping OCR")

            # Use OCR text if successful and better than original
            if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                log.info(f"OCR successful: extracted {len(text)} chars (method={ocr_method})")
            elif ocr_text:
                log.warning(f"OCR did not improve text extraction (original={len(text)}, ocr={len(ocr_text)})")
            else:
                log.warning(f"OCR failed to extract text")

        meta = provider.extract_biblio(text)
        # Use LLM-determined record_type, fallback to JOUR only if not provided
        if not meta.get("record_type"):
            meta["record_type"] = "JOUR"
        meta.setdefault("abstract", None)
        meta.setdefault("confidence", 0.7)
        meta.setdefault("flags", [])
        meta["evidence"] = meta.get("evidence") or {}
        meta["evidence"]["primary_reason"] = primary_reason
        meta["evidence"]["folder"] = str(folder)
        meta["evidence"]["primary"] = str(primary)
        meta["evidence"]["attachments_count"] = len(attachments)
        return meta

    # PPTX / DOCX / TXT / others: create a minimal record using filename
    text = provider.generic_text_snippet(primary)
    if text and len(text.strip()) > 80:
        meta = provider.extract_generic(text)
        meta.setdefault("record_type", "GEN")
        meta.setdefault("confidence", 0.5)
        meta.setdefault("flags", ["non_pdf_primary"])
        meta["evidence"] = meta.get("evidence") or {}
        meta["evidence"]["primary_reason"] = primary_reason
        meta["evidence"]["primary"] = str(primary)
        return meta

    # fallback: no text available
    title = primary.stem.replace("_", " ").replace("-", " ").strip() or f"Untitled ({folder.name})"
    return {
        "title": title,
        "authors": None,
        "year": None,
        "journal": None,
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "url": None,
        "abstract": None,
        "record_type": "GEN",
        "confidence": 0.2,
        "flags": ["no_text_fallback"],
        "evidence": {
            "primary_reason": primary_reason,
            "primary": str(primary),
            "folder": str(folder),
        }
    }

