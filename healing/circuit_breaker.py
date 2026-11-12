import time
from typing import Dict


class TimeWindowCircuitBreaker:
    """时间窗口熔断：窗口内失败次数达到阈值熔断，超时自动恢复"""
    def __init__(self, window_seconds: int = 1800, limit: int = 3):
        self.window = window_seconds
        self.limit = limit
        self.record: Dict[str, list[float]] = {}

    def mark_fail(self, element_id: str):
        now = time.time()
        if element_id not in self.record:
            self.record[element_id] = []
        self.record[element_id].append(now)
        # 清理窗口外旧记录
        self.record[element_id] = [t for t in self.record[element_id] if now - t < self.window]

    def is_break(self, element_id: str) -> bool:
        records = self.record.get(element_id, [])
        now = time.time()
        valid = [t for t in records if now - t < self.window]
        return len(valid) >= self.limit

    def reset(self, element_id: str):
        if element_id in self.record:
            del self.record[element_id]
