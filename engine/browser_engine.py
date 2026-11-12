# engine/browser_engine.py
from playwright.sync_api import Page, ElementHandle
from typing import Optional, Tuple


class BrowserEngine:
    def __init__(self, page: Page):
        self.page = page

    def find_element(self, locator: tuple):
        """locator格式 ("css", "#id") / ("xpath", "//div")"""
        by, selector = locator
        if by == "css":
            return self.page.locator(selector).first
        elif by == "xpath":
            return self.page.locator(selector).first
        else:
            raise ValueError(f"不支持的定位方式 {by}")

    def screenshot(self):
        """返回截图bytes"""
        return self.page.screenshot()

    def click_coordinates(self, x: int, y: int):
        self.page.click(position={"x": x, "y": y})

    def select_by_text(self, elem, text: str):
        elem.select_option(label=text)

    def select_by_value(self, elem, value: str):
        elem.select_option(value=value)

    def is_checked(self, elem) -> bool:
        return elem.is_checked()

    def clear_active_input(self):
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")

    def type_text(self, text: str):
        self.page.keyboard.type(text)

    def wait_page_load(self, timeout=3000):
        self.page.wait_for_load_state("networkidle", timeout=timeout)
