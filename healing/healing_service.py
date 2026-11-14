import json
import time
from typing import Optional, Tuple
from playwright.sync_api import Page
from healing.vision_agent import BaseVisionAgent
from healing.cache_service import ElementCacheService
from healing.exceptions import VisionRecognizeError
from healing.vision_agent import ElementFilter


class HealingService:
    def __init__(
        self,
        vision_agent: BaseVisionAgent,
        cache_service: ElementCacheService,
        viewport_w: int = 1280,
        viewport_h: int = 720
    ):
        self.vision_agent = vision_agent
        self.cache_service = cache_service
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        self.filter = ElementFilter()

    def pixel_to_css(self, pixel_x: float, pixel_y: float, screenshot_w: int, screenshot_h: int) -> Tuple[float, float]:
        """
        截图像素坐标 → Playwright elementFromPoint 使用的CSS视口坐标
        Mock / CV模板匹配 / Ollama 输出的都是截图像素，统一在这里换算
        """
        css_x = pixel_x * (self.viewport_w / screenshot_w)
        css_y = pixel_y * (self.viewport_h / screenshot_h)
        return css_x, css_y

    def _get_screenshot(self, page: Page) -> Tuple[bytes, int, int]:
        """截图，返回图片字节、截图宽高"""
        import cv2
        import numpy as np
        screenshot_bytes = page.screenshot(full_page=False)
        arr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        return screenshot_bytes, w, h

    def locate_element_by_vision(self, page: Page, template_key: str) -> Tuple[float, float]:
        """
        自愈定位主逻辑：先查缓存，缓存失效再调用视觉识别
        返回：换算完成后的CSS坐标 (css_x, css_y)
        """
        # 1. 优先读取缓存
        cache_item = self.cache_service.get(template_key)
        if cache_item is not None:
            return cache_item.locator

        # 2. 缓存未命中，截图调用视觉识别
        img_bytes, scr_w, scr_h = self._get_screenshot(page)
        pixel_x, pixel_y, conf, msg = self.vision_agent.find_element_coordinates(img_bytes, template_key)

        if pixel_x is None or pixel_y is None:
            raise VisionRecognizeError(f"视觉定位失败：{msg}")

        # 3. 像素坐标转CSS坐标
        css_x, css_y = self.pixel_to_css(pixel_x, pixel_y, scr_w, scr_h)

        # 4. 写入缓存（缓存存换算后的css坐标）
        self.cache_service.set(
            template_key=template_key,
            locator=(css_x, css_y),
            confidence=conf
        )
        return css_x, css_y

    def click_by_vision(self, page: Page, template_key: str):
        """视觉自愈点击"""
        x, y = self.locate_element_by_vision(page, template_key)
        page.evaluate("(x, y) => document.elementFromPoint(x, y)", x, y)
        page.click(position={"x": x, "y": y})

    def fill_by_vision(self, page: Page, template_key: str, value: str):
        """视觉自愈输入"""
        x, y = self.locate_element_by_vision(page, template_key)
        # 先点击聚焦
        page.click(position={"x": x, "y": y})
        # 清空原有内容
        page.keyboard.press("Control+A")
        page.keyboard.type(value)
