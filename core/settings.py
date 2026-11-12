import yaml
from pathlib import Path
from typing import Dict, Any
import os

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

class Settings:
    def __init__(self):
        self.raw: Dict[str, Any] = {}
        self.load_config()
        self.validate_config()

    def load_config(self):
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"配置文件不存在：{CONFIG_PATH}")
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.raw = yaml.safe_load(f) or {}  # 兜底防止yaml为空返回None

    def validate_config(self):
        # 参数合法性校验
        conf = self.raw
        # 容错：healing节点存在才校验
        if "healing" in conf:
            conf["healing"]["confidence_threshold"] = float(conf["healing"]["confidence_threshold"])
            if not (0 < conf["healing"]["confidence_threshold"] <= 1):
                raise ValueError("置信度阈值必须在 0~1 之间")
            if conf["healing"]["max_retry"] < 0:
                raise ValueError("重试次数不能小于0")
        if "browser" in conf and conf["browser"]["timeout"] < 1000:
            raise ValueError("浏览器超时不能小于1000ms")

    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self.raw
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key: str, value):
        keys = key.split(".")
        node = self.raw
        for k in keys[:-1]:
            if k not in node:
                node[k] = {}
            node = node[k]
        node[keys[-1]] = value
        # 写入yaml持久化
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self.raw, f, allow_unicode=True, sort_keys=False)

settings = Settings()
