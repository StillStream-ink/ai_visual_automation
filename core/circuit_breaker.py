# core/circuit_breaker.py
import time
from core.config import healing_cfg


class CircuitBreaker:
    def __init__(self):
        self.cache = {}

    def is_open(self, key: str) -> bool:
        item = self.cache.get(key)
        if not item:
            return False
        now = time.time()
        if now - item["last_fail"] > healing_cfg.circuit_break_expire_sec:
            del self.cache[key]
            return False
        return item["fail_count"] >= healing_cfg.circuit_break_limit

    def record_fail(self, key: str):
        now = time.time()
        if key in self.cache:
            self.cache[key]["fail_count"] += 1
            self.cache[key]["last_fail"] = now
        else:
            self.cache[key] = {"fail_count": 1, "last_fail": now}

    def reset(self, key: str):
        if key in self.cache:
            del self.cache[key]


circuit_breaker = CircuitBreaker()
