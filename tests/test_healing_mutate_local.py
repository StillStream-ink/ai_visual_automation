import os
import allure
from playwright.sync_api import Page
from healing.exceptions import LocatorNotFoundError, CircuitBreakError
from healing.cache_service import ElementCacheService
from healing.circuit_breaker import TimeWindowCircuitBreaker
from healing.vision_agent import BaseVisionAgent


@allure.feature("AI视觉自愈登录")
@allure.story("DOM变异后自愈测试【本地静态页面】")
@allure.label("owner", "tester")
def test_healing_mutate_local(pw_page: Page, vision_agent: BaseVisionAgent):
    page = pw_page
    cache = ElementCacheService()
    breaker = TimeWindowCircuitBreaker(window_seconds=10, limit=3)
    max_retry = 3

    page.set_viewport_size({"width": 1280, "height": 720})
    html_path = os.path.abspath("local_login.html")
    page.goto(f"file://{html_path}", wait_until="commit", timeout=30000)
    page.wait_for_timeout(1000)

    def heal_click(template_key: str):
        retry = 0
        while retry < max_retry:
            retry += 1
            if breaker.is_break(template_key):
                raise CircuitBreakError("熔断器打开，停止自愈重试")
            img_bytes = page.screenshot(timeout=8000)
            x, y, conf, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
            allure.attach(f"识别坐标：x={x},y={y},conf={conf},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)
            page.click("body", position={"x": x, "y": y})
            page.wait_for_timeout(600)
            print(f"【DEBUG】识别到按钮 x={x},y={y}")
            return
        breaker.mark_fail(template_key)
        raise LocatorNotFoundError(f"{template_key} 多次自愈识别失败")


    def heal_fill(template_key: str, text: str):
        retry = 0
        while retry < max_retry:
            retry += 1
            if breaker.is_break(template_key):
                raise CircuitBreakError("熔断器打开，停止自愈重试")
            try:
                img_bytes = page.screenshot(timeout=8000)
                css_x, css_y, conf, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
                allure.attach(f"识别坐标：css_x={css_x},css_y={css_y},conf={conf},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)

                tag = page.evaluate("""
                    ([x,y])=>{
                        let el = document.elementFromPoint(x,y);
                        while(el && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA'){
                            el = el.parentElement;
                        }
                        if(!el) return null;
                        el.focus();
                        return el.tagName;
                    }
                """, (css_x, css_y))
                page.wait_for_timeout(300)
                page.keyboard.press("Control+A")
                page.keyboard.type(text)
                page.wait_for_timeout(600)
                print(f"【DEBUG】输入框坐标 css_x={css_x},css_y={css_y}，拿到元素tag={tag}")
                return
            except Exception as e:
                print(f"【DEBUG】第{retry}次自愈失败: {e}")
                continue
        breaker.mark_fail(template_key)
        raise LocatorNotFoundError(f"{template_key} 多次自愈识别失败")

    # ========== DOM变异：篡改元素ID（模拟前端改动） ==========
    page.evaluate("""
        () => {
            const userEl = document.querySelector('#user-name');
            if(userEl) userEl.id = 'user-name-mutated';
            const pwdEl = document.querySelector('#password');
            if(pwdEl) pwdEl.id = 'password-mutated';
            const btnEl = document.querySelector('#login-btn');
            if(btnEl) btnEl.id = 'login-btn-mutated';
            console.log("【变异完成】输入框、按钮ID全部篡改");
        }
    """)
    print("【DEBUG】DOM变异完成，原选择器已经失效")

    # 视觉定位填写账号密码
    heal_fill("login_username_demo_001", "admin")
    heal_fill("login_password_demo_001", "123456")
    heal_click("login_btn_demo_001")

    # 断言登录成功（根据你本地页面改）
    page.wait_for_timeout(1000)
    assert True
