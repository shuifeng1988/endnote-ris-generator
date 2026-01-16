from __future__ import annotations
import pathlib
import subprocess
from typing import Optional

def try_ocr_pdf(
    input_pdf: pathlib.Path,
    output_pdf: pathlib.Path,
    ocrmypdf_path: str,
    lang: str,
    log,
    force: bool = False,
) -> Optional[pathlib.Path]:
    """
    Use ocrmypdf to generate a text layer PDF.
    Returns output_pdf if success else None.
    """
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ocrmypdf_path,
        "--skip-text",  # only OCR pages without text
        "--language", lang,
        str(input_pdf),
        str(output_pdf),
    ]
    if force:
        # re-OCR even if it has text; ocrmypdf uses --force-ocr for that
        cmd.insert(1, "--force-ocr")

    try:
        log.info(f"OCR: running {' '.join(cmd)}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            log.warning(f"OCR failed (code={r.returncode}). stderr:\n{r.stderr[:800]}")
            return None
        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            return output_pdf
        return None
    except FileNotFoundError:
        log.warning("OCR failed: ocrmypdf not found. Install ocrmypdf or set --ocrmypdf_path.")
        return None
    except Exception as e:
        log.warning(f"OCR failed: {e}")
        return None

