from core.settings import settings


class ElementFilter:
    def __init__(self):
        self.confidence_threshold = float(settings.get("healing.confidence_threshold", 0.7))
        self.black_list = set(settings.get("vision.black_list", []))
        self.white_list = set(settings.get("vision.white_list", []))
        self.enable_white = len(self.white_list) > 0

    def is_black(self, template_key: str) -> bool:
        """是否在黑名单"""
        return template_key in self.black_list

    def pass_white(self, template_key: str) -> bool:
        """白名单校验：开启白名单时，必须在白名单内才放行"""
        if not self.enable_white:
            return True
        return template_key in self.white_list

    def confidence_ok(self, confidence: float) -> bool:
        """置信度校验"""
        return confidence >= self.confidence_threshold

    def check(self, template_key: str, confidence: float) -> tuple[bool, str]:
        """综合校验，返回是否放行 + 原因"""
        if self.is_black(template_key):
            return False, "命中黑名单"
        if not self.pass_white(template_key):
            return False, "不在白名单内"
        if not self.confidence_ok(confidence):
            return False, f"置信度{confidence}低于阈值{self.confidence_threshold}"
        return True, "校验通过"
