from __future__ import annotations
import pathlib
import base64
import io
import os
from typing import Optional, List
import fitz  # PyMuPDF
from PIL import Image


def pdf_pages_to_images(pdf_path: pathlib.Path, max_pages: int = 2, dpi: int = 150) -> List[Image.Image]:
    """
    Convert first N pages of PDF to PIL Images.
    Lower DPI for faster processing, 150 is good balance.
    """
    doc = fitz.open(pdf_path)
    images = []
    for i in range(min(max_pages, doc.page_count)):
        page = doc.load_page(i)
        # Render at specified DPI (150 is ~2x screen resolution, good for OCR)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images


def image_to_base64(img: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def ocr_with_vision_model(
    pdf_path: pathlib.Path,
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    max_pages: int,
    timeout: int,
    trust_env: bool,
    log,
) -> Optional[str]:
    """
    Universal vision OCR function that works with both Ollama and OpenAI-compatible APIs.

    Args:
        pdf_path: Path to PDF file
        provider: "ollama_native" or "openai_sdk"
        model: Model name (e.g., "qwen2-vl:7b", "gpt-4-vision-preview")
        base_url: API base URL
        api_key_env: Environment variable name for API key (for openai_sdk)
        max_pages: Number of pages to OCR
        timeout: Request timeout in seconds
        trust_env: Whether to trust environment proxy settings
        log: Logger instance

    Returns:
        Extracted text or None if failed
    """
    try:
        # Convert PDF pages to images
        log.info(f"OCR Vision ({provider}): Converting {pdf_path.name} to images (max {max_pages} pages)")
        images = pdf_pages_to_images(pdf_path, max_pages=max_pages, dpi=150)

        if not images:
            log.warning(f"OCR Vision: No images extracted from {pdf_path.name}")
            return None

        all_text = []

        if provider == "ollama_native":
            # Use Ollama native API
            import requests

            for i, img in enumerate(images, 1):
                log.info(f"OCR Vision (Ollama): Processing page {i}/{len(images)} of {pdf_path.name}")

                img_b64 = image_to_base64(img)

                prompt = (
                    "Extract all text from this image. "
                    "Preserve the original layout and structure. "
                    "If there are tables, preserve them. "
                    "Output only the extracted text, no explanations."
                )

                payload = {
                    "model": model,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                }

                url = base_url.rstrip("/") + "/api/generate"
                resp = requests.post(url, json=payload, timeout=timeout)

                if resp.status_code != 200:
                    log.warning(f"OCR Vision (Ollama): API error {resp.status_code} for page {i}")
                    continue

                result = resp.json()
                text = result.get("response", "").strip()

                if text:
                    all_text.append(f"[PAGE {i}]\n{text}")
                    log.info(f"OCR Vision (Ollama): Extracted {len(text)} chars from page {i}")

        elif provider == "openai_sdk":
            # Use OpenAI-compatible API
            from openai import OpenAI
            import httpx

            api_key = os.getenv(api_key_env) or os.getenv("OPENAI_API_KEY")
            if not api_key:
                log.warning(f"OCR Vision (OpenAI): No API key found in {api_key_env} or OPENAI_API_KEY")
                return None

            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
                http_client=httpx.Client(trust_env=trust_env),
            )

            for i, img in enumerate(images, 1):
                log.info(f"OCR Vision (OpenAI): Processing page {i}/{len(images)} of {pdf_path.name}")

                img_b64 = image_to_base64(img)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Extract all text from this image. "
                                    "Preserve the original layout and structure. "
                                    "Output only the extracted text, no explanations."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ]
                    }
                ]

                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=4096,
                )

                text = resp.choices[0].message.content.strip()
                if text:
                    all_text.append(f"[PAGE {i}]\n{text}")
                    log.info(f"OCR Vision (OpenAI): Extracted {len(text)} chars from page {i}")

        else:
            log.error(f"Unknown OCR provider: {provider}")
            return None

        if not all_text:
            return None

        combined = "\n\n".join(all_text)
        log.info(f"OCR Vision ({provider}): Total extracted {len(combined)} chars from {len(images)} pages")
        return combined

    except Exception as e:
        log.warning(f"OCR Vision ({provider}) failed: {e}")
        return None
