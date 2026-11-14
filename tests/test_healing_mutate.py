import allure
from playwright.sync_api import Page
from healing.vision_agent import BaseVisionAgent
from healing.cache_service import ElementCacheService


@allure.feature("AI视觉自愈登录")
@allure.story("DOM变异后自愈测试")
@allure.label("owner", "tester")
def test_healing_mutate(pw_page: Page, vision_agent: BaseVisionAgent):
    page = pw_page
    cache = ElementCacheService()
    max_retry = 3

    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("https://www.saucedemo.com/", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_selector("#user-name", timeout=15000)
    page.wait_for_timeout(300)

    def heal_click(template_key: str):
        retry = 0
        while retry < max_retry:
            retry += 1
            if breaker.is_break(template_key):
                log_healing_event({"type": "circuit_break", "template_key": template_key})
                raise CircuitBreakError("熔断器打开，停止自愈重试")
            img_bytes = page.screenshot(timeout=8000)
            # 修复：4元组解包
            x, y, conf, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
            allure.attach(f"识别坐标：x={x},y={y},conf={conf},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)
            log_healing_event({"type": "healing_final_success", "template_key": template_key, "x":x, "y":y})
            page.click("body", position={"x": x, "y": y})
            page.wait_for_timeout(600)
            print(f"【DEBUG】识别到按钮 x={x},y={y}")
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
            try:
                img_bytes = page.screenshot(timeout=8000)
                # 直接用 vision_agent，删掉 healer
                css_x, css_y, conf, msg = vision_agent.find_element_coordinates(img_bytes, template_key)
                allure.attach(f"识别坐标：css_x={css_x},css_y={css_y},conf={conf},info={msg}", name=f"{template_key}_识别结果", attachment_type=allure.attachment_type.TEXT)
                log_healing_event({"type": "healing_final_success", "template_key": template_key, "x": css_x, "y": css_y})

                # 向上遍历找input，和SauceDemo成功版本保持一致
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
        log_healing_event({"type": "healing_final_fail", "template_key": template_key})
        breaker.mark_fail(template_key)
        raise LocatorNotFoundError(f"{template_key} 多次自愈识别失败")



