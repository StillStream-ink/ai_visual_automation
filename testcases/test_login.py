from playwright.sync_api import sync_playwright
from core.vision_agent import VisionAgentModule
from pages.login_page import LoginPage

def test_login_and_logout():
    vision = VisionAgentModule()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("https://practicetestautomation.com/practice-test-login/")
        login = LoginPage(page, vision, case_name="test_login_demo")
        # 登录，然后链式调用登出
        login.login("student", "Password123").logout()
        browser.close()
