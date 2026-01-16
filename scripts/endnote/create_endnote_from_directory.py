#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create EndNote-compatible RIS from directory structure

Similar to zotero_restore_from_endnote_pdf_directories.py but:
- Uses relative paths (./pdf/) instead of file:// URIs
- Output structure suitable for EndNote import on Windows

Each subfolder under root is treated as ONE record.
Primary selection rules:
- If multiple PDFs:
  - prefer PDFs with DOI
  - if multiple DOI PDFs, let LLM choose main/fulltext vs supplement
- If no PDF: PPT/PPTX > DOC/DOCX > others

OCR:
- If PDF extracted text too short, try OCR (ocrmypdf or vision) then re-extract.

RIS:
- Authors: multiple AU lines (one per author)
- Attachments: multiple L1 lines with relative paths (./pdf/filename)

Example:
  python create_endnote_from_directory.py --enable_ocr --ocr_lang eng
  python create_endnote_from_directory.py --enable_ocr --ocr_lang eng+chi_sim
"""

from __future__ import annotations
import argparse
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from zr.dotenv import load_dotenv
from zr.config import apply_defaults
from zr.logger import make_logger
from zr.state import StateStore
from zr.file_scan import scan_record_folders
from zr.primary_select import choose_primary_in_folder
from zr.extract_text import extract_primary_text
from zr.providers import build_provider
from zr.utils import folder_id
from zr.classify import auto_classify_documents

# Import our custom EndNote RIS export module
import endnote_ris_export


def parse_args():
    p = argparse.ArgumentParser(
        description="Create EndNote-compatible RIS from directory structure with AI metadata extraction.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument("--dotenv", default=".env", help="Path to .env file (relative to current working directory).")
    p.add_argument("--root_dir", default=None,
                   help="Root directory containing subfolders (PDF/XXX/*). "
                        "If omitted, fallback to ROOT_DIR in .env/environment.")
    p.add_argument("--out_dir", default=None,
                   help="Output base dir. If omitted, fallback to OUT_DIR in .env/environment, then ./outputs.")
    p.add_argument("--recursive", action="store_true",
                   help="Scan root_dir recursively (usually NOT needed for EndNote PDF/XXX/*).")
    p.add_argument("--include_root_files", action="store_true", default=True,
                   help="Include root-level files as individual records (default True). "
                        "Each file in root dir becomes one record.")

    # LLM provider
    p.add_argument("--provider", choices=["ollama_native", "openai_sdk"], default=None,
                   help="LLM provider. Fallback PROVIDER in env.")
    p.add_argument("--model", default=None, help="Model name. Fallback MODEL in env.")
    p.add_argument("--base_url", default=None, help="Base URL. Fallback BASE_URL in env.")
    p.add_argument("--api_key_env", default=None,
                   help="Env var name for API key (openai_sdk). Fallback API_KEY_ENV/LLM_API_KEY.")
    p.add_argument("--timeout", type=int, default=600, help="HTTP timeout seconds.")
    p.add_argument("--num_ctx", type=int, default=16384, help="Ollama num_ctx (ollama_native only).")
    p.add_argument("--trust_env", action="store_true",
                   help="Allow http client to read proxy env vars (default: False, safer).")

    # PDF text extraction
    p.add_argument("--max_pages", type=int, default=2, help="Extract first N pages text.")
    p.add_argument("--scan_doi_pages", type=int, default=20, help="Scan first N pages to locate DOI page.")
    p.add_argument("--min_text_chars", type=int, default=250,
                   help="If extracted PDF text chars < this, treat as scanned/empty and try OCR.")

    # OCR
    p.add_argument("--enable_ocr", action="store_true",
                   help="Enable OCR fallback when PDF text is too short.")
    p.add_argument("--ocr_method", choices=["tesseract", "vision"], default=None,
                   help="OCR method: tesseract (CPU, slow) or vision (GPU/API, fast). Fallback OCR_METHOD in env.")

    # OCR Vision settings (when ocr_method=vision)
    p.add_argument("--ocr_provider", choices=["ollama_native", "openai_sdk"], default=None,
                   help="OCR provider for vision method. If omitted, uses main --provider. Fallback OCR_PROVIDER in env.")
    p.add_argument("--ocr_model", default=None,
                   help="OCR model name (e.g., qwen2-vl:7b, gpt-4-vision-preview). If omitted, uses main --model. Fallback OCR_MODEL in env.")
    p.add_argument("--ocr_base_url", default=None,
                   help="OCR API base URL. If omitted, uses main --base_url. Fallback OCR_BASE_URL in env.")
    p.add_argument("--ocr_api_key_env", default=None,
                   help="OCR API key env var name. If omitted, uses main --api_key_env. Fallback OCR_API_KEY_ENV in env.")

    # OCR Tesseract settings (when ocr_method=tesseract)
    p.add_argument("--ocr_lang", default="eng",
                   help="OCR language for tesseract (e.g., eng, chi_sim, eng+chi_sim). Only for tesseract method.")
    p.add_argument("--ocrmypdf_path", default="ocrmypdf",
                   help="Path to ocrmypdf executable. Only for tesseract method.")
    p.add_argument("--ocr_force", action="store_true",
                   help="Force OCR even if PDF seems to have text (for old scans).")

    # Behavior
    p.add_argument("--max_records", type=int, default=0,
                   help="Process only first N folders for testing (0 = all).")
    p.add_argument("--only_failed", action="store_true",
                   help="Only retry previously failed records (requires state).")
    p.add_argument("--skip_ok", action="store_true", default=True,
                   help="Skip records already marked OK in state (default True).")

    # Concurrency
    p.add_argument("--max_workers", type=int, default=0,
                   help="Max concurrent workers (0 = auto-detect: 10 for cloud API, 1 for local GPU).")

    # Supplement detection and merging
    p.add_argument("--merge_supplements", action="store_true",
                   help="Detect and merge supplement materials (e.g., -SE, -SM, -supplement) into main papers using LLM.")

    # Auto-classification
    p.add_argument("--auto_classify", action="store_true",
                   help="Automatically classify documents into categories after processing.")
    p.add_argument("--num_categories", type=int, default=20,
                   help="Target number of categories for auto-classification (default: 20).")
    p.add_argument("--predefined_categories", type=str, default=None,
                   help="Comma-separated list of predefined category names (e.g., 'Non-coding RNA,High Altitude Adaptation,Echolocation'). "
                        "LLM will generate remaining categories to reach --num_categories total.")

    return p.parse_args()


def process_single_record(folder, provider, cfg, state, out_dir, log, progress_lock, counters):
    """
    Process a single record (folder or file).
    Returns tuple: (success: bool, record_id: str, record_type: str, error: str or None)
    """
    rid = folder_id(folder)
    record_type = "file" if folder.is_file() else "folder"

    try:
        pick = choose_primary_in_folder(
            folder=folder,
            provider=provider,
            scan_doi_pages=cfg["scan_doi_pages"],
            max_pages=cfg["max_pages"],
            log=log,
        )
        primary = pick["primary"]
        reason = pick["primary_reason"]
        attachments = pick["attachments"]

        if primary is None:
            meta = {
                "title": f"Untitled record ({folder.name})",
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
                "evidence": {"note": "empty folder"},
                "confidence": 0.0,
                "flags": ["empty_folder"],
            }
        else:
            meta = extract_primary_text(
                primary=primary,
                provider=provider,
                cfg=cfg,
                folder=folder,
                primary_reason=reason,
                attachments=attachments,
                out_dir=out_dir,
                log=log,
            )

        # Write outputs using EndNote-compatible RIS export
        endnote_ris_export.write_record_outputs(
            out_dir=out_dir,
            folder=folder,
            record_id=rid,
            primary=primary,
            primary_reason=reason,
            attachments=attachments,
            meta=meta,
            log=log,
        )

        state.set(rid, {
            "status": "ok",
            "record_type": record_type,
            "folder": str(folder),
            "primary": str(primary) if primary else None,
            "primary_reason": reason,
        })

        with progress_lock:
            counters["done_ok"] += 1
            current = counters["done_ok"] + counters["failed"]
            log.info(f"[{current}/{counters['total']}] [OK] {record_type} {folder.name}")

        return (True, rid, record_type, None)

    except Exception as e:
        state.set(rid, {
            "status": "fail",
            "record_type": record_type,
            "folder": str(folder),
            "error": repr(e),
        })

        with progress_lock:
            counters["failed"] += 1
            current = counters["done_ok"] + counters["failed"]
            log.exception(f"[{current}/{counters['total']}] [FAIL] {record_type} {folder.name}: {e}")

        return (False, rid, record_type, str(e))


def main():
    args = parse_args()

    # Load .env (relative to current working directory if needed)
    dotenv_path = pathlib.Path(args.dotenv).expanduser()
    if not dotenv_path.is_absolute():
        # Use current working directory, not script directory
        dotenv_path = pathlib.Path.cwd() / dotenv_path
    load_dotenv(dotenv_path)

    # Apply env fallback / defaults
    cfg = apply_defaults(args)

    out_dir = pathlib.Path(cfg["out_dir"]).expanduser().resolve()
    root_dir = pathlib.Path(cfg["root_dir"]).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    log = make_logger(out_dir / "logs")
    log.info("=" * 60)
    log.info("EndNote RIS Generator with AI Metadata Extraction")
    log.info("=" * 60)
    log.info(f"Root dir:   {root_dir}")
    log.info(f"Out dir:    {out_dir}")
    log.info(f"Provider:   {cfg['provider']}")
    log.info(f"Model:      {cfg['model']}")
    log.info(f"Base URL:   {cfg['base_url']}")
    log.info(f"Recursive:  {cfg['recursive']}")
    log.info(f"OCR enable: {cfg['enable_ocr']}")
    if cfg['enable_ocr']:
        log.info(f"  OCR method:   {cfg['ocr_method']}")
        if cfg['ocr_method'] == 'vision':
            log.info(f"  OCR provider: {cfg.get('ocr_provider') or cfg['provider']} (fallback to main if None)")
            log.info(f"  OCR model:    {cfg.get('ocr_model') or cfg['model']} (fallback to main if None)")
            log.info(f"  OCR base_url: {cfg.get('ocr_base_url') or cfg['base_url']} (fallback to main if None)")
        elif cfg['ocr_method'] == 'tesseract':
            log.info(f"  OCR lang:     {cfg['ocr_lang']}")
            log.info(f"  OCR force:    {cfg['ocr_force']}")

    state = StateStore(out_dir / "state.jsonl", log)

    provider = build_provider(
        provider_name=cfg["provider"],
        model=cfg["model"],
        base_url=cfg["base_url"],
        timeout=cfg["timeout"],
        num_ctx=cfg["num_ctx"],
        api_key_env=cfg["api_key_env"],
        trust_env=cfg["trust_env"],
        log=log,
    )

    folders = scan_record_folders(root_dir, recursive=cfg["recursive"], include_root_files=cfg["include_root_files"])
    if cfg["max_records"] and cfg["max_records"] > 0:
        folders = folders[: cfg["max_records"]]

    total = len(folders)
    log.info(f"Found records: {total} (folders + root files)")

    done_ok = 0
    failed = 0
    pending = 0

    # Determine pending list
    pending_folders = []
    for f in folders:
        rid = folder_id(f)
        prev = state.get(rid)
        if cfg["only_failed"]:
            if prev and prev.get("status") == "fail":
                pending_folders.append(f)
        else:
            if cfg["skip_ok"] and prev and prev.get("status") == "ok":
                continue
            pending_folders.append(f)

    pending = len(pending_folders)
    log.info(f"Pending folders: {pending}")
    log.info(f"Max workers: {cfg['max_workers']} ({'auto-detected' if args.max_workers == 0 else 'user-specified'})")

    # Thread-safe counters and lock for progress logging
    progress_lock = threading.Lock()
    counters = {
        "done_ok": 0,
        "failed": 0,
        "total": pending,
    }

    # Process records concurrently
    if cfg['max_workers'] == 1:
        # Single-threaded mode (for local GPU or debugging)
        log.info("Running in single-threaded mode")
        for i, folder in enumerate(pending_folders, 1):
            rid = folder_id(folder)
            record_type = "file" if folder.is_file() else "folder"
            log.info(f"[{i}/{pending}] Processing {record_type}: {folder.name} (id={rid[:8]})")
            process_single_record(folder, provider, cfg, state, out_dir, log, progress_lock, counters)
    else:
        # Multi-threaded mode (for cloud API)
        log.info(f"Running in multi-threaded mode with {cfg['max_workers']} workers")
        with ThreadPoolExecutor(max_workers=cfg['max_workers']) as executor:
            # Submit all tasks
            futures = {}
            for folder in pending_folders:
                rid = folder_id(folder)
                record_type = "file" if folder.is_file() else "folder"
                log.info(f"Submitting {record_type}: {folder.name} (id={rid[:8]})")
                future = executor.submit(
                    process_single_record,
                    folder, provider, cfg, state, out_dir, log, progress_lock, counters
                )
                futures[future] = folder

            # Wait for completion and handle results
            for future in as_completed(futures):
                folder = futures[future]
                try:
                    success, rid, record_type, error = future.result()
                    # Logging already done in process_single_record
                except Exception as e:
                    log.exception(f"Unexpected error processing {folder.name}: {e}")

    done_ok = counters["done_ok"]
    failed = counters["failed"]

    log.info("=" * 60)
    log.info("Summary")
    log.info("=" * 60)
    log.info(f"Total:   {total}")
    log.info(f"OK:      {done_ok}")
    log.info(f"Failed:  {failed}")
    log.info("")
    log.info("Output structure:")
    log.info(f"  {out_dir}/out_ris/        - RIS files (one per record)")
    log.info(f"  {out_dir}/pdf/            - All attachments (copied)")
    log.info(f"  {out_dir}/out_intermediate/ - Intermediate JSON")
    log.info("")
    log.info("Next steps for EndNote import on Windows:")
    log.info(f"  1. Copy entire '{out_dir.name}' folder to Windows")
    log.info(f"  2. In EndNote: File → Import → File")
    log.info(f"  3. Select all .ris files in out_ris/ folder")
    log.info(f"  4. Import Option: RefMan (RIS)")
    log.info(f"  5. Check 'Copy files to library folder'")
    log.info(f"  6. EndNote will recognize ./pdf/ paths and copy attachments")
    log.info("Done.")

    # Supplement detection and merging (before classification)
    if args.merge_supplements:
        log.info("")
        log.info("Starting supplement detection and merging...")
        try:
            from zr.supplement_merge import detect_and_merge_supplements
            merged_count = detect_and_merge_supplements(
                out_dir=out_dir,
                provider=provider,
                log=log
            )
            if merged_count > 0:
                log.info(f"Successfully merged {merged_count} supplement materials")
        except Exception as e:
            log.error(f"Supplement merging failed: {e}")
            log.exception(e)

    # Auto-classification (if enabled)
    if args.auto_classify:
        log.info("")
        log.info("Starting automatic classification...")
        try:
            # Parse predefined categories
            predefined_cats = None
            if args.predefined_categories:
                predefined_cats = [cat.strip() for cat in args.predefined_categories.split(",") if cat.strip()]
                log.info(f"User-specified categories: {predefined_cats}")

            auto_classify_documents(
                out_dir=out_dir,
                num_categories=args.num_categories,
                predefined_categories=predefined_cats,
                provider=provider,
                log=log
            )
        except Exception as e:
            log.error(f"Auto-classification failed: {e}")
            log.exception(e)


if __name__ == "__main__":
    main()
