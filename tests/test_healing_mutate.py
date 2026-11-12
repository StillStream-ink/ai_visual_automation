import allure
from playwright.sync_api import Page
from healing.vision_agent import BaseVisionAgent
from healing.cache_service import ElementCacheService
from healing.circuit_breaker import TimeWindowCircuitBreaker
from healing.exceptions import LocatorNotFoundError, CircuitBreakError
from conftest import log_healing_event


@allure.feature("AI视觉自愈登录")
@allure.story("DOM变异后自愈测试")
@allure.label("owner", "tester")
def test_healing_mutate(pw_page: Page, vision_agent: BaseVisionAgent):
    page = pw_page
    cache = ElementCacheService()
    breaker = TimeWindowCircuitBreaker(window_seconds=10, limit=3)
    max_retry = 3

    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("https://www.saucedemo.com/", wait_until="commit", timeout=30000)
    page.wait_for_timeout(2000)

    def heal_click(template_key: str):
        retry = 0
        while retry < max_retry:
            retry += 1
            if breaker.is_break(template_key):
                log_healing_event({"type": "circuit_break", "template_key": template_key})
                raise CircuitBreakError("熔断器打开，停止自愈重试")
            img_bytes = page.screenshot(timeout=8000)
            x, y, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
            allure.attach(f"识别坐标：x={x},y={y},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)
            log_healing_event({"type": "healing_final_success", "template_key": template_key, "x":x, "y":y})
            page.click("body", position={"x": x, "y": y})
            page.wait_for_timeout(500)
            page.evaluate("""
                ()=>{
                    const btn = document.querySelector('#login-button');
                    if(btn) btn.click();
                }
            """)
            page.wait_for_timeout(2000)
            print(f"【DEBUG】点击按钮后当前URL：{page.url}")
            return
        log_healing_event({"type": "healing_final_fail", "template_key": template_key})
        breaker.mark_fail(template_key)
        raise LocatorNotFoundError(f"{template_key} 多次自愈识别失败")


    def heal_fill(template_key: str, text: str):
        retry = 0
        while retry < max_retry:
            retry += 1
            if breaker.is_break(template_key):
                log_healing_event({"type": "circuit_break", "template_key": template_key})
                raise CircuitBreakError("熔断器打开，停止自愈重试")
            img_bytes = page.screenshot(timeout=8000)
            x, y, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
            allure.attach(f"识别坐标：x={x},y={y},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)
            log_healing_event({"type": "healing_final_success", "template_key": template_key, "x":x, "y":y})
            page.click("body", position={"x": x, "y": y})
            page.wait_for_timeout(400)

            if template_key == "login_username_demo_001":
                selector = "#user-name"
            elif template_key == "login_pwd_demo_001":
                selector = "#password"
            else:
                selector = None

            if selector:
                page.fill(selector, text)

            page.wait_for_timeout(300)
            return
        log_healing_event({"type": "healing_final_fail", "template_key": template_key})
        breaker.mark_fail(template_key)
        raise LocatorNotFoundError(f"{template_key} 多次自愈识别失败")

    # ========== 直接 evaluate 修改DOM，去掉DomMutator ==========
    page.evaluate("""()=>{
        const u = document.querySelector('#user-name');
        if(u) u.id = 'user-name-mutated';
        const p = document.querySelector('#password');
        if(p) p.id = 'password-mutated';
        const b = document.querySelector('#login-button');
        if(b) b.id = 'login-button-mutated';
    }""")

    heal_fill("login_username_demo_001", "standard_user")
    heal_fill("login_pwd_demo_001", "secret_sauce")
    heal_click("login_btn_demo_001")

    page.wait_for_selector("span.title", timeout=15000)
    assert "Products" in page.locator("span.title").text_content()
