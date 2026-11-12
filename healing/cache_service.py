# cache_service.py
import yaml
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CacheItem:
    locator: Any
    update_ts: float
    env: str
    ttl_seconds: int = 86400 * 7  # 默认7天过期


class ElementCacheService:
    def __init__(self, cache_file: str = "assets/element_repair.yaml", env: str = "test"):
        self.cache_path = Path(cache_file)
        self.env = env
        self.cache: Dict[str, CacheItem] = {}
        self._load()

    def _load(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.cache_path.exists():
            self.cache = {}
            return
        with open(self.cache_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raw = {}
        self.cache = {}
        now = time.time()
        for elem_id, data in raw.items():
            if not isinstance(data, dict):
                continue
            try:
                loc = data.get("locator")
                if isinstance(loc, list) and len(loc) == 2 and all(isinstance(x, (int, float)) for x in loc):
                    data["locator"] = tuple(loc)
                item = CacheItem(**data)
                self.cache[elem_id] = item
            except Exception:
                continue

    def save(self, elem_id: str, loc_data):
        item = CacheItem(
            locator=loc_data,
            update_ts=time.time(),
            env=self.env,
            ttl_seconds=86400 * 7
        )
        self.cache[elem_id] = item
        self._persist()

    def get(self, element_id: str) -> Optional[Any]:
        item = self.cache.get(element_id)
        if not item:
            return None
        now = time.time()
        if now - item.update_ts >= item.ttl_seconds:
            del self.cache[element_id]
            self._persist()
            return None
        if item.env != self.env:
            return None
        return item.locator

    def _persist(self):
        dump_data = {}
        for k, v in self.cache.items():
            d = asdict(v)
            loc = d.get("locator")
            if isinstance(loc, tuple):
                d["locator"] = list(loc)
            dump_data[k] = d
        with open(self.cache_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(dump_data, f, allow_unicode=True, sort_keys=False)
