from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(obj: Any) -> str:
    """Compute a stable SHA1 hash for a JSON-serializable object.

    Ensures keys are sorted and separators are consistent.
    """
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(data.encode("utf-8")).hexdigest()
