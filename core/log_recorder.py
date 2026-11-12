import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import streamlit as st

from core.settings import settings

LOG_ROOT = Path(settings.get("storage.log_root"))
LOG_ROOT.mkdir(parents=True, exist_ok=True)

class SensitiveFilter(logging.Filter):
    def filter(self, record):
        # 脱敏，屏蔽密钥
        msg = str(record.msg)
        key = settings.get("llm.api_key", "")
        if key and key in msg:
            record.msg = msg.replace(key, "***")
        return True

class TestLogger:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.log_path = LOG_ROOT / f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = logging.getLogger(f"task_{task_id}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self.logger.addFilter(SensitiveFilter())

        file_handler = logging.FileHandler(self.log_path, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s | %(levelname)-6s | %(message)s")
        file_handler.setFormatter(fmt)
        self.logger.addHandler(file_handler)

        self.page_buffer = []

    def info(self, msg: str):
        self.logger.info(msg)
        self.page_buffer.append(("INFO", msg))
    def warn(self, msg: str):
        self.logger.warning(msg)
        self.page_buffer.append(("WARN", msg))
    def error(self, msg: str):
        self.logger.error(msg)
        self.page_buffer.append(("ERROR", msg))
    def debug(self, msg: str):
        self.logger.debug(msg)
        self.page_buffer.append(("DEBUG", msg))

    def render_streamlit(self, st_container):
        """在streamlit容器实时渲染日志"""
        for level, text in self.page_buffer:
            if level == "ERROR":
                st_container.error(text)
            elif level == "WARN":
                st_container.warning(text)
            elif level == "INFO":
                st_container.info(text)
            else:
                st_container.code(text)
