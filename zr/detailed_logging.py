from __future__ import annotations
import time
import traceback
from typing import Any, Callable, Optional
from functools import wraps
from contextlib import contextmanager


class DetailedLogger:
    """
    Enhanced logger with detailed step tracking and timing.
    """
    def __init__(self, base_logger):
        self.log = base_logger
        self.current_record = None
        self.current_step = None
        self.step_start_time = None

    def start_record(self, record_path: str, record_type: str):
        """Start processing a new record."""
        self.current_record = record_path
        self.log.info("=" * 80)
        self.log.info(f"📁 START RECORD: {record_path} (type: {record_type})")
        self.log.info("=" * 80)

    def end_record(self, success: bool, total_time: float):
        """End processing current record."""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.log.info("-" * 80)
        self.log.info(f"{status} | Record: {self.current_record} | Total time: {total_time:.2f}s")
        self.log.info("=" * 80)
        self.current_record = None

    @contextmanager
    def step(self, step_name: str, **context):
        """
        Context manager for tracking individual processing steps.

        Usage:
            with logger.step("PDF Text Extraction", file="paper.pdf"):
                text = extract_text(pdf)
        """
        self.current_step = step_name
        self.step_start_time = time.time()

        # Log step start with context
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        if context_str:
            self.log.info(f"  ▶ STEP: {step_name} ({context_str})")
        else:
            self.log.info(f"  ▶ STEP: {step_name}")

        try:
            yield self
            # Step succeeded
            elapsed = time.time() - self.step_start_time
            self.log.info(f"    ✓ Completed in {elapsed:.2f}s")

        except Exception as e:
            # Step failed
            elapsed = time.time() - self.step_start_time
            self.log.error(f"    ✗ Failed after {elapsed:.2f}s")
            self.log_exception(e, step_name)
            raise

        finally:
            self.current_step = None
            self.step_start_time = None

    def log_exception(self, exception: Exception, context: str = ""):
        """Log detailed exception information."""
        self.log.error("-" * 80)
        self.log.error(f"❌ EXCEPTION: {type(exception).__name__}")
        if context:
            self.log.error(f"   Context: {context}")
        self.log.error(f"   Message: {str(exception)}")
        self.log.error("-" * 80)
        self.log.error("   Stack trace:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                self.log.error(f"   {line}")
        self.log.error("-" * 80)

    def log_data(self, label: str, data: Any, max_length: int = 200):
        """Log data with truncation for readability."""
        if data is None:
            self.log.info(f"    {label}: None")
        elif isinstance(data, str):
            if len(data) > max_length:
                self.log.info(f"    {label}: {data[:max_length]}... ({len(data)} chars total)")
            else:
                self.log.info(f"    {label}: {data}")
        elif isinstance(data, (list, tuple)):
            self.log.info(f"    {label}: {len(data)} items")
            for i, item in enumerate(data[:3]):  # Show first 3 items
                self.log.info(f"      [{i}] {item}")
            if len(data) > 3:
                self.log.info(f"      ... and {len(data) - 3} more")
        elif isinstance(data, dict):
            self.log.info(f"    {label}: {len(data)} keys")
            for key, value in list(data.items())[:5]:  # Show first 5 keys
                if isinstance(value, str) and len(value) > 100:
                    self.log.info(f"      {key}: {value[:100]}...")
                else:
                    self.log.info(f"      {key}: {value}")
            if len(data) > 5:
                self.log.info(f"      ... and {len(data) - 5} more keys")
        else:
            self.log.info(f"    {label}: {data}")

    def log_metadata_quality(self, meta: dict):
        """Log metadata extraction quality assessment."""
        self.log.info("    📊 Metadata Quality Assessment:")

        # Check each field
        fields = {
            "title": meta.get("title"),
            "authors": meta.get("authors"),
            "year": meta.get("year"),
            "journal": meta.get("journal"),
            "doi": meta.get("doi"),
            "abstract": meta.get("abstract"),
        }

        for field, value in fields.items():
            if value:
                if field == "authors":
                    status = f"✓ {len(value)} authors"
                elif field == "abstract":
                    length = len(str(value))
                    status = f"✓ {length} chars"
                    if length < 50:
                        status += " ⚠️ (too short)"
                else:
                    status = f"✓ {value}"
            else:
                status = "✗ Missing"

            self.log.info(f"      {field:12s}: {status}")

        # Calculate and log confidence
        confidence = meta.get("confidence", 0.0)
        if confidence >= 0.7:
            level = "HIGH"
            emoji = "🟢"
        elif confidence >= 0.4:
            level = "MEDIUM"
            emoji = "🟡"
        else:
            level = "LOW"
            emoji = "🔴"

        self.log.info(f"      {'confidence':12s}: {emoji} {confidence:.2f} ({level})")

        # Log flags if any
        flags = meta.get("flags", [])
        if flags:
            self.log.info(f"      {'flags':12s}: {', '.join(flags)}")

    def log_file_info(self, file_path, label: str = "File"):
        """Log detailed file information."""
        import pathlib
        path = pathlib.Path(file_path)

        if not path.exists():
            self.log.warning(f"    {label}: {path.name} (NOT FOUND)")
            return

        size_mb = path.stat().st_size / (1024 * 1024)
        self.log.info(f"    {label}: {path.name}")
        self.log.info(f"      Size: {size_mb:.2f} MB")
        self.log.info(f"      Type: {path.suffix}")
        self.log.info(f"      Path: {path}")

    def log_api_call(self, provider: str, model: str, endpoint: str, attempt: int = 1):
        """Log API call details."""
        self.log.info(f"    🌐 API Call:")
        self.log.info(f"      Provider: {provider}")
        self.log.info(f"      Model: {model}")
        self.log.info(f"      Endpoint: {endpoint}")
        if attempt > 1:
            self.log.info(f"      Attempt: {attempt}")

    def log_ocr_details(self, method: str, pages: int, result_length: int):
        """Log OCR processing details."""
        self.log.info(f"    🔍 OCR Details:")
        self.log.info(f"      Method: {method}")
        self.log.info(f"      Pages processed: {pages}")
        self.log.info(f"      Text extracted: {result_length} chars")

    def log_warning_with_suggestion(self, warning: str, suggestions: list):
        """Log warning with actionable suggestions."""
        self.log.warning(f"    ⚠️  {warning}")
        if suggestions:
            self.log.warning(f"       Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                self.log.warning(f"         {i}. {suggestion}")


def timed_step(step_name: str):
    """
    Decorator for timing function execution.

    Usage:
        @timed_step("PDF Text Extraction")
        def extract_text(pdf_path):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get logger from args/kwargs
            log = kwargs.get('log') or (args[0].log if hasattr(args[0], 'log') else None)

            start_time = time.time()

            if log:
                log.info(f"  ▶ {step_name}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                if log:
                    log.info(f"    ✓ Completed in {elapsed:.2f}s")

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                if log:
                    log.error(f"    ✗ Failed after {elapsed:.2f}s: {e}")

                raise

        return wrapper
    return decorator


class PerformanceMonitor:
    """
    Monitor performance metrics for different operations.
    """
    def __init__(self, log):
        self.log = log
        self.metrics = {}

    def record(self, operation: str, duration: float, success: bool):
        """Record operation metrics."""
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "success": 0,
                "failed": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
            }

        m = self.metrics[operation]
        m["count"] += 1
        if success:
            m["success"] += 1
        else:
            m["failed"] += 1
        m["total_time"] += duration
        m["min_time"] = min(m["min_time"], duration)
        m["max_time"] = max(m["max_time"], duration)

    def get_summary(self) -> dict:
        """Get performance summary."""
        summary = {}
        for op, m in self.metrics.items():
            avg_time = m["total_time"] / m["count"] if m["count"] > 0 else 0
            success_rate = (m["success"] / m["count"] * 100) if m["count"] > 0 else 0

            summary[op] = {
                "count": m["count"],
                "success_rate": f"{success_rate:.1f}%",
                "avg_time": f"{avg_time:.2f}s",
                "min_time": f"{m['min_time']:.2f}s",
                "max_time": f"{m['max_time']:.2f}s",
                "total_time": f"{m['total_time']:.2f}s",
            }

        return summary

    def log_summary(self):
        """Log performance summary."""
        self.log.info("=" * 80)
        self.log.info("📊 PERFORMANCE SUMMARY")
        self.log.info("=" * 80)

        summary = self.get_summary()
        for operation, stats in summary.items():
            self.log.info(f"\n{operation}:")
            for key, value in stats.items():
                self.log.info(f"  {key:15s}: {value}")

        self.log.info("=" * 80)
