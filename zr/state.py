from __future__ import annotations
import json
import pathlib
import threading
from typing import Optional, Dict, Any

class StateStore:
    def __init__(self, path: pathlib.Path, log):
        self.path = path
        self.log = log
        self._map: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()  # Thread-safe lock for concurrent writes
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                rid = obj.get("record_id")
                if rid:
                    self._map[rid] = obj
        except Exception as e:
            self.log.warning(f"Failed to load state: {e}")

    def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._map.get(record_id)

    def set(self, record_id: str, data: Dict[str, Any]) -> None:
        obj = {"record_id": record_id, **data}
        with self._lock:
            self._map[record_id] = obj
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

