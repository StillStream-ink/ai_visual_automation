from playwright.sync_api import sync_playwright
from core.vision_agent import VisionAgentModule
from core.agent_runner import WebTestAgent


def test_nlp_agent_login_fail():
    vision = VisionAgentModule()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 720})

        agent = WebTestAgent(page, vision)
        agent.run("打开 https://practicetestautomation.com/practice-test-login/ ，在用户名输入框输入student，密码框输入wrongpass123，点击登录按钮，确认页面提示密码错误")

        browser.close()
