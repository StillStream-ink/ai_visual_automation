import pytest
import allure
import json
import time
import os
from pathlib import Path
from core.settings import settings
from playwright.sync_api import sync_playwright
from healing.vision_agent import MockVisionAgent, RecordVisionAgent, OllamaVisionAgent
from healing.exceptions import VisionRecognizeError

# 修复：yaml节点是 storage.log_file
LOG_PATH = Path(settings.get("storage.log_file", "./reports/healing_log.jsonl"))
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_healing_event(event: dict):
    """写入结构化日志，给看板 & Allure汇总消费"""
    event["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="function")
def pw_page(playwright):
    headless_flag = settings.get("browser.headless", False)
    browser_timeout = settings.get("browser.timeout", 30000)
    view_w = settings.get("browser.viewport_width", 1280)
    view_h = settings.get("browser.viewport_height", 720)

    browser = playwright.chromium.launch(headless=headless_flag)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(browser_timeout)
    page.set_viewport_size({"width": view_w, "height": view_h})
    yield page
    context.close()
    browser.close()


@pytest.fixture(scope="function")
def vision_agent():
    agent_type = settings.get("vision.agent_type", "mock")
    record_json_path = settings.get("vision.record_json_path", "config/mock_vision_result.json")
    ollama_model = settings.get("vision.ollama.model", "moondream")

    if agent_type == "mock":
        agent = MockVisionAgent()
    elif agent_type == "record":
        agent = RecordVisionAgent(json_path=record_json_path)
    elif agent_type == "ollama":
        agent = OllamaVisionAgent(model_name=ollama_model)
    else:
        raise ValueError("vision.agent_type 仅支持 mock / record / ollama")
    return agent


@pytest.fixture(scope="function", autouse=True)
def case_record(request):
    case_name = request.node.name
    start = time.time()
    yield
    duration = round(time.time() - start, 2)
    # 安全读取rep_call，做判断兜底
    if hasattr(request.node, "rep_call"):
        status = "passed" if request.node.rep_call.passed else "failed"
    else:
        status = "unknown"

    log_healing_event({
        "type": "case_finish",
        "case_name": case_name,
        "duration": duration,
        "status": status
    })


# ========== 新增：用例失败自动截图，打入Allure ==========
@pytest.fixture(scope="function", autouse=True)
def capture_screenshot_on_failure(request, pw_page):
    yield
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshot_bytes = pw_page.screenshot(full_page=True)
        allure.attach(
            screenshot_bytes,
            name="失败页面截图",
            attachment_type=allure.attachment_type.PNG
        )


@pytest.fixture(scope="session", autouse=True)
def healing_summary_after_run():
    yield
    # ========== 在这里增加固定业务信息：测试人员、项目、站点 ==========
    env_content = f"""
项目名称=AI视觉自愈自动化测试框架
测试人员=測測
测试站点=SauceDemo
站点地址=https://www.saucedemo.com/
browser.driver_type={settings.get("browser.driver_type")}
browser.headless={settings.get("browser.headless")}
browser.timeout={settings.get("browser.timeout")}
browser.viewport_width={settings.get("browser.viewport_width")}
browser.viewport_height={settings.get("browser.viewport_height")}
healing.enable={settings.get("healing.enable")}
healing.confidence_threshold={settings.get("healing.confidence_threshold")}
healing.max_retry={settings.get("healing.max_retry")}
healing.circuit_break_limit={settings.get("healing.circuit_break_limit")}
vision.agent_type={settings.get("vision.agent_type")}
llm.model_name={settings.get("llm.model_name")}
""".strip()
    env_file = Path("allure-results/environment.properties")
    # 自动创建目录，解决FileNotFoundError
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(env_content, encoding="utf-8")

    # 写入 executor.json 填充右下角Executors
    executor_info = {
        "name": "AI视觉自愈自动化框架",
        "type": "pytest",
        "url": "",
        "build": "v1.0.0",
        "reportName": "AI自愈测试报告"
    }
    executor_file = Path("allure-results/executor.json")
    executor_file.write_text(json.dumps(executor_info, ensure_ascii=False, indent=2), encoding="utf-8")

    if not LOG_PATH.exists():
        allure.attach(
            "本次执行无自愈日志（全部原生定位成功，未触发视觉自愈）",
            name="本轮自愈总汇总",
            attachment_type=allure.attachment_type.TEXT
        )
        return

    heal_success = 0
    heal_fail = 0
    circuit_break = 0
    cache_hit = 0
    native_success = 0
    native_fail = 0
    block_count = 0
    case_pass = 0
    case_fail = 0

    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                evt_type = item["type"]
                if evt_type == "healing_final_success":
                    heal_success += 1
                elif evt_type == "healing_final_fail":
                    heal_fail += 1
                elif evt_type == "circuit_break":
                    circuit_break += 1
                elif evt_type == "cache_hit":
                    cache_hit += 1
                elif evt_type == "native_locate_success":
                    native_success += 1
                elif evt_type == "native_locate_fail":
                    native_fail += 1
                elif evt_type == "healing_block":
                    block_count += 1
                elif evt_type == "case_finish":
                    if item["status"] == "passed":
                        case_pass += 1
                    elif item["status"] == "failed":
                        case_fail += 1
            except Exception:
                continue

    # Markdown表格版本
    summary_md = f"""
# AI视觉自愈汇总
| 指标 | 数值 |
| ---- | ---- |
| ✅ 自愈成功次数 | {heal_success} |
| ❌ 自愈最终失败 | {heal_fail} |
| ⛔ 熔断拦截 | {circuit_break} |
| 📦 缓存命中 | {cache_hit} |
| 🔍 原生定位成功 | {native_success} |
| ⚠️ 原生定位失败（触发自愈） | {native_fail} |
| 🚫 黑白名单拦截 | {block_count} |
| ✅ 用例通过 | {case_pass} |
| ❌ 用例失败 | {case_fail} |
"""
    allure.attach(
        summary_md,
        name="本轮自愈总汇总",
        attachment_type=allure.attachment_type.HTML
    )
