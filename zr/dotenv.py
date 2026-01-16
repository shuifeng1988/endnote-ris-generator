from __future__ import annotations
import os
import pathlib

def load_dotenv(dotenv_path: pathlib.Path) -> None:
    """
    Minimal .env loader.
    Supports:
      KEY=VALUE
      export KEY=VALUE
    Does not override existing env vars.
    """
    if not dotenv_path.exists():
        return

    text = dotenv_path.read_text(encoding="utf-8", errors="ignore")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not k:
            continue
        os.environ.setdefault(k, v)

