"""
Intelligent Supplement Detection and Merging

This module uses LLM to identify supplement materials and merge them
into their corresponding main papers.

Strategy:
1. Identify potential supplements by filename patterns (-SE, -SM, -supplement, etc.)
2. Use LLM to identify additional supplements by content analysis
3. Use LLM to match supplements to main papers globally based on:
   - Title similarity
   - Author overlap
   - Content relationship
4. Merge supplements as attachments to main papers
5. Remove supplement RIS files
"""

from __future__ import annotations
import pathlib
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import logging


# Supplement filename patterns
SUPPLEMENT_PATTERNS = [
    r'[-_]SE\b',           # -SE (Supplementary)
    r'[-_]SM\b',           # -SM (Supplementary Material)
    r'[-_]SI\b',           # -SI (Supporting Information)
    r'[-_]supplement',     # -supplement
    r'[-_]supplementary',  # -supplementary
    r'[-_]supporting',     # -supporting
    r'[-_]supp\b',         # -supp
    r'[-_]appendix',       # -appendix
    r'\bsupplement',       # supplement (word boundary)
    r'\bsupplementary',    # supplementary
    r'\bsupporting',       # supporting
]


def looks_like_supplement(filename: str) -> bool:
    """
    Check if filename looks like a supplement based on patterns.

    Args:
        filename: Filename to check (without extension)

    Returns:
        True if filename matches supplement patterns
    """
    filename_lower = filename.lower()

    for pattern in SUPPLEMENT_PATTERNS:
        if re.search(pattern, filename_lower, re.IGNORECASE):
            return True

    return False


def load_ris_metadata(ris_dir: pathlib.Path, intermediate_dir: pathlib.Path, log: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load metadata for all RIS files.

    Args:
        ris_dir: Directory containing RIS files
        intermediate_dir: Directory containing intermediate JSON files
        log: Logger instance

    Returns:
        List of metadata dicts with keys:
        - record_id: Record ID
        - ris_filename: RIS filename
        - ris_path: Full path to RIS file
        - json_path: Full path to intermediate JSON
        - title: Paper title
        - authors: List of authors
        - year: Publication year
        - abstract: Abstract text
        - primary: Primary file path
        - attachments: List of attachment paths
        - is_potential_supplement_by_filename: Boolean flag based on filename
    """
    records = []

    # Load all intermediate JSON files
    for json_file in intermediate_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            record_id = data.get("record_id")
            if not record_id:
                continue

            # Find corresponding RIS file
            ris_files = list(ris_dir.glob(f"*{record_id[:8]}.ris"))
            if not ris_files:
                log.warning(f"No RIS file found for record {record_id}")
                continue

            ris_path = ris_files[0]

            # Extract metadata
            meta = data.get("meta", {})
            primary = data.get("primary")

            # Check if this looks like a supplement by filename
            is_supplement_filename = False
            if primary:
                primary_name = pathlib.Path(primary).stem
                is_supplement_filename = looks_like_supplement(primary_name)

            record = {
                "record_id": record_id,
                "ris_filename": ris_path.name,
                "ris_path": ris_path,
                "json_path": json_file,
                "title": meta.get("title"),
                "authors": meta.get("authors", []),
                "year": meta.get("year"),
                "abstract": meta.get("abstract"),
                "primary": primary,
                "attachments": data.get("attachments", []),
                "attachment_absolute_paths": data.get("attachment_absolute_paths", []),
                "is_potential_supplement_by_filename": is_supplement_filename,
            }

            records.append(record)

        except Exception as e:
            log.warning(f"Failed to load {json_file}: {e}")

    log.info(f"Loaded {len(records)} records")
    potential_supplements = sum(1 for r in records if r["is_potential_supplement_by_filename"])
    log.info(f"Found {potential_supplements} potential supplements based on filename patterns")

    return records


def identify_supplements_with_llm(
    records: List[Dict[str, Any]],
    provider,
    log: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Phase 1: Use LLM to identify which documents are supplements.

    Args:
        records: List of all record metadata dicts
        provider: LLM provider instance
        log: Logger instance

    Returns:
        List of supplement records with detection info
    """
    log.info(f"Phase 1: Identifying supplements from {len(records)} records...")

    # Start with filename-based supplements
    supplements = []
    for rec in records:
        if rec["is_potential_supplement_by_filename"]:
            supplements.append({
                "record": rec,
                "detection_method": "filename",
            })

    log.info(f"  - Found {len(supplements)} supplements by filename patterns")

    # Use LLM to identify additional supplements by content
    # Process in batches
    batch_size = 50
    content_supplements = []

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]

        # Prepare document info
        doc_info = []
        for idx, rec in enumerate(batch):
            title = (rec["title"] or "Unknown")[:300]
            abstract = (rec["abstract"] or "")[:500]
            authors_str = ", ".join(rec["authors"][:5]) if rec["authors"] else "Unknown"
            filename = pathlib.Path(rec["primary"]).name if rec["primary"] else "Unknown"

            doc_info.append({
                "index": idx,
                "record_id": rec["record_id"],
                "title": title,
                "abstract": abstract,
                "authors": authors_str,
                "year": rec["year"],
                "filename": filename,
                "is_supplement_by_filename": rec["is_potential_supplement_by_filename"]
            })

        prompt = f"""You are a bibliographic expert. Identify which of these documents are supplementary materials.

DOCUMENTS:
{json.dumps(doc_info, ensure_ascii=False, indent=2)}

Your task: Identify supplements based on:
1. Filename patterns (already flagged with is_supplement_by_filename=true)
2. Title content (contains "supplement", "supporting information", "supplementary data", "appendix", etc.)
3. Abstract content (describes supplementary data, additional materials, methods, etc.)

IMPORTANT: Be LIBERAL in identifying supplements. If there's ANY indication a document is supplementary material, mark it as a supplement.

Return a JSON array of supplement indices. Each entry should have:
- index: Document index (0-based)
- is_supplement: true
- reason: Brief explanation
- confidence: "high" or "medium"

Example:
[
  {{"index": 2, "is_supplement": true, "reason": "Title contains 'Supplementary Information'", "confidence": "high"}},
  {{"index": 5, "is_supplement": true, "reason": "Filename pattern -SM", "confidence": "high"}}
]

Return ONLY the JSON array, no markdown, no extra text. If no supplements found, return [].
"""

        try:
            response_text = call_llm(provider, prompt, log)
            if not response_text:
                continue

            # Parse response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                llm_results = json.loads(json_match.group())
                for result in llm_results:
                    idx = result.get("index")
                    if idx is not None and result.get("is_supplement"):
                        rec = batch[idx]
                        # Skip if already identified by filename
                        if not rec["is_potential_supplement_by_filename"]:
                            content_supplements.append({
                                "record": rec,
                                "detection_method": "content",
                                "reason": result.get("reason", ""),
                                "confidence": result.get("confidence", "medium")
                            })

        except Exception as e:
            log.error(f"LLM identification failed for batch {i//batch_size + 1}: {e}")

    log.info(f"  - Found {len(content_supplements)} additional supplements by content analysis")

    # Combine all supplements
    all_supplements = supplements + content_supplements
    log.info(f"Total supplements identified: {len(all_supplements)}")

    return all_supplements


def match_supplements_to_main_papers(
    supplements: List[Dict[str, Any]],
    all_records: List[Dict[str, Any]],
    provider,
    log: logging.Logger
) -> List[Tuple[str, str]]:
    """
    Phase 2: Match each supplement to its main paper globally.

    Args:
        supplements: List of identified supplement dicts
        all_records: List of all record metadata dicts
        provider: LLM provider instance
        log: Logger instance

    Returns:
        List of (supplement_record_id, main_record_id) tuples
    """
    if not supplements:
        return []

    log.info(f"Phase 2: Matching {len(supplements)} supplements to main papers...")

    matches = []

    # Create a lookup for all records
    record_dict = {r["record_id"]: r for r in all_records}

    # Process supplements in batches
    batch_size = 10  # Smaller batch for matching

    for i in range(0, len(supplements), batch_size):
        supp_batch = supplements[i:i+batch_size]

        # Prepare supplement info
        supp_info = []
        for idx, supp_dict in enumerate(supp_batch):
            rec = supp_dict["record"]
            title = (rec["title"] or "Unknown")[:300]
            abstract = (rec["abstract"] or "")[:500]
            authors_str = ", ".join(rec["authors"][:5]) if rec["authors"] else "Unknown"
            filename = pathlib.Path(rec["primary"]).name if rec["primary"] else "Unknown"

            supp_info.append({
                "index": idx,
                "record_id": rec["record_id"],
                "title": title,
                "abstract": abstract,
                "authors": authors_str,
                "year": rec["year"],
                "filename": filename
            })

        # Prepare candidate main papers (all non-supplement records)
        supplement_ids = {s["record"]["record_id"] for s in supplements}
        main_candidates = [r for r in all_records if r["record_id"] not in supplement_ids]

        # Sample main candidates if too many
        if len(main_candidates) > 100:
            # Prioritize candidates with similar years
            supp_years = {s["record"]["record_id"]: s["record"].get("year") for s in supp_batch}
            scored_candidates = []
            for cand in main_candidates:
                score = 0
                cand_year = cand.get("year")
                if cand_year:
                    for supp_year in supp_years.values():
                        if supp_year and str(cand_year) == str(supp_year):
                            score += 10
                scored_candidates.append((score, cand))
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            main_candidates = [c for _, c in scored_candidates[:100]]

        main_info = []
        for idx, rec in enumerate(main_candidates):
            title = (rec["title"] or "Unknown")[:300]
            authors_str = ", ".join(rec["authors"][:5]) if rec["authors"] else "Unknown"

            main_info.append({
                "index": idx,
                "record_id": rec["record_id"],
                "title": title,
                "authors": authors_str,
                "year": rec["year"]
            })

        prompt = f"""You are a bibliographic expert. Match these supplementary materials to their main papers.

SUPPLEMENTS:
{json.dumps(supp_info, ensure_ascii=False, indent=2)}

CANDIDATE MAIN PAPERS:
{json.dumps(main_info, ensure_ascii=False, indent=2)}

Your task: For each supplement, find its corresponding main paper based on:
1. Title similarity (supplements often reference the main paper title or have similar titles)
2. Author overlap (same or overlapping authors)
3. Publication year (same year)
4. Filename similarity (e.g., "scGPT-supplementary" matches "scGPT")

IMPORTANT: Be LIBERAL in matching. Even if the match is not perfect, if there's a reasonable connection, make the match.

Return a JSON array of matches. Each entry should have:
- supplement_index: Index of supplement (0-based, from SUPPLEMENTS list)
- main_index: Index of main paper (0-based, from CANDIDATE MAIN PAPERS list)
- confidence: "high" or "medium"
- reason: Brief explanation

Example:
[
  {{"supplement_index": 0, "main_index": 5, "confidence": "high", "reason": "Filename 'scGPT-supplementary' matches 'scGPT' and same authors"}},
  {{"supplement_index": 1, "main_index": 12, "confidence": "medium", "reason": "Same authors and year, similar research topic"}}
]

Return ONLY the JSON array, no markdown, no extra text. If no matches found, return [].
"""

        try:
            response_text = call_llm(provider, prompt, log)
            if not response_text:
                continue

            # Parse response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                llm_matches = json.loads(json_match.group())
                for match in llm_matches:
                    supp_idx = match.get("supplement_index")
                    main_idx = match.get("main_index")
                    confidence = match.get("confidence", "medium")
                    reason = match.get("reason", "")

                    if supp_idx is None or main_idx is None:
                        continue

                    # Only accept high and medium confidence
                    if confidence not in ["high", "medium"]:
                        continue

                    if supp_idx >= len(supp_batch) or main_idx >= len(main_candidates):
                        continue

                    supplement_record_id = supp_batch[supp_idx]["record"]["record_id"]
                    main_record_id = main_candidates[main_idx]["record_id"]

                    matches.append((supplement_record_id, main_record_id))

                    detection_method = supp_batch[supp_idx].get("detection_method", "unknown")
                    log.info(f"  [{detection_method}] Matched supplement {supplement_record_id} to main paper {main_record_id}")
                    log.info(f"    Confidence: {confidence}, Reason: {reason}")

        except Exception as e:
            log.error(f"LLM matching failed for batch {i//batch_size + 1}: {e}")
            import traceback
            traceback.print_exc()

    log.info(f"Found {len(matches)} supplement-to-main matches")
    return matches


def call_llm(provider, prompt: str, log: logging.Logger) -> Optional[str]:
    """
    Call LLM with the given prompt.

    Args:
        provider: LLM provider instance
        prompt: Prompt text
        log: Logger instance

    Returns:
        Response text or None if failed
    """
    try:
        import requests
        import os

        # Determine provider type and call appropriately
        if hasattr(provider, 'model') and hasattr(provider, 'base_url'):
            # OpenAI SDK provider
            from openai import OpenAI
            import httpx

            api_key = os.getenv(provider.api_key_env) or os.getenv("OPENAI_API_KEY")
            if not api_key:
                log.warning(f"Missing API key for LLM provider")
                return None

            client = OpenAI(
                api_key=api_key,
                base_url=provider.base_url,
                timeout=provider.timeout,
                http_client=httpx.Client(trust_env=provider.trust_env),
            )

            resp = client.chat.completions.create(
                model=provider.model,
                messages=[
                    {"role": "system", "content": "You are a bibliographic expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            return (resp.choices[0].message.content or "").strip()

        else:
            # Ollama provider
            url = provider.base_url.rstrip("/") + "/api/chat"
            payload = {
                "model": provider.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            r = requests.post(url, json=payload, timeout=provider.timeout)
            if r.status_code != 200:
                log.warning(f"LLM request failed with status {r.status_code}")
                return None
            return r.json()["message"]["content"]

    except Exception as e:
        log.error(f"LLM call failed: {e}")
        return None


def merge_supplements(
    matches: List[Tuple[str, str]],
    records: List[Dict[str, Any]],
    ris_dir: pathlib.Path,
    intermediate_dir: pathlib.Path,
    log: logging.Logger
) -> int:
    """
    Merge supplements into main papers.

    Args:
        matches: List of (supplement_record_id, main_record_id) tuples
        records: List of all record metadata
        ris_dir: Directory containing RIS files
        intermediate_dir: Directory containing intermediate JSON files
        log: Logger instance

    Returns:
        Number of supplements merged
    """
    if not matches:
        return 0

    log.info(f"Merging {len(matches)} supplements into main papers...")

    # Create lookup dict
    record_dict = {r["record_id"]: r for r in records}

    merged_count = 0

    for supp_id, main_id in matches:
        try:
            supp_record = record_dict.get(supp_id)
            main_record = record_dict.get(main_id)

            if not supp_record or not main_record:
                log.warning(f"Could not find records for {supp_id} -> {main_id}")
                continue

            # Load main paper's intermediate JSON
            with open(main_record["json_path"], 'r', encoding='utf-8') as f:
                main_data = json.load(f)

            # Add supplement's attachments to main paper
            supp_attachments = supp_record.get("attachment_absolute_paths", [])
            if not supp_attachments:
                supp_attachments = supp_record.get("attachments", [])

            if supp_attachments:
                main_data.setdefault("attachment_absolute_paths", []).extend(supp_attachments)
                main_data.setdefault("attachments", []).extend(supp_record.get("attachments", []))

                # Save updated main paper JSON
                with open(main_record["json_path"], 'w', encoding='utf-8') as f:
                    json.dump(main_data, f, ensure_ascii=False, indent=2)

                log.info(f"  Added {len(supp_attachments)} attachments from {supp_id} to {main_id}")

            # Regenerate main paper's RIS file with new attachments
            from zr.ris_export import to_ris_folder_record

            meta = main_data.get("meta", {})
            attachment_paths = [pathlib.Path(p) for p in main_data.get("attachment_absolute_paths", [])]
            primary = main_data.get("primary")
            primary_reason = main_data.get("primary_reason", "unknown")

            # Get category if exists
            category = None
            for kw in meta.get("keywords", []):
                if isinstance(kw, str) and kw.startswith("Category: "):
                    category = kw.replace("Category: ", "")
                    break

            ris_text = to_ris_folder_record(
                meta,
                attachment_paths,
                pathlib.Path(primary).stem if primary else "Unknown",
                primary_reason,
                category
            )

            # Save updated RIS
            main_record["ris_path"].write_text(ris_text, encoding="utf-8")
            log.info(f"  Updated RIS file for {main_id}")

            # Delete supplement's RIS and JSON files
            supp_record["ris_path"].unlink()
            supp_record["json_path"].unlink()
            log.info(f"  Deleted supplement files for {supp_id}")

            merged_count += 1

        except Exception as e:
            log.error(f"Failed to merge {supp_id} into {main_id}: {e}")
            import traceback
            traceback.print_exc()

    log.info(f"Successfully merged {merged_count} supplements")
    return merged_count


def detect_and_merge_supplements(
    out_dir: pathlib.Path,
    provider,
    log: logging.Logger
) -> int:
    """
    Main function to detect and merge supplement materials.

    Two-phase approach:
    1. Identify all supplements (filename + content analysis)
    2. Match each supplement to its main paper globally

    Args:
        out_dir: Output directory containing RIS and intermediate files
        provider: LLM provider instance
        log: Logger instance

    Returns:
        Number of supplements merged
    """
    log.info("")
    log.info("=" * 80)
    log.info("Detecting and Merging Supplement Materials")
    log.info("=" * 80)

    ris_dir = out_dir / "out_ris"
    intermediate_dir = out_dir / "out_intermediate"

    if not ris_dir.exists() or not intermediate_dir.exists():
        log.warning("RIS or intermediate directory not found, skipping supplement detection")
        return 0

    # Step 1: Load all records
    records = load_ris_metadata(ris_dir, intermediate_dir, log)

    if not records:
        log.warning("No records found")
        return 0

    # Step 2: Identify all supplements
    supplements = identify_supplements_with_llm(records, provider, log)

    if not supplements:
        log.info("No supplements identified")
        return 0

    # Step 3: Match supplements to main papers
    matches = match_supplements_to_main_papers(supplements, records, provider, log)

    if not matches:
        log.info("No supplement matches found")
        return 0

    # Step 4: Merge supplements into main papers
    merged_count = merge_supplements(matches, records, ris_dir, intermediate_dir, log)

    log.info("")
    log.info("=" * 80)
    log.info(f"Supplement Detection Complete: {merged_count} supplements merged")
    log.info("=" * 80)

    return merged_count
