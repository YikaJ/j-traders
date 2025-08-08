from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass
class RateLimit:
    qps: int
    burst: int


class TokenBucket:
    def __init__(self, qps: int, burst: int) -> None:
        self.capacity = max(1, burst)
        self.tokens = self.capacity
        self.refill_rate = max(1e-6, qps)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.last_refill = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
            time.sleep(1.0 / (self.refill_rate + 1e-6))
