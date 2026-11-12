from playwright.sync_api import Page, expect
from core.vision_agent import VisionAgentModule
from core.task_planner import TaskPlanner
from core.base_page import BasePage
import time


class WebTestAgent:
    def __init__(self, page: Page, vision: VisionAgentModule):
        self.page = page
        self.vision = vision
        self.planner = TaskPlanner()
        self.base = BasePage(page, vision, case_name="agent_nlp_run")
        self.element_map = {
            "用户名输入框": {
                "element_id": "user_input",
                "desc": "用户名输入框",
                "locator": ["css", "#username"],
                "template_key": "user_input"
            },
            "密码输入框": {
                "element_id": "pwd_input",
                "desc": "密码输入框",
                "locator": ["css", "#password"],
                "template_key": "pwd_input"
            },
            "登出按钮": {
                "element_id": "logout_btn",
                "desc": "登出按钮",
                "locator": ["css", "a[href='/practice-test-login']"],
                "template_key": "logout_btn"
            },
            "登出按钮": {
                "element_id": "logout_btn",
                "desc": "登出按钮",
                "locator": ["css", "#logout"],
                "template_key": "logout_btn"
            }
        }

    def run(self, user_command: str):
        print(f"\n🤖 Agent收到指令：{user_command}")
        steps = self.planner.plan(user_command)
        print(f"📋 拆解步骤：{steps}")

        for step in steps:
            action = step["action"]
            print(f"\n👉 执行动作：{step}")
            if action == "goto":
                self.page.goto(step["url"])
            elif action == "input":
                elem_desc = step["desc"]
                elem_def = self.element_map[elem_desc]
                self.base._input_with_heal(elem_def, step["value"])
            elif action == "click":
                elem_desc = step["desc"]
                elem_def = self.element_map[elem_desc]
                self.base._click_with_heal(elem_def)
            elif action == "assert_vision":
                print("💡 切换原生文本断言，跳过视觉模型调用")
                assert_desc = step["desc"]
                if "登录成功" in assert_desc:
                    expect(self.page.locator("h1")).to_have_text("Logged In Successfully")
                    print("✅ 登录成功断言通过")
                elif "密码错误" in assert_desc:
                    expect(self.page.locator("#error")).to_contain_text("password is invalid")
                    print("✅ 密码错误提示断言通过")
                elif "用户名不存在" in assert_desc:
                    expect(self.page.locator("#error")).to_contain_text("username is invalid")
                    print("✅ 用户名不存在提示断言通过")
                elif "登出后回到登录页面" in assert_desc:
                    expect(self.page.locator("#username")).to_be_visible()
                    print("✅ 登出成功，返回登录页断言通过")
                else:
                    raise Exception(f"未支持的断言描述：{assert_desc}")
            elif action == "wait":
                time.sleep(step["ms"] / 1000)
            else:
                raise Exception(f"未知动作 {action}")
        print("\n🎉 全部任务执行完成！")
