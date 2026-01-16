#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation tool for checking RIS output quality.

Usage:
    python validate_output.py outputs/out_ris
    python validate_output.py outputs/out_intermediate
"""

from __future__ import annotations
import pathlib
import json
import sys
from collections import defaultdict


class OutputValidator:
    """Validate RIS and JSON output quality."""

    def __init__(self):
        self.stats = {
            "total": 0,
            "with_abstract": 0,
            "with_doi": 0,
            "with_authors": 0,
            "with_year": 0,
            "with_journal": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "record_types": defaultdict(int),
            "flags": defaultdict(int),
        }
        self.issues = []

    def validate_json_file(self, json_path: pathlib.Path):
        """Validate a single JSON intermediate file."""
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            meta = data.get("meta", {})

            self.stats["total"] += 1

            # Check fields
            if meta.get("abstract"):
                self.stats["with_abstract"] += 1
                abstract_len = len(str(meta["abstract"]))
                if abstract_len < 50:
                    self.issues.append({
                        "file": json_path.name,
                        "issue": "abstract_too_short",
                        "detail": f"Abstract only {abstract_len} chars"
                    })
            else:
                self.issues.append({
                    "file": json_path.name,
                    "issue": "missing_abstract",
                    "detail": "No abstract found"
                })

            if meta.get("doi"):
                self.stats["with_doi"] += 1

            if meta.get("authors"):
                self.stats["with_authors"] += 1
            else:
                self.issues.append({
                    "file": json_path.name,
                    "issue": "missing_authors",
                    "detail": "No authors found"
                })

            if meta.get("year"):
                self.stats["with_year"] += 1

            if meta.get("journal"):
                self.stats["with_journal"] += 1

            # Check confidence
            confidence = meta.get("confidence", 0.0)
            if confidence >= 0.7:
                self.stats["high_confidence"] += 1
            elif confidence >= 0.4:
                self.stats["medium_confidence"] += 1
            else:
                self.stats["low_confidence"] += 1
                self.issues.append({
                    "file": json_path.name,
                    "issue": "low_confidence",
                    "detail": f"Confidence: {confidence:.2f}"
                })

            # Record type
            record_type = meta.get("record_type", "UNKNOWN")
            self.stats["record_types"][record_type] += 1

            # Flags
            for flag in meta.get("flags", []):
                self.stats["flags"][flag] += 1

        except Exception as e:
            self.issues.append({
                "file": json_path.name,
                "issue": "parse_error",
                "detail": str(e)
            })

    def validate_ris_file(self, ris_path: pathlib.Path):
        """Validate a single RIS file."""
        try:
            content = ris_path.read_text(encoding="utf-8")

            # Check for abstract (N2 field)
            has_abstract = "N2  -" in content
            if not has_abstract:
                self.issues.append({
                    "file": ris_path.name,
                    "issue": "missing_abstract_in_ris",
                    "detail": "No N2 (abstract) field in RIS"
                })

            # Check for DOI
            has_doi = "DO  -" in content
            if not has_doi:
                self.issues.append({
                    "file": ris_path.name,
                    "issue": "missing_doi_in_ris",
                    "detail": "No DO (DOI) field in RIS"
                })

            # Check for authors
            has_authors = "AU  -" in content
            if not has_authors:
                self.issues.append({
                    "file": ris_path.name,
                    "issue": "missing_authors_in_ris",
                    "detail": "No AU (authors) field in RIS"
                })

        except Exception as e:
            self.issues.append({
                "file": ris_path.name,
                "issue": "parse_error",
                "detail": str(e)
            })

    def print_report(self):
        """Print validation report."""
        print("=" * 80)
        print("📊 OUTPUT VALIDATION REPORT")
        print("=" * 80)
        print()

        # Overall stats
        print("📈 Overall Statistics:")
        print(f"  Total records:        {self.stats['total']}")
        print()

        # Field coverage
        print("📋 Field Coverage:")
        if self.stats['total'] > 0:
            print(f"  With Abstract:        {self.stats['with_abstract']:4d} ({self.stats['with_abstract']/self.stats['total']*100:5.1f}%)")
            print(f"  With DOI:             {self.stats['with_doi']:4d} ({self.stats['with_doi']/self.stats['total']*100:5.1f}%)")
            print(f"  With Authors:         {self.stats['with_authors']:4d} ({self.stats['with_authors']/self.stats['total']*100:5.1f}%)")
            print(f"  With Year:            {self.stats['with_year']:4d} ({self.stats['with_year']/self.stats['total']*100:5.1f}%)")
            print(f"  With Journal:         {self.stats['with_journal']:4d} ({self.stats['with_journal']/self.stats['total']*100:5.1f}%)")
        print()

        # Confidence distribution
        print("🎯 Confidence Distribution:")
        if self.stats['total'] > 0:
            print(f"  High (≥0.7):          {self.stats['high_confidence']:4d} ({self.stats['high_confidence']/self.stats['total']*100:5.1f}%)")
            print(f"  Medium (0.4-0.7):     {self.stats['medium_confidence']:4d} ({self.stats['medium_confidence']/self.stats['total']*100:5.1f}%)")
            print(f"  Low (<0.4):           {self.stats['low_confidence']:4d} ({self.stats['low_confidence']/self.stats['total']*100:5.1f}%)")
        print()

        # Record types
        if self.stats['record_types']:
            print("📁 Record Types:")
            for rtype, count in sorted(self.stats['record_types'].items(), key=lambda x: -x[1]):
                pct = count / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
                print(f"  {rtype:15s}:     {count:4d} ({pct:5.1f}%)")
            print()

        # Flags
        if self.stats['flags']:
            print("🚩 Flags (Issues):")
            for flag, count in sorted(self.stats['flags'].items(), key=lambda x: -x[1]):
                pct = count / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
                print(f"  {flag:25s}: {count:4d} ({pct:5.1f}%)")
            print()

        # Issues summary
        print("⚠️  Issues Summary:")
        issue_counts = defaultdict(int)
        for issue in self.issues:
            issue_counts[issue["issue"]] += 1

        if issue_counts:
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
                print(f"  {issue_type:30s}: {count:4d}")
        else:
            print("  No issues found! ✓")
        print()

        # Detailed issues (top 20)
        if self.issues:
            print("🔍 Detailed Issues (showing first 20):")
            for i, issue in enumerate(self.issues[:20], 1):
                print(f"  {i}. {issue['file']}")
                print(f"     Issue: {issue['issue']}")
                print(f"     Detail: {issue['detail']}")
                print()

        print("=" * 80)

        # Recommendations
        print()
        print("💡 Recommendations:")
        print()

        abstract_pct = self.stats['with_abstract'] / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
        if abstract_pct < 50:
            print("  ⚠️  Low abstract coverage (<50%)")
            print("     - Check if PDFs contain abstracts")
            print("     - Try increasing --max_pages to extract more text")
            print("     - Enable OCR for scanned PDFs")
            print()

        doi_pct = self.stats['with_doi'] / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
        if doi_pct < 70:
            print("  ⚠️  Low DOI coverage (<70%)")
            print("     - Increase --scan_doi_pages to scan more pages")
            print("     - Some documents may not have DOIs (presentations, notes)")
            print()

        low_conf_pct = self.stats['low_confidence'] / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
        if low_conf_pct > 20:
            print("  ⚠️  High proportion of low-confidence records (>20%)")
            print("     - Review logs for extraction errors")
            print("     - Consider manual review of low-confidence records")
            print("     - Check if OCR is working properly")
            print()

        print("=" * 80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <output_directory>")
        print()
        print("Examples:")
        print("  python validate_output.py outputs/out_intermediate")
        print("  python validate_output.py outputs/out_ris")
        sys.exit(1)

    output_dir = pathlib.Path(sys.argv[1])

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    validator = OutputValidator()

    # Detect file type
    json_files = list(output_dir.glob("*.json"))
    ris_files = list(output_dir.glob("*.ris"))

    if json_files:
        print(f"Validating {len(json_files)} JSON files...")
        for json_file in json_files:
            validator.validate_json_file(json_file)

    elif ris_files:
        print(f"Validating {len(ris_files)} RIS files...")
        for ris_file in ris_files:
            validator.validate_ris_file(ris_file)

    else:
        print(f"Error: No JSON or RIS files found in {output_dir}")
        sys.exit(1)

    # Print report
    validator.print_report()


if __name__ == "__main__":
    main()
