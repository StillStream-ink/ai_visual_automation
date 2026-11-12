import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from playwright.sync_api import Locator
import allure
from core.settings import settings
from core.log_recorder import TestLogger

# 读取配置
CONFIDENCE_THRESHOLD = settings.get("healing.confidence_threshold", 0.85)
MAX_RETRY = settings.get("healing.max_retry", 3)
BACKOFF_INITIAL = settings.get("healing.backoff_initial", 1)
CIRCUIT_BREAK_LIMIT = settings.get("healing.circuit_break_limit", 3)

# 熔断缓存
circuit_break_cache: Dict[str, int] = {}


class BasePage:
    def __init__(self, page, vision_agent, case_name: str, logger: TestLogger):
        self.page = page
        self.vision = vision_agent
        self.case_name = case_name
        self.logger = logger
        self.repair_cache: Dict[str, Any] = {}
        self.black_list = set()
        self.white_list = set()
        self._load_repair_cache()

    def _load_repair_cache(self):
        """加载yaml持久化修复定位缓存"""
        import yaml
        repair_path = Path("assets/element_repair.yaml")
        repair_path.parent.mkdir(parents=True, exist_ok=True)
        if repair_path.exists():
            with open(repair_path, "r", encoding="utf-8") as f:
                self.repair_cache = yaml.safe_load(f) or {}
        else:
            self.repair_cache = {}

    def _save_repair_cache(self, element_id: str, locator_data):
        """自愈成功，回写yaml持久化"""
        import yaml
        repair_path = Path("assets/element_repair.yaml")
        repair_path.parent.mkdir(parents=True, exist_ok=True)
        self.repair_cache[element_id] = {
            "locator": locator_data,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(repair_path, "w", encoding="utf-8") as f:
            yaml.dump(self.repair_cache, f, allow_unicode=True, sort_keys=False)

    def _parse_locator(self, loc_info):
        """解析定位器 [css, #id] 或者直接字符串"""
        if isinstance(loc_info, list):
            by, val = loc_info
            if by == "css":
                return self.page.locator(val)
            elif by == "xpath":
                return self.page.locator(f"xpath={val}")
            elif by == "text":
                return self.page.get_by_text(val)
        return self.page.locator(loc_info)

    def _reset_circuit_break(self, element_id: str):
        if element_id in circuit_break_cache:
            del circuit_break_cache[element_id]

    def _is_circuit_break(self, element_id: str) -> bool:
        cnt = circuit_break_cache.get(element_id, 0)
        return cnt >= CIRCUIT_BREAK_LIMIT

    def _inc_circuit_break(self, element_id: str):
        circuit_break_cache[element_id] = circuit_break_cache.get(element_id, 0) + 1

    def _log_healing(self, element_id, status, msg, extra: dict = None):
        """统一使用TestLogger记录，同时保留Allure附件"""
        log_msg = f"[{element_id}] | {status} | {msg}"
        self.logger.logger.info(log_msg, extra=extra or {})

        if extra and extra.get("screenshot_bytes"):
            allure.attach(
                extra["screenshot_bytes"],
                name=f"{element_id}_screenshot",
                attachment_type=allure.attachment_type.PNG
            )
        log_data = {
            "case_name": self.case_name,
            "element_id": element_id,
            "status": status,
            "msg": msg,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "extra": extra or {}
        }
        allure.attach(
            json.dumps(log_data, ensure_ascii=False, indent=2),
            name=f"healing_record_{element_id}_{status}",
            attachment_type=allure.attachment_type.JSON
        )

    def _do_vision_heal(self, elem: Dict[str, Any]) -> Tuple[Optional[Dict], bool]:
        """执行视觉自愈，成功返回坐标信息，不再返回Locator（坐标不能生成locator）"""
        element_id = elem["element_id"]
        desc = elem["desc"]
        template_key = elem.get("template_key", "")

        screenshot_bytes = self.page.screenshot()
        x, y, msg = self.vision.find_element_coordinates(
            img_bytes=screenshot_bytes,
            template_key=template_key
        )

        if x is None or y is None:
            self._inc_circuit_break(element_id)
            self._log_healing(
                element_id=element_id,
                status="vision_heal_fail",
                msg=f"{desc} 视觉定位失败: {msg}",
                extra={"template_key": template_key, "screenshot_bytes": screenshot_bytes}
            )
            return None, False

        # 坐标方案：直接返回坐标，上层用page.click(position=...)
        self._save_repair_cache(element_id, ["coordinate", [x, y]])
        self._reset_circuit_break(element_id)
        self._log_healing(
            element_id=element_id,
            status="vision_heal_success",
            msg=f"{desc} 视觉自愈成功，坐标({x},{y})",
            extra={"template_key": template_key, "x": x, "y": y, "screenshot_bytes": screenshot_bytes}
        )
        return {"x": x, "y": y}, True

    def _find_elem_with_heal(self, elem: Dict[str, Any]) -> Tuple[Optional[Locator | Dict], bool]:
        """路线A：原生优先，失败走视觉自愈
        返回：(locator / 坐标dict, 是否自愈)
        """
        element_id = elem["element_id"]
        desc = elem["desc"]
        template_key = elem.get("template_key", "")

        # 黑名单：禁止自愈，原生失败直接返回
        if element_id in self.black_list:
            self._log_healing(element_id=element_id, status="blacklist_skip_heal", msg=desc)
            loc = self._parse_locator(elem["locator"])
            try:
                loc.wait_for(timeout=1000)
                self._reset_circuit_break(element_id)
                return loc, False
            except Exception:
                return None, False

        # 白名单：强制自愈，跳过原生定位
        if element_id in self.white_list:
            self._log_healing(element_id=element_id, status="whitelist_force_vision", msg=desc)
            return self._do_vision_heal(elem)

        # 优先读取yaml里已经修复好的缓存
        if element_id in self.repair_cache:
            cached_loc = self.repair_cache[element_id]["locator"]
            if cached_loc[0] == "coordinate":
                # 缓存是坐标
                coord_data = {"x": cached_loc[1][0], "y": cached_loc[1][1]}
                self._log_healing(element_id=element_id, status="use_cached_coordinate", msg=desc)
                return coord_data, True
            else:
                loc = self._parse_locator(cached_loc)
            try:
                loc.wait_for(timeout=1000)
                self._log_healing(element_id=element_id, status="use_cached_locator", msg=desc)
                return loc, True
            except Exception:
                self._log_healing(element_id=element_id, status="cache_invalid", msg=desc)

        if self._is_circuit_break(element_id):
            self._log_healing(element_id=element_id, status="circuit_break", msg=desc)
            return None, False

        retry = 0
        loc = self._parse_locator(elem["locator"])
        while retry < MAX_RETRY:
            try:
                loc.wait_for(timeout=1000)
                self._reset_circuit_break(element_id)
                self._log_healing(element_id=element_id, status="native_success", msg=desc)
                return loc, False
            except Exception:
                retry += 1
                sleep_t = BACKOFF_INITIAL * retry
                time.sleep(sleep_t)

        # 原生全部失败，进入视觉自愈
        self._log_healing(
            element_id=element_id,
            status="vision_healing_start",
            msg=desc,
            extra={"template_key": template_key}
        )
        return self._do_vision_heal(elem)

    # ========== 对外封装方法 ==========
    def _click_with_heal(self, elem: Dict[str, Any], force=False):
        target, healed = self._find_elem_with_heal(elem)
        if target is None:
            raise Exception(f"元素 {elem['element_id']} 定位失败，自愈流程结束")
        try:
            if isinstance(target, dict) and "x" in target:
                # 视觉自愈拿到坐标，直接页面点击
                self.page.click(position={"x": target["x"], "y": target["y"]}, force=force)
            else:
                # 原生locator
                target.click(force=force)
            return healed
        except Exception as e:
            self.logger.logger.exception(f"元素 {elem['element_id']} 点击执行异常")
            raise

    def _input_with_heal(self, elem: Dict[str, Any], text: str):
        target, healed = self._find_elem_with_heal(elem)
        if target is None:
            raise Exception(f"元素 {elem['element_id']} 定位失败，自愈流程结束")
        try:
            if isinstance(target, dict) and "x" in target:
                # 坐标模式：先点击激活再输入
                self.page.click(position={"x": target["x"], "y": target["y"]})
                self.page.fill("body", text)
            else:
                target.fill(text)
            return healed
        except Exception as e:
            self.logger.logger.exception(f"元素 {elem['element_id']} 输入执行异常")
            raise

    def _select_with_heal(self, elem: Dict[str, Any], value):
        target, healed = self._find_elem_with_heal(elem)
        if target is None:
            raise Exception(f"元素 {elem['element_id']} 定位失败，自愈流程结束")
        try:
            if isinstance(target, dict) and "x" in target:
                raise Exception("坐标模式不支持select下拉选择，请使用原生定位器")
            target.select_option(value)
            return healed
        except Exception as e:
            self.logger.logger.exception(f"元素 {elem['element_id']} 下拉选择异常")
            raise

    def _check_with_heal(self, elem: Dict[str, Any], checked: bool = True):
        target, healed = self._find_elem_with_heal(elem)
        if target is None:
            raise Exception(f"元素 {elem['element_id']} 定位失败，自愈流程结束")
        try:
            if isinstance(target, dict) and "x" in target:
                self.page.click(position={"x": target["x"], "y": target["y"]})
            else:
                if checked:
                    target.check()
                else:
                    target.uncheck()
            return healed
        except Exception as e:
            self.logger.logger.exception(f"元素 {elem['element_id']} 复选框操作异常")
            raise
