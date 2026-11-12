import cv2
import numpy as np
from pathlib import Path

class VisionAgent:
    def __init__(self, template_dir: str = "assets/templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = 0.82

    def find_element_coordinates(self, img_bytes: bytes, query: str):
        nparr = np.frombuffer(img_bytes, np.uint8)
        screen_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if screen_img is None:
            return None, None, "截图解析失败"

        # ✅ 这里改成 query，query 就是模板文件名（如 user_input.png）
        template_path = self.template_dir / query
        if not template_path.exists():
            return None, None, f"模板文件不存在：{query}"

        template = cv2.imread(str(template_path))
        if template is None:
            return None, None, f"模板图片读取失败：{query}"

        t_h, t_w = template.shape[:2]
        result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        match_loc = np.where(result >= self.threshold)
        match_points = list(zip(*match_loc[::-1]))

        if not match_points:
            return None, None, "模板匹配失败，相似度低于阈值"

        match_x, match_y = match_points[0]
        center_x = int(match_x + t_w / 2)
        center_y = int(match_y + t_h / 2)
        return center_x, center_y, "ok"

    def heal_by_vision(self, img, template_key, element_id, target_desc, case_name):
        """给BasePage调用的统一入口"""
        if not template_key:
            return None
        x, y, msg = self.find_element_coordinates(img, template_key)
        if x is not None and y is not None:
            return (x, y)
        return None

    def set_threshold(self, val: float):
        self.threshold = val