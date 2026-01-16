from __future__ import annotations
import os

def _pick(cli_val, env_key, default_val):
    if cli_val is not None and str(cli_val).strip() != "":
        return cli_val
    env_val = os.getenv(env_key)
    if env_val is not None and str(env_val).strip() != "":
        return env_val
    return default_val

def apply_defaults(args) -> dict:
    """
    Priority: CLI (if provided) > .env/env > hardcoded defaults
    """
    cfg = {}
    cfg["provider"] = _pick(args.provider, "PROVIDER", "ollama_native")
    cfg["model"] = _pick(args.model, "MODEL", "yasserrmd/Qwen2.5-7B-Instruct-1M")
    cfg["base_url"] = _pick(args.base_url, "BASE_URL", "http://localhost:11434")
    cfg["api_key_env"] = _pick(args.api_key_env, "API_KEY_ENV", "LLM_API_KEY")

    cfg["root_dir"] = _pick(args.root_dir, "ROOT_DIR", None)
    if not cfg["root_dir"]:
        raise SystemExit("Missing --root_dir and ROOT_DIR not set in .env/environment.")

    cfg["out_dir"] = _pick(args.out_dir, "OUT_DIR", "./outputs")
    cfg["recursive"] = bool(args.recursive)
    cfg["include_root_files"] = bool(args.include_root_files)

    cfg["timeout"] = int(args.timeout)
    cfg["num_ctx"] = int(args.num_ctx)
    cfg["trust_env"] = bool(args.trust_env)

    cfg["max_pages"] = int(args.max_pages)
    cfg["scan_doi_pages"] = int(args.scan_doi_pages)
    cfg["min_text_chars"] = int(args.min_text_chars)

    cfg["enable_ocr"] = bool(args.enable_ocr)
    cfg["ocr_method"] = _pick(args.ocr_method, "OCR_METHOD", "tesseract")
    cfg["ocr_provider"] = _pick(args.ocr_provider, "OCR_PROVIDER", None)  # ollama_native, openai_sdk, or None (use main provider)
    cfg["ocr_model"] = _pick(args.ocr_model, "OCR_MODEL", None)
    cfg["ocr_base_url"] = _pick(args.ocr_base_url, "OCR_BASE_URL", None)  # None = use main base_url
    cfg["ocr_api_key_env"] = _pick(args.ocr_api_key_env, "OCR_API_KEY_ENV", None)  # None = use main api_key_env
    cfg["ocr_lang"] = str(args.ocr_lang)
    cfg["ocrmypdf_path"] = str(args.ocrmypdf_path)
    cfg["ocr_force"] = bool(args.ocr_force)

    cfg["max_records"] = int(args.max_records)
    cfg["only_failed"] = bool(args.only_failed)
    cfg["skip_ok"] = bool(args.skip_ok)

    # Concurrency settings
    cfg["max_workers"] = int(args.max_workers) if args.max_workers > 0 else None
    # Auto-detect workers if not specified
    if cfg["max_workers"] is None:
        if cfg["provider"] == "openai_sdk":
            cfg["max_workers"] = 10  # Cloud API can handle more concurrent requests
        else:  # ollama_native
            cfg["max_workers"] = 1   # Local GPU limited by VRAM

    return cfg

