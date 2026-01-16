#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Word/PowerPoint document text extraction

This script tests if the system can properly extract text from
Word (.docx) and PowerPoint (.pptx) files.
"""

import sys
import pathlib

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from zr.providers import OllamaProvider, OpenAISDKProvider
from zr.logger import make_logger

def test_office_extraction():
    """Test Word and PowerPoint text extraction"""

    print("=" * 80)
    print("Office Document Text Extraction Test")
    print("=" * 80)

    # Create a dummy provider (we only need the text extraction methods)
    log = make_logger(pathlib.Path("./logs"))
    provider = OpenAISDKProvider(
        model="test",
        base_url="http://test",
        timeout=60,
        num_ctx=8192,
        api_key_env="TEST_KEY",
        trust_env=False,
        log=log
    )

    # Find test files
    pdf_dir = pathlib.Path("./pdf")

    # Test DOCX files
    docx_files = list(pdf_dir.glob("**/*.docx"))
    print(f"\nFound {len(docx_files)} .docx files")

    for docx_file in docx_files[:3]:  # Test first 3
        print(f"\n{'='*60}")
        print(f"Testing: {docx_file.name}")
        print(f"{'='*60}")

        try:
            text = provider.generic_text_snippet(docx_file)
            if text:
                print(f"OK Extracted {len(text)} characters")
                print(f"\nFirst 500 chars:")
                print("-" * 60)
                print(text[:500])
                print("-" * 60)
            else:
                print("X No text extracted")
        except Exception as e:
            print(f"X Error: {e}")

    # Test PPTX files
    pptx_files = list(pdf_dir.glob("**/*.pptx"))
    print(f"\n\nFound {len(pptx_files)} .pptx files")

    for pptx_file in pptx_files[:3]:  # Test first 3
        print(f"\n{'='*60}")
        print(f"Testing: {pptx_file.name}")
        print(f"{'='*60}")

        try:
            text = provider.generic_text_snippet(pptx_file)
            if text:
                print(f"OK Extracted {len(text)} characters")
                print(f"\nFirst 500 chars:")
                print("-" * 60)
                print(text[:500])
                print("-" * 60)
            else:
                print("X No text extracted")
        except Exception as e:
            print(f"X Error: {e}")

    # Test DOC files (old format)
    doc_files = list(pdf_dir.glob("**/*.doc"))
    print(f"\n\nFound {len(doc_files)} .doc files")

    if doc_files:
        print("\nNote: .doc files require LibreOffice to be installed for conversion")
        for doc_file in doc_files[:2]:  # Test first 2
            print(f"\n{'='*60}")
            print(f"Testing: {doc_file.name}")
            print(f"{'='*60}")

            try:
                text = provider.generic_text_snippet(doc_file)
                if text:
                    print(f"OK Extracted {len(text)} characters")
                    print(f"\nFirst 500 chars:")
                    print("-" * 60)
                    print(text[:500])
                    print("-" * 60)
                else:
                    print("X No text extracted (LibreOffice may not be installed)")
            except Exception as e:
                print(f"X Error: {e}")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
    print("\nSummary:")
    print(f"- DOCX files: {len(docx_files)}")
    print(f"- PPTX files: {len(pptx_files)}")
    print(f"- DOC files: {len(doc_files)}")
    print("\nIf text extraction failed:")
    print("1. Check if python-docx and python-pptx are installed:")
    print("   pip install python-docx python-pptx")
    print("2. For .doc/.ppt files, install LibreOffice:")
    print("   https://www.libreoffice.org/download/")

if __name__ == "__main__":
    test_office_extraction()
