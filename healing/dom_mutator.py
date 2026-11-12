from playwright.sync_api import Page
import allure

class DomMutator:
    """DOM变异：修改属性、偏移位置，模拟前端改版，验证自愈"""
    @staticmethod
    def mutate_element_offset(page: Page, selector: str, dx: int = 60, dy: int = 30):
        """偏移元素位置，left/top加上dx dy"""
        js = f"""
        const el = document.querySelector('{selector}');
        if(el){{
            const rect = el.getBoundingClientRect();
            el.style.position = 'relative';
            el.style.left = "{dx}px";
            el.style.top = "{dy}px";
        }}
        """
        page.evaluate(js)
        allure.attach(f"变异：元素 {selector} 偏移 dx={dx}, dy={dy}", name="变异记录", attachment_type=allure.attachment_type.TEXT)

    @staticmethod
    def mutate_attr(page: Page, selector: str, attr_name: str, new_value: str):
        """修改元素属性，比如id、class、name"""
        js = f"""
        const el = document.querySelector('{selector}');
        if(el) el.setAttribute('{attr_name}', '{new_value}');
        """
        page.evaluate(js)
        allure.attach(f"变异：{selector} 修改属性 {attr_name} → {new_value}", name="变异记录", attachment_type=allure.attachment_type.TEXT)

    @staticmethod
    def mutate_hide_element(page: Page, selector: str):
        """隐藏元素，极端场景"""
        js = f"""
        const el = document.querySelector('{selector}');
        if(el) el.style.display = 'none';
        """
        page.evaluate(js)
        allure.attach(f"变异：{selector} 设置display:none", name="变异记录", attachment_type=allure.attachment_type.TEXT)
