import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from core.settings import settings

# 读取配置，一次性加载，避免重复读取
CONFIDENCE_THRESHOLD = settings.get("healing.confidence_threshold", 0.85)
MAX_RETRY = settings.get("healing.max_retry", 3)
BACKOFF_INITIAL = settings.get("healing.backoff_initial", 1)
CIRCUIT_BREAK_LIMIT = settings.get("healing.circuit_break_limit", 3)
HEAL_ENABLE = settings.get("healing.enable_healing", True)
WHITE_LIST = settings.get("heal_whitelist", [])
BLACK_LIST = settings.get("heal_blacklist", [])

LOG_FILE = Path(settings.get("path.log_file"))
ASSET_DIR = Path(settings.get("path.asset_dir"))

# 熔断缓存：key=element_id，value=连续失败次数
circuit_break_cache: Dict[str, int] = {}

# 确保目录存在
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def write_healing_log(
    case_name: str,
    element_id: str,
    fail_reason: str,
    raw_snap_path: str,
    annotate_snap_path: Optional[str],
    confidence: float,
    heal_success: bool,
    layer: str = "vision"
):
    """写入自愈日志，jsonl格式"""
    log_item = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "case_name": case_name,
        "element_id": element_id,
        "fail_reason": fail_reason,
        "raw_snap_path": raw_snap_path,
        "annotate_snap_path": annotate_snap_path,
        "confidence": confidence,
        "heal_success": heal_success,
        "layer": layer
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_item, ensure_ascii=False) + "\n")


def is_allow_heal(element_id: str) -> bool:
    """黑白名单校验：判断这个元素是否允许自愈"""
    if element_id in BLACK_LIST:
        return False
    if element_id in WHITE_LIST:
        return True
    # 不在白名单也不在黑名单，默认不启用自愈
    return False


def check_circuit_break(element_id: str) -> bool:
    """检查是否熔断：True=已经熔断，禁止自愈"""
    fail_cnt = circuit_break_cache.get(element_id, 0)
    return fail_cnt >= CIRCUIT_BREAK_LIMIT


def reset_circuit_break(element_id: str):
    """自愈成功，重置熔断计数"""
    if element_id in circuit_break_cache:
        circuit_break_cache[element_id] = 0


def add_break_count(element_id: str):
    """失败，熔断计数+1"""
    circuit_break_cache[element_id] = circuit_break_cache.get(element_id, 0) + 1


def vision_identify_with_retry(
    driver: WebDriver,
    element_id: str,
    target_desc: str,
    case_name: str
) -> Tuple[bool, float, float, float, str, str]:
    """
    带指数退避重试的视觉识别主入口
    return: (success:bool, x:float, y:float, confidence:float, raw_img:str, annotate_img:str)
    """
    # 1. 全局自愈开关判断
    if not HEAL_ENABLE:
        return False, 0, 0, 0.0, "", ""

    # 2. 黑白名单校验
    if not is_allow_heal(element_id):
        write_healing_log(
            case_name=case_name,
            element_id=element_id,
            fail_reason="元素在黑名单，禁止自愈",
            raw_snap_path="",
            annotate_snap_path=None,
            confidence=0,
            heal_success=False,
            layer="blacklist"
        )
        return False, 0, 0, 0.0, "", ""

    # 3. 熔断校验
    if check_circuit_break(element_id):
        write_healing_log(
            case_name=case_name,
            element_id=element_id,
            fail_reason="元素已熔断，跳过自愈",
            raw_snap_path="",
            annotate_snap_path=None,
            confidence=0,
            heal_success=False,
            layer="circuit_break"
        )
        return False, 0, 0, 0.0, "", ""

    # 4. 截图（修复selenium原生写法！）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    raw_snap_path = str(ASSET_DIR / f"{timestamp}_{case_name}_{element_id}_raw.png")
    annotate_snap_path = str(ASSET_DIR / f"{timestamp}_{case_name}_{element_id}_annotate.png")
    driver.save_screenshot(raw_snap_path)

    retry_count = 0
    while retry_count < MAX_RETRY:
        try:
            # ======================
            # 这里替换成你原来的视觉LLM调用代码
            # res = call_vision_llm(raw_snap_path, target_desc)
            # x, y, confidence = res["x"], res["y"], res["confidence"]
            # ======================
            # 👉 自测占位，后续对接MCP视觉能力时删掉
            confidence = 0.9
            x, y = 200, 300

            # 置信度判断
            if confidence >= CONFIDENCE_THRESHOLD:
                # 识别成功，重置熔断
                reset_circuit_break(element_id)
                write_healing_log(
                    case_name=case_name,
                    element_id=element_id,
                    fail_reason="原生选择器失效，视觉兜底成功",
                    raw_snap_path=raw_snap_path,
                    annotate_snap_path=annotate_snap_path,
                    confidence=confidence,
                    heal_success=True,
                    layer="vision"
                )
                return True, x, y, confidence, raw_snap_path, annotate_snap_path
            else:
                # 置信不够，判定失败
                add_break_count(element_id)
                write_healing_log(
                    case_name=case_name,
                    element_id=element_id,
                    fail_reason=f"识别置信度{confidence}低于阈值{CONFIDENCE_THRESHOLD}",
                    raw_snap_path=raw_snap_path,
                    annotate_snap_path=annotate_snap_path,
                    confidence=confidence,
                    heal_success=False,
                    layer="vision"
                )
                return False, 0, 0, confidence, raw_snap_path, annotate_snap_path
        except Exception as e:
            retry_count += 1
            sleep_sec = BACKOFF_INITIAL * (2 ** (retry_count - 1))
            time.sleep(sleep_sec)
            continue

    # 重试全部失败
    add_break_count(element_id)
    write_healing_log(
        case_name=case_name,
        element_id=element_id,
        fail_reason="LLM接口重试全部失败",
        raw_snap_path=raw_snap_path,
        annotate_snap_path=annotate_snap_path,
        confidence=0,
        heal_success=False,
        layer="vision"
    )
    return False, 0, 0, 0.0, raw_snap_path, annotate_snap_path


# ========= 新增：给BasePage调用的上层封装方法 =========
def heal_by_vision(driver: WebDriver, element_id: str, target_desc: str, case_name: str):
    """
    对外暴露给BasePage调用
    返回：成功返回坐标(x,y)，失败返回None
    """
    success, x, y, conf, _, _ = vision_identify_with_retry(driver, element_id, target_desc, case_name)
    if success:
        return (x, y)
    return None


if __name__ == "__main__":
    # 简单自测
    print("vision healing module loaded")
    print("白名单", WHITE_LIST)
    print("黑名单", BLACK_LIST)
