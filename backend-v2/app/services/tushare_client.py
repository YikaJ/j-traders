from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

import pandas as pd

from ..core.config import load_settings
from ..models.endpoint import EndpointMeta
from ..services.cache import FileCache
from ..services.df_cache import DataFrameCache
from ..services.rate_limiter import TokenBucket


class TuShareClient:
    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.settings = load_settings()
        base = Path(cache_dir) if cache_dir else Path(__file__).resolve().parents[2] / "cache"
        self.cache = DataFrameCache(base)
        qps = self.settings.max_qps
        self.bucket = TokenBucket(qps=qps, burst=max(2, qps * 2))
        self._pro = None

    def _ensure_sdk(self):
        if self._pro is None:
            import tushare as ts  # type: ignore
            token = self.settings.tushare_token or os.getenv("TUSHARE_TOKEN")
            if not token:
                raise RuntimeError("TUSHARE_TOKEN is required")
            ts.set_token(token)
            self._pro = ts.pro_api()
        return self._pro

    def fetch(self, endpoint_meta: EndpointMeta, params: Dict[str, Any]) -> pd.DataFrame:
        namespace = f"tushare:{endpoint_meta.name}"
        cached_df = self.cache.get(namespace, params)
        if cached_df is not None:
            return cached_df

        # retry with exponential backoff
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                self.bucket.acquire()
                pro = self._ensure_sdk()
                method_name = endpoint_meta.sdk.get("method")
                if not method_name:
                    raise RuntimeError("endpoint sdk.method missing")
                method = getattr(pro, method_name)
                df = method(**params)
                self.cache.set(namespace, params, df)
                return df
            except Exception as e:  # noqa: BLE001
                last_exc = e
                import time as _t
                _t.sleep(0.5 * (2 ** attempt))
        assert last_exc is not None
        raise last_exc

    def fetch_iter_ts_codes(self, endpoint_meta: EndpointMeta, base_params: Dict[str, Any], ts_codes: List[str]) -> pd.DataFrame:
        all_rows: List[Dict[str, Any]] = []
        for code in ts_codes:
            local_params = dict(base_params)
            local_params["ts_code"] = code
            df = self.fetch(endpoint_meta, local_params)
            if not df.empty:
                all_rows.extend(df.to_dict(orient="records"))
        return pd.DataFrame(all_rows)
