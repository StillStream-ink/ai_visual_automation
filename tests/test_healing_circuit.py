import allure
import pytest
from playwright.sync_api import Page
from healing.exceptions import CircuitBreakError


@allure.feature("AI视觉自愈")
@allure.story("熔断保护")
@allure.title("连续识别失败，框架内部触发熔断抛出异常")
@pytest.mark.xfail(reason="Mock模式固定返回坐标，不会失败；切换真实视觉模型后可正常触发熔断")
def test_healing_circuit(pw_page: Page, vision_agent):
    with pytest.raises(CircuitBreakError):
        for _ in range(5):
            vision_agent.find_element_coordinates(b"fake", "wrong_key_001")
