from playwright.sync_api import Page
import json
from typing import List, Dict

class UIMutator:
    """UI元素变异器，用来模拟前端改动，评估自愈框架鲁棒性"""
    def __init__(self, page: Page):
        self.page = page

    def mutate_id(self, selector: str, new_id: str = "mutated_fake_id"):
        """变异1：修改元素id，破坏css #id定位"""
        self.page.evaluate(f'''
            () => {{
                const el = document.querySelector("{selector}");
                if(el) el.id = "{new_id}";
            }}
        ''')

    def mutate_class(self, selector: str, new_class: str = "mutated-fake-class"):
        """变异2：修改class属性"""
        self.page.evaluate(f'''
            () => {{
                const el = document.querySelector("{selector}");
                if(el) el.className = "{new_class}";
            }}
        ''')

    def mutate_offset(self, selector: str, offset_x: int = 15, offset_y: int = 15):
        """变异3：元素位移，视觉上偏移，模拟前端排版微调"""
        self.page.evaluate(f'''
            () => {{
                const el = document.querySelector("{selector}");
                if(el) {{
                    const rect = el.getBoundingClientRect();
                    el.style.position = "relative";
                    el.style.left = "{offset_x}px";
                    el.style.top = "{offset_y}px";
                }}
            }}
        ''')

    def mutate_text(self, selector: str, new_text: str = "mutated_text"):
        """变异4：修改元素文本（针对text定位）"""
        self.page.evaluate(f'''
            () => {{
                const el = document.querySelector("{selector}");
                if(el) el.innerText = "{new_text}";
            }}
        ''')

    def remove_selector_attr(self, selector: str):
        """变异5：删除id、class，清空定位特征"""
        self.page.evaluate(f'''
            () => {{
                const el = document.querySelector("{selector}");
                if(el) {{
                    el.removeAttribute("id");
                    el.removeAttribute("class");
                }}
            }}
        ''')

    def get_all_mutators(self) -> List[Dict]:
        """返回所有变异类型，用于批量循环执行"""
        return [
            {"name": "mutate_id", "func": self.mutate_id, "desc": "修改元素ID"},
            {"name": "mutate_class", "func": self.mutate_class, "desc": "修改class"},
            {"name": "mutate_offset", "func": self.mutate_offset, "desc": "元素偏移"},
            {"name": "mutate_text", "func": self.mutate_text, "desc": "修改文本"},
            {"name": "remove_attr", "func": self.remove_selector_attr, "desc": "删除id/class"},
        ]
