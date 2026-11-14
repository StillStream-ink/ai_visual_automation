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
    confidence: float
    ttl_seconds: int = 86400 * 7  # 默认7天过期


class ElementCacheService:
    def __init__(self, cache_file: str = "assets/element_repair.yaml", env: str = "test"):
        self.cache_path = Path(cache_file)
        self.env = env
        self.cache: Dict[str, CacheItem] = {}
        self._load()

    def _load(self):
        if self.cache_path.exists():
            raw = yaml.safe_load(self.cache_path.read_text(encoding="utf-8")) or {}
            for k, v in raw.items():
                loc = v["locator"]
                if isinstance(loc, list):
                    v["locator"] = tuple(loc)
                self.cache[k] = CacheItem(**v)

    def _save(self):
        raw_data = {}
        for k, item in self.cache.items():
            d = asdict(item)
            if isinstance(d["locator"], tuple):
                d["locator"] = list(d["locator"])
            raw_data[k] = d
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        # 加上 sort_keys=False 避免顺序乱，关键：不自动加python标签
        self.cache_path.write_text(yaml.dump(raw_data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def set(self, template_key: str, locator, confidence: float):
        item = CacheItem(
            locator=locator,
            update_ts=time.time(),
            env=self.env,
            confidence=confidence
        )
        self.cache[template_key] = item
        self._save()

    def get(self, template_key: str) -> Optional[CacheItem]:
        item = self.cache.get(template_key)
        if not item:
            return None
        if time.time() - item.update_ts > item.ttl_seconds:
            del self.cache[template_key]
            self._save()
            return None
        if item.env != self.env:
            return None
        return item
