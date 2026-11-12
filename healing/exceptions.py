class HealingBaseError(Exception):
    """自愈组件基础异常"""
    pass


class LocatorNotFoundError(HealingBaseError):
    """原生定位器查找失败，可进入自愈流程"""
    pass


class VisionRecognizeError(HealingBaseError):
    """视觉模型识别元素失败"""
    pass


class CircuitBreakError(HealingBaseError):
    """熔断拦截，停止自愈"""
    pass


class CacheValidateFailedError(HealingBaseError):
    """缓存定位校验失败，缓存失效"""
    pass
