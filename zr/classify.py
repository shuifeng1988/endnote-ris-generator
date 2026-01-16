"""
Automatic document classification using LLM.

This module provides functionality to:
1. Collect metadata from all processed records
2. Use LLM to cluster documents into categories
3. Automatically name each category
4. Copy RIS files to categorized directories
"""

import json
import logging
import pathlib
import shutil
from typing import Dict, List, Any, Optional
import time


def collect_metadata(intermediate_dir: pathlib.Path, log: logging.Logger) -> List[Dict[str, Any]]:
    """
    Collect metadata from all JSON files in intermediate directory.

    Args:
        intermediate_dir: Path to out_intermediate directory
        log: Logger instance

    Returns:
        List of metadata dicts with keys: record_id, title, abstract, authors,
        journal, year, primary_file, file_type, ris_filename
    """
    log.info(f"Collecting metadata from {intermediate_dir}")

    json_files = list(intermediate_dir.glob("*.json"))
    log.info(f"Found {len(json_files)} JSON files")

    records = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            meta = data.get("meta", {})
            primary = data.get("primary", "")

            # Determine file type from primary file extension
            file_type = "unknown"
            if primary:
                ext = pathlib.Path(primary).suffix.lower()
                if ext == ".pdf":
                    file_type = "pdf"
                elif ext in [".doc", ".docx"]:
                    file_type = "word"
                elif ext in [".ppt", ".pptx"]:
                    file_type = "powerpoint"
                elif ext in [".txt", ".md"]:
                    file_type = "text"

            # Get RIS filename (same basename as JSON)
            ris_filename = json_file.stem + ".ris"

            record = {
                "record_id": data.get("record_id", ""),
                "title": meta.get("title", ""),
                "abstract": meta.get("abstract", ""),
                "authors": meta.get("authors", []),
                "journal": meta.get("journal", ""),
                "year": meta.get("year", ""),
                "primary_file": primary,
                "file_type": file_type,
                "ris_filename": ris_filename,
                "folder": data.get("folder", ""),
            }
            records.append(record)

        except Exception as e:
            log.warning(f"Failed to read {json_file}: {e}")
            continue

    log.info(f"Successfully collected {len(records)} records")
    return records


def classify_with_llm(
    records: List[Dict[str, Any]],
    num_categories: int,
    provider,
    log: logging.Logger,
    predefined_categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Use LLM to classify documents into categories using a two-stage approach.

    Stage 1: Generate category definitions based on document overview
    Stage 2: Assign each document to the best matching category

    This ensures at least 80% of documents are categorized.

    Args:
        records: List of metadata dicts
        num_categories: Target number of categories (including predefined ones)
        provider: LLM provider instance (OllamaProvider or OpenAISDKProvider)
        log: Logger instance
        predefined_categories: Optional list of user-specified category names

    Returns:
        Dict with keys:
        - categories: List of category dicts with {name, description, record_ids}
        - uncategorized: List of record_ids that couldn't be categorized
    """
    log.info(f"Starting two-stage LLM classification into {num_categories} categories")

    if predefined_categories:
        log.info(f"User-specified categories ({len(predefined_categories)}): {', '.join(predefined_categories)}")

    # Stage 1: Generate category definitions
    log.info("Stage 1: Generating category definitions...")
    categories = _generate_categories(
        records,
        num_categories,
        provider,
        log,
        predefined_categories=predefined_categories
    )

    if not categories:
        log.error("Failed to generate categories")
        return {"categories": [], "uncategorized": [r["record_id"] for r in records]}

    log.info(f"Generated {len(categories)} categories")
    for cat in categories:
        log.info(f"  - {cat['name']}: {cat['description']}")

    # Stage 2: Assign documents to categories
    log.info("Stage 2: Assigning documents to categories...")
    assignment = _assign_documents_to_categories(records, categories, provider, log)

    # Build final result
    category_map = {cat["name"]: cat for cat in categories}
    for cat in categories:
        cat["record_ids"] = []

    uncategorized = []

    for record_id, category_name in assignment.items():
        if category_name and category_name in category_map:
            category_map[category_name]["record_ids"].append(record_id)
        else:
            uncategorized.append(record_id)

    # Calculate statistics
    total = len(records)
    categorized_count = total - len(uncategorized)
    categorization_rate = (categorized_count / total * 100) if total > 0 else 0

    log.info(f"Classification complete:")
    log.info(f"  Total documents: {total}")
    log.info(f"  Categorized: {categorized_count} ({categorization_rate:.1f}%)")
    log.info(f"  Uncategorized: {len(uncategorized)} ({100-categorization_rate:.1f}%)")

    for cat in categories:
        count = len(cat["record_ids"])
        log.info(f"  {cat['name']}: {count} documents")

    return {
        "categories": categories,
        "uncategorized": uncategorized
    }


def _generate_categories(
    records: List[Dict[str, Any]],
    num_categories: int,
    provider,
    log: logging.Logger,
    predefined_categories: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Stage 1: Generate category definitions based on document overview.

    If predefined_categories is provided, those categories are included first,
    and LLM generates additional categories to reach num_categories total.

    Returns:
        List of category dicts with {name, description}
    """
    # Sample documents for overview (use more samples for better coverage)
    sample_size = min(500, len(records))
    import random
    sampled = random.sample(records, sample_size) if len(records) > sample_size else records

    # Prepare overview
    summaries = []
    for rec in sampled:
        title = rec.get("title", "No title")
        file_type = rec.get("file_type", "unknown")
        journal = rec.get("journal", "")

        summary = f"Type: {file_type} | Title: {title}"
        if journal:
            summary += f" | Journal: {journal}"
        summaries.append(summary)

    # Build predefined categories section
    predefined_section = ""
    num_to_generate = num_categories
    if predefined_categories:
        num_to_generate = max(0, num_categories - len(predefined_categories))
        predefined_section = f"""
USER-SPECIFIED CATEGORIES (must be included):
{chr(10).join(f"{i+1}. {cat}" for i, cat in enumerate(predefined_categories))}

You must include ALL of the above categories in your output.
Generate {num_to_generate} ADDITIONAL categories to reach a total of {num_categories} categories.
"""
    else:
        predefined_section = f"Generate {num_categories} categories."

    prompt = f"""You are a document classification expert. Based on the following sample of {len(sampled)} documents (out of {len(records)} total), generate categories for classification.

{predefined_section}

REQUIREMENTS:
1. Categories should cover at least 80% of all documents
2. Use broad, inclusive categories rather than narrow ones
3. First separate by document type (Word, PowerPoint, Books, Text files)
4. For PDF documents, create topic-based categories (e.g., Genomics, Neuroscience, Cancer, Evolution)
5. Use 2-4 word category names (English, filesystem-safe)
6. Each category needs a clear description

SAMPLE DOCUMENTS:
{chr(10).join(summaries[:200])}

{"... (showing first 200 samples)" if len(summaries) > 200 else ""}

Total documents to classify: {len(records)}
Sample shown: {len(sampled)}

OUTPUT FORMAT (JSON only):
{{
  "categories": [
    {{
      "name": "Category Name",
      "description": "Clear description of what documents belong here"
    }},
    ...
  ]
}}

IMPORTANT:
- {"Include ALL user-specified categories PLUS " + str(num_to_generate) + " additional categories" if predefined_categories else "Generate exactly " + str(num_categories) + " categories"}
- Make categories broad enough to cover most documents
- Category names must be filesystem-safe (no special characters)
- Return ONLY valid JSON
"""

    try:
        if hasattr(provider, 'extract_biblio'):
            result = _call_openai_classify(provider, prompt, log)
        else:
            result = _call_ollama_classify(provider, prompt, log)

        if result and "categories" in result:
            generated_cats = result["categories"]

            # If predefined categories exist, ensure they are included
            if predefined_categories:
                # Sanitize predefined category names
                predefined_sanitized = [sanitize_category_name(cat) for cat in predefined_categories]

                # Check if LLM included them
                generated_names = {cat["name"] for cat in generated_cats}
                missing_predefined = []

                for orig_name, sanitized_name in zip(predefined_categories, predefined_sanitized):
                    # Check if either original or sanitized name is in generated categories
                    if orig_name not in generated_names and sanitized_name not in generated_names:
                        missing_predefined.append({
                            "name": sanitized_name,
                            "description": f"User-specified category: {orig_name}"
                        })

                # Add missing predefined categories at the beginning
                if missing_predefined:
                    log.warning(f"LLM did not include {len(missing_predefined)} predefined categories, adding them manually")
                    generated_cats = missing_predefined + generated_cats

            return generated_cats
        else:
            log.error("Invalid category generation result")
            return []

    except Exception as e:
        log.error(f"Category generation failed: {e}")
        return []


def _assign_documents_to_categories(
    records: List[Dict[str, Any]],
    categories: List[Dict[str, str]],
    provider,
    log: logging.Logger
) -> Dict[str, str]:
    """
    Stage 2: Assign each document to the best matching category.

    Process documents in batches to avoid token limits.

    Returns:
        Dict mapping record_id to category_name (or None for uncategorized)
    """
    # Build category list for prompt
    category_list = []
    for i, cat in enumerate(categories):
        category_list.append(f"{i}. {cat['name']}: {cat['description']}")

    category_text = "\n".join(category_list)

    # Process in batches
    batch_size = 50  # Process 50 documents at a time
    assignment = {}

    for batch_start in range(0, len(records), batch_size):
        batch_end = min(batch_start + batch_size, len(records))
        batch = records[batch_start:batch_end]

        log.info(f"  Processing batch {batch_start//batch_size + 1}/{(len(records)-1)//batch_size + 1} ({len(batch)} documents)")

        # Prepare document summaries
        doc_summaries = []
        for i, rec in enumerate(batch):
            title = rec.get("title", "No title")
            abstract = rec.get("abstract", "")
            file_type = rec.get("file_type", "unknown")
            journal = rec.get("journal", "")

            # Truncate abstract
            abstract_snippet = abstract[:200] if abstract else ""

            summary = f"[{i}] Type: {file_type} | Title: {title}"
            if journal:
                summary += f" | Journal: {journal}"
            if abstract_snippet:
                summary += f" | Abstract: {abstract_snippet}..."

            doc_summaries.append(summary)

        prompt = f"""Assign each document to the BEST matching category. You MUST assign at least 80% of documents to categories (not "other").

CATEGORIES:
{category_text}
{len(categories)}. Other (only for documents that truly don't fit any category)

DOCUMENTS:
{chr(10).join(doc_summaries)}

OUTPUT FORMAT (JSON only):
{{
  "assignments": [
    {{"doc_index": 0, "category_index": 2}},
    {{"doc_index": 1, "category_index": 0}},
    ...
  ]
}}

RULES:
- Assign at least 80% of documents to categories 0-{len(categories)-1}
- Use category {len(categories)} (Other) for less than 20% of documents
- Be generous with category matching - use broad interpretation
- Return ONLY valid JSON
"""

        try:
            if hasattr(provider, 'extract_biblio'):
                result = _call_openai_classify(provider, prompt, log)
            else:
                result = _call_ollama_classify(provider, prompt, log)

            if result and "assignments" in result:
                for item in result["assignments"]:
                    doc_idx = item.get("doc_index")
                    cat_idx = item.get("category_index")

                    if doc_idx is not None and 0 <= doc_idx < len(batch):
                        record_id = batch[doc_idx]["record_id"]

                        if cat_idx is not None and 0 <= cat_idx < len(categories):
                            assignment[record_id] = categories[cat_idx]["name"]
                        else:
                            assignment[record_id] = None  # Uncategorized
            else:
                log.warning(f"Invalid assignment result for batch {batch_start//batch_size + 1}")
                # Mark all as uncategorized
                for rec in batch:
                    assignment[rec["record_id"]] = None

        except Exception as e:
            log.error(f"Assignment failed for batch {batch_start//batch_size + 1}: {e}")
            # Mark all as uncategorized
            for rec in batch:
                assignment[rec["record_id"]] = None

    return assignment


def _call_openai_classify(provider, prompt: str, log: logging.Logger) -> Optional[Dict[str, Any]]:
    """Call OpenAI SDK provider for classification."""
    import os
    from openai import OpenAI
    import httpx
    from .providers import _extract_json_object

    api_key = os.getenv(provider.api_key_env) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.error(f"Missing API key: {provider.api_key_env}")
        return None

    client = OpenAI(
        api_key=api_key,
        base_url=provider.base_url,
        timeout=provider.timeout,
        http_client=httpx.Client(trust_env=provider.trust_env),
    )

    system = "You are a document classification expert. Return ONLY valid JSON."

    try:
        resp = client.chat.completions.create(
            model=provider.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Slightly higher for creative category naming
        )
        content = (resp.choices[0].message.content or "").strip()
        result = _extract_json_object(content)
        return result
    except Exception as e:
        log.error(f"OpenAI classification call failed: {e}")
        return None


def _call_ollama_classify(provider, prompt: str, log: logging.Logger) -> Optional[Dict[str, Any]]:
    """Call Ollama provider for classification."""
    import requests
    from .providers import _extract_json_object

    # Detect which stage based on prompt content
    if "generate" in prompt.lower() and "category definitions" in prompt.lower():
        # Stage 1: Category generation
        schema = {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            "required": ["categories"]
        }
    else:
        # Stage 2: Document assignment
        schema = {
            "type": "object",
            "properties": {
                "assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "doc_index": {"type": "integer"},
                            "category_index": {"type": "integer"}
                        },
                        "required": ["doc_index", "category_index"]
                    }
                }
            },
            "required": ["assignments"]
        }

    payload = {
        "model": provider.model,
        "messages": [{"role": "user", "content": prompt}],
        "format": schema,
        "stream": False,
        "options": {"num_ctx": provider.num_ctx}
    }

    url = provider.base_url.rstrip("/") + "/api/chat"

    try:
        r = requests.post(url, json=payload, timeout=provider.timeout)
        if r.status_code != 200:
            log.error(f"Ollama API error: {r.status_code}")
            return None

        content = r.json()["message"]["content"]
        if isinstance(content, str):
            result = _extract_json_object(content)
        else:
            result = content

        return result
    except Exception as e:
        log.error(f"Ollama classification call failed: {e}")
        return None


def sanitize_category_name(name: str) -> str:
    """
    Sanitize category name to be filesystem-safe.

    Args:
        name: Original category name

    Returns:
        Sanitized name safe for directory creation
    """
    # Replace spaces and ampersands with underscores
    name = name.replace(" ", "_")
    name = name.replace("&", "_")

    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, "")

    # Remove multiple consecutive underscores
    while "__" in name:
        name = name.replace("__", "_")

    # Remove leading/trailing dots, spaces, and underscores
    name = name.strip(". _")

    # Limit length
    if len(name) > 50:
        name = name[:50]

    # Ensure not empty
    if not name:
        name = "Uncategorized"

    return name


def _add_category_keyword(ris_content: str, category: str) -> str:
    """
    Add category as keyword to RIS content.

    Inserts "KW  - Category: <category>" before the ER tag.

    Args:
        ris_content: Original RIS content
        category: Category name to add

    Returns:
        Modified RIS content with category keyword
    """
    lines = ris_content.split('\n')
    result = []

    for line in lines:
        if line.strip() == "ER  -":
            # Insert category keyword before ER tag
            result.append(f"KW  - Category: {category}")
        result.append(line)

    return '\n'.join(result)


def copy_ris_to_categories(
    classification: Dict[str, Any],
    records: List[Dict[str, Any]],
    ris_dir: pathlib.Path,
    output_dir: pathlib.Path,
    log: logging.Logger,
    add_category_keyword: bool = True
) -> None:
    """
    Merge RIS files by category into single files.

    Each category gets one RIS file containing all records in that category.
    File naming: <category_name>.ris (e.g., Genomics.ris, Neuroscience.ris)

    Args:
        classification: Classification result from classify_with_llm
        records: List of metadata dicts
        ris_dir: Source directory containing RIS files
        output_dir: Base output directory (will create out_ris_class subdirectory)
        log: Logger instance
        add_category_keyword: If True, add category as keyword to each RIS record for Smart Groups
    """
    log.info("Merging RIS files by category...")

    # Create base classification directory
    class_dir = output_dir / "out_ris_class"
    class_dir.mkdir(parents=True, exist_ok=True)

    # Create record_id to record mapping
    record_map = {r["record_id"]: r for r in records}

    # Process each category
    categories = classification.get("categories", [])
    total_records = 0

    for cat in categories:
        cat_name = sanitize_category_name(cat["name"])
        record_ids = cat.get("record_ids", [])

        if not record_ids:
            continue

        log.info(f"Category '{cat_name}': merging {len(record_ids)} documents")

        # Merge all RIS files for this category
        merged_ris_path = class_dir / f"{cat_name}.ris"
        merged_content = []

        for record_id in record_ids:
            record = record_map.get(record_id)
            if not record:
                continue

            ris_filename = record["ris_filename"]
            src_path = ris_dir / ris_filename

            if src_path.exists():
                try:
                    with open(src_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and add_category_keyword:
                            # Add category as keyword before ER tag
                            content = _add_category_keyword(content, cat_name)
                        if content:
                            merged_content.append(content)
                            total_records += 1
                except Exception as e:
                    log.warning(f"Failed to read {ris_filename}: {e}")
            else:
                log.warning(f"RIS file not found: {src_path}")

        # Write merged RIS file
        if merged_content:
            try:
                with open(merged_ris_path, 'w', encoding='utf-8') as f:
                    # Join records with double newline separator
                    f.write("\n\n".join(merged_content))
                    f.write("\n")
                log.info(f"  -> Created {merged_ris_path.name} with {len(merged_content)} records")
            except Exception as e:
                log.error(f"Failed to write merged RIS file {merged_ris_path}: {e}")

    # Handle uncategorized documents
    uncategorized = classification.get("uncategorized", [])
    if uncategorized:
        log.info(f"Category 'Uncategorized': merging {len(uncategorized)} documents")

        merged_ris_path = class_dir / "Uncategorized.ris"
        merged_content = []

        for record_id in uncategorized:
            record = record_map.get(record_id)
            if not record:
                continue

            ris_filename = record["ris_filename"]
            src_path = ris_dir / ris_filename

            if src_path.exists():
                try:
                    with open(src_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and add_category_keyword:
                            # Add "Uncategorized" as keyword
                            content = _add_category_keyword(content, "Uncategorized")
                        if content:
                            merged_content.append(content)
                            total_records += 1
                except Exception as e:
                    log.warning(f"Failed to read {ris_filename}: {e}")

        # Write merged uncategorized RIS file
        if merged_content:
            try:
                with open(merged_ris_path, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(merged_content))
                    f.write("\n")
                log.info(f"  -> Created {merged_ris_path.name} with {len(merged_content)} records")
            except Exception as e:
                log.error(f"Failed to write merged RIS file {merged_ris_path}: {e}")

    log.info(f"Classification complete: {total_records} records merged into {len(categories) + (1 if uncategorized else 0)} RIS files")

    # Save classification report
    report_path = class_dir / "classification_report.json"
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_documents": len(records),
        "num_categories": len(categories),
        "categories": [
            {
                "name": cat["name"],
                "description": cat.get("description", ""),
                "count": len(cat.get("record_ids", []))
            }
            for cat in categories
        ],
        "uncategorized_count": len(uncategorized)
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    log.info(f"Classification report saved to {report_path}")

    # Generate EndNote import guide
    if add_category_keyword:
        _generate_endnote_import_guide(class_dir, categories, log)
        _generate_auto_import_script(class_dir, categories, log)


def _generate_endnote_import_guide(class_dir: pathlib.Path, categories: List[Dict], log: logging.Logger) -> None:
    """
    Generate a guide for importing classified RIS files into EndNote with Smart Groups.

    Args:
        class_dir: Directory containing classified RIS files
        categories: List of category dicts
        log: Logger instance
    """
    guide_path = class_dir / "EndNote_Import_Guide.txt"

    guide_content = """
═══════════════════════════════════════════════════════════════════════════
EndNote Import Guide - Automatic Grouping with Smart Groups
═══════════════════════════════════════════════════════════════════════════

This guide shows you how to import all classified documents into EndNote at once
and automatically create groups using Smart Groups feature.

STEP 1: Import All RIS Files at Once
─────────────────────────────────────────────────────────────────────────────
1. In EndNote, go to: File → Import → File
2. Click "Choose File" and select ALL .ris files in this directory
   (You can select multiple files by holding Ctrl/Cmd)
3. Import Option: Select "RefMan (RIS)"
4. Duplicates: Choose your preference
5. Click "Import"

All documents will be imported with category keywords (e.g., "Category: Genomics")

STEP 2: Create Smart Groups for Automatic Categorization
─────────────────────────────────────────────────────────────────────────────
Smart Groups automatically include references based on search criteria.

For each category below, create a Smart Group:

1. In EndNote, go to: Groups → Create Smart Group
2. Name the group (e.g., "Genomics")
3. Set the search criteria:
   - Field: Keywords
   - Condition: Contains
   - Value: Category: <category_name>
4. Click "Create"

CATEGORIES TO CREATE:
─────────────────────────────────────────────────────────────────────────────
"""

    for i, cat in enumerate(categories, 1):
        cat_name = cat["name"]
        count = len(cat.get("record_ids", []))
        guide_content += f"{i}. Group Name: {cat_name}\n"
        guide_content += f"   Search: Keywords Contains \"Category: {cat_name}\"\n"
        guide_content += f"   Expected: {count} documents\n\n"

    guide_content += """
ALTERNATIVE: Import Each Category Separately (Manual Method)
─────────────────────────────────────────────────────────────────────────────
If you prefer manual groups instead of Smart Groups:

1. Create a group in EndNote (Groups → Create Group)
2. Import the corresponding .ris file
3. Select all imported references
4. Right-click → Add References to → [Your Group]
5. Repeat for each category

═══════════════════════════════════════════════════════════════════════════
TIPS:
─────────────────────────────────────────────────────────────────────────────
• Smart Groups update automatically when you add/remove references
• You can view all category keywords by checking the Keywords field
• To remove category keywords: Edit → Find and Replace → Keywords field
• Smart Groups are saved with your EndNote library

═══════════════════════════════════════════════════════════════════════════
"""

    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        log.info(f"EndNote import guide saved to {guide_path}")
    except Exception as e:
        log.error(f"Failed to write import guide: {e}")


def _generate_auto_import_script(class_dir: pathlib.Path, categories: List[Dict], log: logging.Logger) -> None:
    """
    Generate Python script for automatic EndNote import.

    Args:
        class_dir: Directory containing classified RIS files
        categories: List of category dicts
        log: Logger instance
    """
    script_path = class_dir / "auto_import_to_endnote.py"

    # Get the path to the auto import script template
    import pathlib as pl
    template_path = pl.Path(__file__).parent.parent / "scripts" / "endnote" / "endnote_auto_import.py"

    if not template_path.exists():
        log.warning(f"Auto import script template not found: {template_path}")
        return

    try:
        # Copy the template script
        import shutil
        shutil.copy2(template_path, script_path)
        log.info(f"Auto import script saved to {script_path}")

        # Generate a simple batch file for Windows
        batch_path = class_dir / "auto_import_to_endnote.bat"
        batch_content = """@echo off
REM EndNote Auto Import Batch Script
REM This script automatically imports all classified RIS files into EndNote

echo ========================================
echo EndNote Auto Import
echo ========================================
echo.
echo This script will:
echo 1. Connect to EndNote
echo 2. Import all RIS files in this directory
echo 3. Create custom groups for each category
echo.
echo Make sure EndNote is installed and closed before running this script.
echo.
pause

REM Run the Python script (. means current directory)
python auto_import_to_endnote.py .

echo.
echo ========================================
echo Import Complete
echo ========================================
echo.
pause
"""

        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        log.info(f"Batch script saved to {batch_path}")

        # Generate README for the auto import
        readme_path = class_dir / "AUTO_IMPORT_README.txt"
        readme_content = f"""
═══════════════════════════════════════════════════════════════════════════
EndNote Auto Import - Quick Start Guide
═══════════════════════════════════════════════════════════════════════════

OPTION 1: Automatic Import (Recommended) ⭐
─────────────────────────────────────────────────────────────────────────────
Use the Python script to automatically import all files and create groups.

REQUIREMENTS:
• Windows OS
• EndNote installed
• Python with pywin32 package (pip install pywin32)

STEPS:
1. Close EndNote if it's currently open
2. Double-click: auto_import_to_endnote.bat
   OR run: python auto_import_to_endnote.py "{class_dir.resolve()}"
3. Follow the prompts
4. Open EndNote to see your imported references and groups

The script will:
✓ Import all {len(categories)} category RIS files
✓ Create custom groups automatically
✓ Organize references by category

OPTION 2: Manual Import with Smart Groups
─────────────────────────────────────────────────────────────────────────────
See: EndNote_Import_Guide.txt for detailed manual import instructions.

═══════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════

If auto import fails:
1. Make sure pywin32 is installed: pip install pywin32
2. Try opening EndNote manually first
3. Check if EndNote is registered in Windows COM
4. Fall back to manual import (see EndNote_Import_Guide.txt)

If groups are empty:
1. Check the Keywords field in your references
2. Make sure they have "Category: XXX" keywords
3. Manually search for "Category: XXX" in EndNote
4. Create Smart Groups manually (see guide)

═══════════════════════════════════════════════════════════════════════════
"""

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        log.info(f"Auto import README saved to {readme_path}")

    except Exception as e:
        log.error(f"Failed to generate auto import script: {e}")


def auto_classify_documents(
    out_dir: pathlib.Path,
    num_categories: int,
    provider,
    log: logging.Logger,
    predefined_categories: Optional[List[str]] = None
) -> None:
    """
    Main function to automatically classify all documents.

    Args:
        out_dir: Output directory containing out_intermediate and out_ris
        num_categories: Target number of categories (including predefined ones)
        provider: LLM provider instance
        log: Logger instance
        predefined_categories: Optional list of user-specified category names
    """
    log.info("="*80)
    log.info("Starting automatic document classification")
    log.info("="*80)

    intermediate_dir = out_dir / "out_intermediate"
    ris_dir = out_dir / "out_ris"

    # Step 1: Collect metadata
    records = collect_metadata(intermediate_dir, log)
    if not records:
        log.error("No records found for classification")
        return

    # Step 2: Classify with LLM
    classification = classify_with_llm(
        records,
        num_categories,
        provider,
        log,
        predefined_categories=predefined_categories
    )

    # Step 3: Copy files to categorized directories
    copy_ris_to_categories(classification, records, ris_dir, out_dir, log)

    log.info("="*80)
    log.info("Automatic classification completed")
    log.info("="*80)
