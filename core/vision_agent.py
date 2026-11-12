import time
import requests
from typing import Optional, Tuple, Dict
from core.settings import settings

class VisionAgent:
    def __init__(self, logger):
        self.logger = logger
        self.use_mock = settings.get("llm.use_mock")
        self.confidence_threshold = settings.get("healing.confidence_threshold")
        self.max_retry = settings.get("healing.max_retry")
        self.backoff_initial = settings.get("healing.backoff_initial")
        self.circuit_break_limit = settings.get("healing.circuit_break_limit")
        self.break_counter = 0
        self.is_break = False

    def circuit_break_check(self) -> bool:
        """熔断判断：连续失败达到阈值，直接拒绝调用"""
        if self.is_break:
            self.logger.warn("【熔断触发】视觉模型已熔断，不再发起请求")
            return False
        return True

    def reset_break(self):
        self.break_counter = 0
        self.is_break = False

    def _call_vision_model(self, base64_img: str, prompt: str) -> Dict:
        if self.use_mock:
            self.logger.info("【Mock模式】跳过大模型调用")
            return {"ok": True, "x": None, "y": None, "confidence": 0.9}

        api_key = settings.get("llm.api_key")
        model = settings.get("llm.model_name")
        url = settings.get("llm.base_url") + "/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ]}
            ]
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def detect_element(self, base64_img: str, target_name: str) -> Tuple[bool, Optional[int], Optional[int], float]:
        """
        返回：ok, x, y, confidence
        """
        if not self.circuit_break_check():
            return False, None, None, 0.0

        prompt = f"在截图中找到【{target_name}】，返回json：{{'x':中心点x,'y':中心点y,'confidence':0~1}}"
        retry_count = 0
        while retry_count <= self.max_retry:
            try:
                res_json = self._call_vision_model(base64_img, prompt)
                if self.use_mock:
                    # mock模式下，外部传入坐标指令接管
                    self.reset_break()
                    return True, None, None, 0.9

                content = res_json["choices"][0]["message"]["content"]
                import json
                ret = json.loads(content)
                x = int(ret["x"])
                y = int(ret["y"])
                conf = float(ret["confidence"])

                if conf >= self.confidence_threshold:
                    self.reset_break()
                    self.logger.info(f"视觉识别成功，坐标({x},{y})，置信度：{conf:.2f}")
                    return True, x, y, conf
                else:
                    self.logger.warn(f"置信度{conf:.2f}低于阈值{self.confidence_threshold}，识别无效")
                    raise Exception("置信度不足")

            except Exception as e:
                retry_count +=1
                sleep_sec = self.backoff_initial * (2 ** (retry_count -1))
                self.logger.error(f"视觉识别失败，重试{retry_count}/{self.max_retry}，等待{sleep_sec}s，err:{str(e)}")
                time.sleep(sleep_sec)
                if retry_count > self.max_retry:
                    self.break_counter +=1
                    if self.break_counter >= self.circuit_break_limit:
                        self.is_break = True
                        self.logger.error(f"连续失败达到{self.circuit_break_limit}次，熔断开启")
                    return False, None, None, 0.0
        return False, None, None, 0.0
