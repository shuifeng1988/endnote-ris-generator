from __future__ import annotations
import pathlib
from typing import Dict, Any, Optional, Callable, List


class FallbackChain:
    """
    Intelligent fallback chain for robust processing.

    Tries multiple strategies in order until one succeeds.
    """
    def __init__(self, log):
        self.log = log

    def execute(
        self,
        strategies: List[tuple[str, Callable]],
        context: str = "Operation"
    ) -> Optional[Any]:
        """
        Execute strategies in order until one succeeds.

        Args:
            strategies: List of (name, function) tuples
            context: Description of what we're trying to do

        Returns:
            Result from first successful strategy, or None if all fail
        """
        last_error = None

        for i, (name, func) in enumerate(strategies, 1):
            try:
                self.log.info(f"{context}: Trying strategy {i}/{len(strategies)}: {name}")
                result = func()

                if result is not None:
                    self.log.info(f"{context}: ✓ Success with {name}")
                    return result
                else:
                    self.log.warning(f"{context}: {name} returned None, trying next...")

            except Exception as e:
                last_error = e
                self.log.warning(f"{context}: {name} failed: {e}")

                if i < len(strategies):
                    self.log.info(f"{context}: Falling back to next strategy...")
                else:
                    self.log.error(f"{context}: All {len(strategies)} strategies failed")

        return None


def create_ocr_fallback_chain(
    pdf_path: pathlib.Path,
    cfg: dict,
    provider,
    interm_dir: pathlib.Path,
    log
) -> FallbackChain:
    """
    Create intelligent OCR fallback chain.

    Strategy order:
    1. Vision OCR (fast, GPU/API)
    2. Tesseract OCR (slow, CPU)
    3. Use filename as title (always succeeds)
    """
    from zr.ocr_vision import ocr_with_vision_model
    from zr.ocr import try_ocr_pdf

    chain = FallbackChain(log)

    strategies = []

    # Strategy 1: Vision OCR (if configured)
    if cfg.get("ocr_method") == "vision":
        def vision_ocr():
            ocr_provider = cfg.get("ocr_provider") or cfg["provider"]
            ocr_model = cfg.get("ocr_model") or cfg["model"]
            ocr_base_url = cfg.get("ocr_base_url") or cfg["base_url"]
            ocr_api_key_env = cfg.get("ocr_api_key_env") or cfg["api_key_env"]

            return ocr_with_vision_model(
                pdf_path=pdf_path,
                provider=ocr_provider,
                model=ocr_model,
                base_url=ocr_base_url,
                api_key_env=ocr_api_key_env,
                max_pages=cfg["max_pages"],
                timeout=cfg["timeout"],
                trust_env=cfg["trust_env"],
                log=log,
            )

        strategies.append(("Vision OCR", vision_ocr))

    # Strategy 2: Tesseract OCR (always available as fallback)
    def tesseract_ocr():
        ocr_out = interm_dir / "ocr_pdfs" / f"{pdf_path.stem}.ocr.pdf"
        ocr_pdf = try_ocr_pdf(
            input_pdf=pdf_path,
            output_pdf=ocr_out,
            ocrmypdf_path=cfg.get("ocrmypdf_path", "ocrmypdf"),
            lang=cfg.get("ocr_lang", "eng"),
            log=log,
            force=cfg.get("ocr_force", False),
        )
        if ocr_pdf:
            info = provider.pdf_text_snippet(
                ocr_pdf,
                max_pages=cfg["max_pages"],
                scan_doi_pages=cfg["scan_doi_pages"]
            )
            return info.get("text", "").strip()
        return None

    strategies.append(("Tesseract OCR", tesseract_ocr))

    # Strategy 3: Filename fallback (always succeeds)
    def filename_fallback():
        log.warning(f"All OCR methods failed, using filename as title")
        return f"[OCR Failed] {pdf_path.stem}"

    strategies.append(("Filename Fallback", filename_fallback))

    return chain, strategies


def create_metadata_extraction_fallback(
    text: str,
    provider,
    log
) -> tuple[FallbackChain, List]:
    """
    Create fallback chain for metadata extraction.

    Strategy order:
    1. Full extraction with all fields
    2. Minimal extraction (title + authors only)
    3. Title from first line
    """
    chain = FallbackChain(log)

    strategies = []

    # Strategy 1: Full extraction
    def full_extraction():
        return provider.extract_biblio(text)

    strategies.append(("Full Metadata Extraction", full_extraction))

    # Strategy 2: Minimal extraction (if provider has method)
    if hasattr(provider, 'extract_minimal'):
        def minimal_extraction():
            return provider.extract_minimal(text)

        strategies.append(("Minimal Extraction", minimal_extraction))

    # Strategy 3: Basic fallback
    def basic_fallback():
        lines = text.strip().split('\n')
        title = lines[0] if lines else "Untitled"

        return {
            "title": title[:200],  # First line as title
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
            "confidence": 0.1,
            "flags": ["extraction_failed", "basic_fallback"],
            "evidence": {"note": "Metadata extraction failed, using basic fallback"}
        }

    strategies.append(("Basic Fallback", basic_fallback))

    return chain, strategies


def auto_repair_metadata(meta: Dict[str, Any], log) -> Dict[str, Any]:
    """
    Automatically repair common metadata errors.

    Fixes:
    - OCR errors in year (o→0, O→0, l→1)
    - DOI formatting (remove spaces, fix case)
    - Author name normalization
    - Invalid year ranges
    """
    repaired = meta.copy()
    repairs = []

    # Fix year
    if repaired.get("year"):
        original_year = repaired["year"]
        year_str = str(original_year)

        # Fix OCR errors
        year_str = year_str.replace("o", "0").replace("O", "0").replace("l", "1")

        # Extract 4-digit year
        import re
        year_match = re.search(r'(19|20)\d{2}', year_str)
        if year_match:
            try:
                fixed_year = int(year_match.group(0))
                if 1900 <= fixed_year <= 2100:
                    repaired["year"] = fixed_year
                    if fixed_year != original_year:
                        repairs.append(f"year: {original_year} → {fixed_year}")
            except:
                pass

    # Fix DOI
    if repaired.get("doi"):
        original_doi = repaired["doi"]
        fixed_doi = original_doi.strip().replace(" ", "")

        # Remove common prefixes
        if fixed_doi.lower().startswith("doi:"):
            fixed_doi = fixed_doi[4:].strip()
        if fixed_doi.lower().startswith("http://dx.doi.org/"):
            fixed_doi = fixed_doi[18:]
        if fixed_doi.lower().startswith("https://doi.org/"):
            fixed_doi = fixed_doi[16:]

        if fixed_doi != original_doi:
            repaired["doi"] = fixed_doi
            repairs.append(f"doi: cleaned")

    # Normalize authors
    if repaired.get("authors") and isinstance(repaired["authors"], list):
        original_authors = repaired["authors"]
        fixed_authors = []

        for author in original_authors:
            if not author or not isinstance(author, str):
                continue

            # Remove extra whitespace
            author = " ".join(author.split())

            # Remove trailing commas/periods
            author = author.rstrip(".,;")

            if author:
                fixed_authors.append(author)

        if fixed_authors != original_authors:
            repaired["authors"] = fixed_authors
            repairs.append(f"authors: normalized {len(fixed_authors)} names")

    # Add repair log
    if repairs:
        log.info(f"Auto-repaired metadata: {', '.join(repairs)}")
        repaired.setdefault("flags", [])
        repaired["flags"].append("auto_repaired")

    return repaired


def calculate_confidence_score(meta: Dict[str, Any]) -> float:
    """
    Calculate confidence score for extracted metadata.

    Score components:
    - DOI present: +0.3
    - Authors present: +0.2
    - Year present: +0.2
    - Title present: +0.2
    - Abstract present (>100 chars): +0.1
    """
    score = 0.0

    if meta.get("doi"):
        score += 0.3

    if meta.get("authors") and len(meta["authors"]) > 0:
        score += 0.2

    if meta.get("year"):
        try:
            year = int(meta["year"])
            if 1900 <= year <= 2100:
                score += 0.2
        except:
            pass

    if meta.get("title") and len(str(meta["title"])) > 10:
        score += 0.2

    if meta.get("abstract") and len(str(meta["abstract"])) > 100:
        score += 0.1

    return round(score, 2)
