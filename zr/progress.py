from __future__ import annotations
import time
from typing import Optional


class ProgressTracker:
    """
    Track processing progress and estimate completion time.
    """
    def __init__(self, total: int, log):
        self.total = total
        self.processed = 0
        self.failed = 0
        self.start_time = time.time()
        self.record_times = []
        self.log = log
        self.last_log_time = time.time()
        self.log_interval = 10  # Log every 10 seconds minimum

    def update(self, success: bool, time_taken: float):
        """Update progress after processing one record."""
        self.processed += 1
        if not success:
            self.failed += 1

        self.record_times.append(time_taken)

        # Keep only last 50 records for moving average
        if len(self.record_times) > 50:
            self.record_times.pop(0)

        # Log progress periodically
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self._log_progress()
            self.last_log_time = current_time

    def _log_progress(self):
        """Log current progress and ETA."""
        if self.processed == 0:
            return

        elapsed = time.time() - self.start_time
        percent = (self.processed / self.total) * 100
        success_rate = ((self.processed - self.failed) / self.processed) * 100

        # Calculate ETA
        avg_time = sum(self.record_times) / len(self.record_times)
        remaining = self.total - self.processed
        eta_seconds = remaining * avg_time

        self.log.info(
            f"Progress: {self.processed}/{self.total} ({percent:.1f}%) | "
            f"Success: {success_rate:.1f}% | "
            f"Speed: {1/avg_time:.2f} records/s | "
            f"ETA: {self._format_time(eta_seconds)}"
        )

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def final_summary(self):
        """Log final summary."""
        elapsed = time.time() - self.start_time
        success_count = self.processed - self.failed
        success_rate = (success_count / self.processed * 100) if self.processed > 0 else 0

        self.log.info("=" * 60)
        self.log.info("FINAL SUMMARY")
        self.log.info("=" * 60)
        self.log.info(f"Total records:    {self.total}")
        self.log.info(f"Processed:        {self.processed}")
        self.log.info(f"Successful:       {success_count} ({success_rate:.1f}%)")
        self.log.info(f"Failed:           {self.failed}")
        self.log.info(f"Total time:       {self._format_time(elapsed)}")
        if self.processed > 0:
            self.log.info(f"Average time:     {elapsed/self.processed:.2f}s per record")
        self.log.info("=" * 60)


class ErrorAnalyzer:
    """
    Analyze error patterns and suggest fixes.
    """
    def __init__(self, log):
        self.log = log
        self.error_counts = {}
        self.suggestions_given = set()

    def record_error(self, error_type: str, error_msg: str):
        """Record an error and analyze patterns."""
        # Normalize error message
        key = f"{error_type}:{error_msg[:100]}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Detect patterns and suggest fixes
        if self.error_counts[key] >= 5 and key not in self.suggestions_given:
            self._suggest_fix(error_type, error_msg)
            self.suggestions_given.add(key)

    def _suggest_fix(self, error_type: str, error_msg: str):
        """Suggest fixes based on error patterns."""
        msg_lower = error_msg.lower()

        if "connection" in msg_lower or "timeout" in msg_lower:
            self.log.warning(
                "⚠️  FREQUENT CONNECTION ERRORS DETECTED\n"
                "   Suggestions:\n"
                "   1. Check your network connection\n"
                "   2. Increase timeout: --timeout 1200\n"
                "   3. Switch to local model if using cloud API\n"
                "   4. Check if API endpoint is accessible"
            )
        elif "memory" in msg_lower or "oom" in msg_lower:
            self.log.warning(
                "⚠️  FREQUENT MEMORY ERRORS DETECTED\n"
                "   Suggestions:\n"
                "   1. Close other applications\n"
                "   2. Use smaller model\n"
                "   3. Reduce --max_pages (default: 2)\n"
                "   4. Disable OCR if not needed"
            )
        elif "rate limit" in msg_lower or "429" in msg_lower:
            self.log.warning(
                "⚠️  API RATE LIMIT DETECTED\n"
                "   Suggestions:\n"
                "   1. Slow down processing (add delays)\n"
                "   2. Switch to local Ollama model\n"
                "   3. Upgrade API tier\n"
                "   4. Process in smaller batches"
            )
        elif "json" in msg_lower or "parse" in msg_lower:
            self.log.warning(
                "⚠️  FREQUENT JSON PARSING ERRORS\n"
                "   Suggestions:\n"
                "   1. Model may not support structured output well\n"
                "   2. Try different model\n"
                "   3. Check model compatibility\n"
                "   4. Review logs/openai_raw_*.txt for details"
            )
        elif "pdf" in msg_lower or "corrupt" in msg_lower:
            self.log.warning(
                "⚠️  FREQUENT PDF ERRORS DETECTED\n"
                "   Suggestions:\n"
                "   1. Some PDFs may be corrupted\n"
                "   2. Try --enable_ocr for scanned PDFs\n"
                "   3. Check PDF files manually\n"
                "   4. Skip problematic files with --skip_ok"
            )
        elif "ocr" in msg_lower:
            self.log.warning(
                "⚠️  FREQUENT OCR ERRORS DETECTED\n"
                "   Suggestions:\n"
                "   1. Check if ocrmypdf/tesseract is installed\n"
                "   2. Try vision OCR: --ocr_method vision\n"
                "   3. Check OCR language setting: --ocr_lang eng+chi_sim\n"
                "   4. Some PDFs may be too complex for OCR"
            )

    def get_summary(self) -> dict:
        """Get error summary statistics."""
        total_errors = sum(self.error_counts.values())
        unique_errors = len(self.error_counts)

        # Find most common errors
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_errors": total_errors,
            "unique_errors": unique_errors,
            "top_errors": sorted_errors[:5]
        }
