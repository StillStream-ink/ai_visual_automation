import allure
from healing.vision_agent import BaseVisionAgent
from healing.cache_service import ElementCacheService
from conftest import log_healing_event

@allure.feature("AI视觉自愈")
@allure.story("元素坐标缓存")
def test_healing_cache_hit(pw_page, vision_agent: BaseVisionAgent):
    cache = ElementCacheService()
    template_key = "login_username_demo_001"
    img_bytes = b"fake_img"

    # 第一次：调用视觉识别，写入缓存
    x1, y1, conf1, msg1 = vision_agent.find_element_coordinates(img_bytes, template_key)
    cache.set(template_key, (x1, y1), conf1)

    # 第二次：走缓存命中
    res = cache.get(template_key)
    assert res is not None
    (x2, y2) = res.locator
    conf2 = res.confidence
    assert x1 == x2
    assert y1 == y2
    assert conf1 == conf2
