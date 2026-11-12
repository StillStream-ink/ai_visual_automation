# core/llm_case_generator.py
"""
AI 测试用例生成 + 缺陷提取
无Key时返回模拟结果；有Key时调用智谱文本模型
"""
from openai import OpenAI
from core.config import llm_cfg

_client = None
if llm_cfg.zhipu_key and llm_cfg.zhipu_key.strip():
    try:
        _client = OpenAI(api_key=llm_cfg.zhipu_key, base_url=llm_cfg.base_url)
    except Exception:
        _client = None


def generate_test_cases(requirement: str) -> str:
    if not _client:
        return ("【模拟模式】需配置 ZHIPUAI_API_KEY 才能生成真实用例\n\n"
                "### 模拟用例示例\n"
                "| 用例ID | 模块 | 标题 | 前置 | 步骤 | 预期 | 优先级 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| TC-001 | 登录 | 正确账号密码登录成功 | 已注册账号 | 1.输入账号 2.输入密码 3.点击登录 | 跳转首页 | 高 |\n"
                "| TC-002 | 登录 | 空用户名登录 | 进入登录页 | 1.密码留空 2.点击登录 | 提示'请输入用户名' | 高 |")
    prompt = ("你是测试专家，基于下面需求生成结构化测试用例：包含 用例ID、模块、标题、"
             "前置条件、步骤、预期结果、优先级，用Markdown表格输出。\n需求：" + requirement)
    resp = _client.chat.completions.create(
        model=llm_cfg.text_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def extract_defect(requirement: str, case_text: str) -> str:
    if not _client:
        return ("【模拟模式】需配置 ZHIPUAI_API_KEY 才能提取缺陷\n\n"
                "### 模拟缺陷清单\n"
                "1. **边界缺失**（高）：未覆盖输入长度上限、特殊字符、空值场景\n"
                "2. **异常处理缺失**（中）：未定义接口异常报错提示规范\n"
                "3. **并发场景缺失**（中）：未明确重复提交/并发处理的兜底逻辑")
    prompt = ("根据需求和测试用例，识别潜在缺陷风险点，输出缺陷清单：缺陷标题、风险等级、描述、建议。\n"
              f"需求：{requirement}\n测试用例：{case_text}")
    resp = _client.chat.completions.create(
        model=llm_cfg.text_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content
