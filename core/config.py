from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class LLMConfig:
    zhipu_key: str
    base_url: str
    vision_model: str


@dataclass
class HealingCfg:
    enable_healing: bool = True
    confidence_threshold: float = 0.85
    max_retry: int = 3
    backoff_initial: int = 1
    circuit_break_limit: int = 3


@dataclass
class Settings:
    llm: LLMConfig
    healing: HealingCfg


# 加载配置实例
llm_cfg = LLMConfig(
    zhipu_key=os.getenv("ZHIPU_API_KEY", ""),
    base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
    vision_model=os.getenv("VISION_MODEL", "glm-4v")
)

healing_cfg = HealingCfg()

settings = Settings(
    llm=llm_cfg,
    healing=healing_cfg
)
