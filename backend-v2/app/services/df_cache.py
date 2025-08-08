from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from ..services.cache import FileCache


class DataFrameCache:
    def __init__(self, base_dir: Path) -> None:
        self.json_cache = FileCache(base_dir)

    def get(self, namespace: str, payload: Any) -> Optional[pd.DataFrame]:
        obj = self.json_cache.get(namespace, payload)
        if obj is None:
            return None
        try:
            return pd.DataFrame(obj)
        except Exception:
            return None

    def set(self, namespace: str, payload: Any, df: pd.DataFrame) -> None:
        self.json_cache.set(namespace, payload, df.to_dict(orient="records"))
