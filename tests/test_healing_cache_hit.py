# tests/test_healing_cache_hit.py
import allure
from healing.cache_service import ElementCacheService
from healing.exceptions import VisionRecognizeError

@allure.feature("AI视觉自愈")
@allure.story("元素坐标缓存")
def test_healing_cache_hit(pw_page, vision_agent):
    cache = ElementCacheService()
    template_key = "login_username_demo_001"
    img_bytes = b"fake_img"

    # 第一次：调用视觉识别，写入缓存
    x1, y1, msg1 = vision_agent.find_element_coordinates(img_bytes, template_key)
    cache.put(template_key, x1, y1)

    # 第二次：直接读取缓存，不调用视觉Agent
    cached = cache.get_cache(template_key)
    assert cached is not None
    x2, y2 = cached
    assert x1 == x2 and y1 == y2
    print(f"\n✅ 缓存命中成功！key={template_key}, cached_x={x2}, cached_y={y2}")
