import json
import base64
from pathlib import Path
import requests
from healing.exceptions import VisionRecognizeError
from healing.filter import ElementFilter

filter_ins = ElementFilter()


class BaseVisionAgent:
    """抽象父类，统一接口，面向对象规范"""
    def find_element_coordinates(self, img_bytes, template_key: str):
        raise NotImplementedError("子类必须实现 find_element_coordinates")


class MockVisionAgent(BaseVisionAgent):
    def find_element_coordinates(self, img_bytes, template_key: str):
        """适配 1280*720 视口 SauceDemo登录页 精准坐标"""
        coord_map = {
            "login_username_demo_001": (156, 264, 0.9, "用户名输入框匹配成功"),
            "login_pwd_demo_001": (156, 314, 0.9, "密码输入框匹配成功"),
            "login_btn_demo_001": (156, 376, 0.9, "登录按钮匹配成功"),
        }
        if template_key in coord_map:
            x, y, confidence, msg = coord_map[template_key]
            # 黑白名单 + 置信度校验
            ok, check_msg = filter_ins.check(template_key, confidence)
            if not ok:
                raise VisionRecognizeError(f"视觉过滤拦截：{check_msg}")
            print(f"☑ MockVisionAgent DEBUG ==== {msg} x={x},y={y} confidence={confidence}")
            return x, y, msg
        else:
            raise VisionRecognizeError(f"Mock未识别模板：{template_key}")


class RecordVisionAgent(BaseVisionAgent):
    """预录制json模式，笔记本演示用，联动全局置信度阈值"""
    def __init__(self, json_path: str = "config/mock_vision_result.json"):
        fp = Path(json_path)
        if fp.exists():
            text = fp.read_text(encoding="utf-8").strip()
            self.data = json.loads(text) if text else {}
        else:
            self.data = {}

    def find_element_coordinates(self, img_bytes, template_key: str):
        res = self.data.get(template_key)
        if not res:
            raise VisionRecognizeError(f"录制数据中未找到template_key: {template_key}")
        if "error" in res:
            raise VisionRecognizeError(res["error"])

        x = res["x"]
        y = res["y"]
        confidence = res.get("confidence", 0.0)
        # 统一走filter校验（黑白名单+置信度）
        ok, check_msg = filter_ins.check(template_key, confidence)
        if not ok:
            raise VisionRecognizeError(f"视觉过滤拦截：{check_msg}")

        msg = f"录制识别成功，置信度：{confidence}"
        print(f"\n==== RecordVisionAgent DEBUG ====")
        print(f"收到 template_key = [{template_key}]")
        print(f"☑ 匹配成功，x={x},y={y}，置信度={confidence}")
        return x, y, msg


class OllamaVisionAgent(BaseVisionAgent):
    """Ollama Moondream 本地多模态视觉版本"""
    def __init__(self, model_name: str = "moondream", ollama_url: str = "http://127.0.0.1:11434/api/generate"):
        self.model_name = model_name
        self.ollama_url = ollama_url

    def find_element_coordinates(self, img_bytes, template_key: str):
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        prompt = f"""
你是UI自动化视觉定位助手，在截图里找到【{template_key}】元素。
只返回json格式，字段 x,y,confidence，是元素中心点像素坐标和置信度0~1，不要多余文字。
示例：{{"x":120,"y":340,"confidence":0.92}}
"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            content = result.get("response", "")
            coord_json = json.loads(content)
            x = float(coord_json["x"])
            y = float(coord_json["y"])
            confidence = float(coord_json.get("confidence", 0.0))

            # 黑白名单+置信度过滤
            ok, check_msg = filter_ins.check(template_key, confidence)
            if not ok:
                raise VisionRecognizeError(f"视觉过滤拦截：{check_msg}")

            return x, y, f"ollama识别成功，置信度={confidence}"
        except Exception as e:
            raise VisionRecognizeError(f"Ollama视觉识别失败: {str(e)}")
