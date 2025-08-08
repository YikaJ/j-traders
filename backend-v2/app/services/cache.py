from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from ..core.config import load_settings
from ..utils.hash import stable_hash


class FileCache:
    def __init__(self, base_dir: Path, ttl_hours: Optional[int] = None) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.settings = load_settings()
        self.ttl_seconds = (ttl_hours or self.settings.cache_ttl_hours) * 3600

    def _key_to_path(self, key: str) -> Path:
        return self.base_dir / f"{key}.json"

    def get(self, namespace: str, payload: Any) -> Optional[Any]:
        key = f"{namespace}:{stable_hash(payload)}"
        path = self._key_to_path(key)
        if not path.exists():
            return None
        # TTL check
        if time.time() - path.stat().st_mtime > self.ttl_seconds:
            try:
                path.unlink()
            except Exception:
                pass
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def set(self, namespace: str, payload: Any, value: Any) -> None:
        key = f"{namespace}:{stable_hash(payload)}"
        path = self._key_to_path(key)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
