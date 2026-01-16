from __future__ import annotations
import platform
import shutil
import pathlib
from typing import Optional


def get_system() -> str:
    """Get current operating system."""
    return platform.system()  # "Windows", "Darwin" (macOS), "Linux"


def find_libreoffice() -> Optional[str]:
    """
    Find LibreOffice executable across platforms.

    Returns:
        Path to LibreOffice executable, or None if not found
    """
    system = get_system()

    if system == "Windows":
        # Try common Windows installation paths
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            pathlib.Path.home() / "AppData/Local/Programs/LibreOffice/program/soffice.exe",
        ]

        for path in possible_paths:
            p = pathlib.Path(path)
            if p.exists():
                return str(p)

        # Try PATH
        return shutil.which("soffice.exe") or shutil.which("libreoffice.exe")

    elif system == "Darwin":  # macOS
        # Try standard macOS application location
        mac_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            pathlib.Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]

        for path in mac_paths:
            p = pathlib.Path(path)
            if p.exists():
                return str(p)

        # Try PATH
        return shutil.which("soffice") or shutil.which("libreoffice")

    else:  # Linux and others
        # Try PATH first (most common on Linux)
        return shutil.which("libreoffice") or shutil.which("soffice")


def find_unoconv() -> Optional[str]:
    """
    Find unoconv executable.

    Returns:
        Path to unoconv executable, or None if not found
    """
    return shutil.which("unoconv")


def find_ocrmypdf() -> Optional[str]:
    """
    Find ocrmypdf executable across platforms.

    Returns:
        Path to ocrmypdf executable, or None if not found
    """
    system = get_system()

    if system == "Windows":
        # Windows might have .exe extension
        return shutil.which("ocrmypdf.exe") or shutil.which("ocrmypdf")
    else:
        return shutil.which("ocrmypdf")


def get_temp_dir(base_name: str = "zotero_restore") -> pathlib.Path:
    """
    Get platform-appropriate temp directory.

    Uses project directory instead of system temp for better control
    and to avoid permission issues.

    Args:
        base_name: Base name for temp directory

    Returns:
        Path to temp directory (created if doesn't exist)
    """
    # Use current working directory + temp
    temp_dir = pathlib.Path.cwd() / "temp" / base_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def normalize_line_endings(text: str, target: str = "unix") -> str:
    """
    Normalize line endings for cross-platform compatibility.

    Args:
        text: Input text
        target: "unix" (\\n), "windows" (\\r\\n), or "mac" (\\r)

    Returns:
        Text with normalized line endings
    """
    # First normalize everything to \\n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if target == "windows":
        return text.replace("\n", "\r\n")
    elif target == "mac":
        return text.replace("\n", "\r")
    else:  # unix (default)
        return text


def truncate_filename(name: str, max_length: int = 200) -> str:
    """
    Truncate filename to safe length across platforms.

    Windows: 260 char total path limit (leave room for directory)
    macOS/Linux: 255 byte filename limit

    Args:
        name: Original filename
        max_length: Maximum length (default 200 to be safe)

    Returns:
        Truncated filename if necessary
    """
    if len(name) <= max_length:
        return name

    # Keep file extension
    parts = name.rsplit(".", 1)
    if len(parts) == 2:
        base, ext = parts
        # Reserve space for extension + dot
        max_base = max_length - len(ext) - 1
        if max_base > 0:
            return f"{base[:max_base]}.{ext}"

    # No extension or extension too long
    return name[:max_length]


def is_case_sensitive_filesystem() -> bool:
    """
    Check if current filesystem is case-sensitive.

    Returns:
        True if case-sensitive, False otherwise
    """
    system = get_system()

    # Linux is typically case-sensitive
    if system == "Linux":
        return True

    # Windows is case-insensitive
    if system == "Windows":
        return False

    # macOS can be either, need to test
    if system == "Darwin":
        import tempfile
        import os

        # Create a test file
        with tempfile.NamedTemporaryFile(prefix="test_", suffix=".tmp", delete=False) as f:
            test_path = f.name

        try:
            # Try to access with different case
            upper_path = test_path.upper()
            if upper_path != test_path:
                return not pathlib.Path(upper_path).exists()
            return False
        finally:
            # Clean up
            try:
                pathlib.Path(test_path).unlink()
            except:
                pass

    # Default to case-sensitive for unknown systems
    return True


def get_path_separator() -> str:
    """
    Get platform-specific path separator.

    Returns:
        Path separator ("/" or "\\")
    """
    return "\\" if get_system() == "Windows" else "/"


def sanitize_path(path_str: str) -> pathlib.Path:
    """
    Sanitize path string for current platform.

    Handles:
    - Forward/backward slashes
    - Tilde expansion
    - Environment variables

    Args:
        path_str: Path string (may contain ~, $VAR, etc.)

    Returns:
        Sanitized Path object
    """
    import os

    # Expand user home directory
    path_str = os.path.expanduser(path_str)

    # Expand environment variables
    path_str = os.path.expandvars(path_str)

    # Convert to Path (handles slash conversion automatically)
    return pathlib.Path(path_str)


def check_disk_space(path: pathlib.Path, required_mb: float = 100) -> bool:
    """
    Check if there's enough disk space.

    Args:
        path: Path to check
        required_mb: Required space in MB

    Returns:
        True if enough space, False otherwise
    """
    import shutil

    try:
        stat = shutil.disk_usage(path)
        available_mb = stat.free / (1024 * 1024)
        return available_mb >= required_mb
    except Exception:
        # If we can't check, assume it's okay
        return True


def get_system_info() -> dict:
    """
    Get detailed system information for debugging.

    Returns:
        Dictionary with system information
    """
    import sys

    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "case_sensitive": is_case_sensitive_filesystem(),
        "path_separator": get_path_separator(),
    }


def log_system_info(log):
    """Log system information for debugging."""
    info = get_system_info()
    log.info("=" * 60)
    log.info("System Information:")
    for key, value in info.items():
        log.info(f"  {key:20s}: {value}")
    log.info("=" * 60)
