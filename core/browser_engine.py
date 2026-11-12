# core/browser_engine.py
from playwright.sync_api import sync_playwright
from core.vision_agent import VisionAgentModule
from pages.login_page import LoginPage
from core.settings import settings

class BrowserEngine:
    def __init__(self, healing_mode: bool = False):
        self.play = None
        self.browser = None
        self.page = None
        self.vision = VisionAgentModule()
        self.healing_mode = healing_mode

    def start(self, headless=False):
        self.play = sync_playwright().start()
        self.browser = self.play.chromium.launch(headless=headless)
        self.page = self.browser.new_page(viewport={"width":1280, "height":720})
        return "✅ 浏览器启动成功"

    def open_url(self, url: str):
        if not self.page:
            return "❌ 浏览器未初始化"
        self.page.goto(url)
        return f"✅ 页面打开：{url}"

    def close(self):
        if self.browser:
            self.browser.close()
        if self.play:
            self.play.stop()
