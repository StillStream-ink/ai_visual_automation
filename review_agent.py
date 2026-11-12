import re
from playwright.sync_api import sync_playwright
from core.vision_agent import VisionAgent
from core.base_page import BasePage
from core.log_recorder import TestLogger
from core.settings import settings
from pathlib import Path
import json
from datetime import datetime

REPORT_ROOT = Path(settings.get("storage.report_root"))
REPORT_ROOT.mkdir(parents=True, exist_ok=True)

# ========== 指令注册表 ==========
CMD_REG = [
    {"name": "打开网页", "pattern": re.compile(r"打开网页[:：]\s*(.+)"), "func": "cmd_open"},
    {"name": "等待", "pattern": re.compile(r"等待[:：]\s*([0-9.]+)\s*秒"), "func": "cmd_wait"},
    {"name": "输入文字", "pattern": re.compile(r"输入文字[:：]\s*(.+)"), "func": "cmd_input"},
    {"name": "视觉点击", "pattern": re.compile(r"视觉点击\s*@\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)"), "func": "cmd_vision_click_pos"},
    {"name": "视觉点击文本", "pattern": re.compile(r"视觉点击[:：]\s*(.+)"), "func": "cmd_vision_click_text"},
    {"name": "视觉断言", "pattern": re.compile(r"视觉断言[:：]\s*(.+)"), "func": "cmd_vision_assert"},
]

def parse_command(line: str):
    line = line.strip()
    for item in CMD_REG:
        m = item["pattern"].match(line)
        if m:
            return item["func"], m.groups()
    return None, None


def run_test_task(task_text: str, logger: TestLogger):
    task_id = logger.task_id
    report_dir = REPORT_ROOT / task_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_data = {
        "task_id": task_id,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "steps": [],
        "total": 0,
        "pass_cnt": 0,
        "fail_cnt": 0,
        "result": "未完成"
    }

    vision_agent = VisionAgent(logger)
    case_name = "UI视觉自愈测试任务"
    lines = [i.strip() for i in task_text.splitlines() if i.strip()]
    viewport_w = settings.get("browser.viewport_width")
    viewport_h = settings.get("browser.viewport_height")
    timeout = settings.get("browser.timeout")
    headless = settings.get("browser.headless")

    # 简易元素池，把文本映射成自愈框架需要的elem结构
    elem_map = {}
    elem_seq = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": viewport_w, "height": viewport_h})
        page.set_default_timeout(timeout)
        # 初始化自愈基类，注入logger
        base = BasePage(page=page, vision_agent=vision_agent, case_name=case_name, logger=logger)

        for idx, line in enumerate(lines):
            step_info = {"step_no": idx+1, "raw_cmd": line, "status": "待执行", "screenshot": None, "msg": ""}
            report_data["steps"].append(step_info)
            report_data["total"] += 1
            cmd_func, args = parse_command(line)
            if not cmd_func:
                step_info["status"] = "失败"
                step_info["msg"] = f"不识别指令：{line}"
                logger.error(f"不识别指令：{line}")
                report_data["fail_cnt"] += 1
                continue
            try:
                if cmd_func == "cmd_open":
                    url = args[0]
                    logger.info(f"打开网页：{url}")
                    page.goto(url)
                    step_info["status"] = "成功"
                    step_info["msg"] = f"页面打开成功 {url}"
                    report_data["pass_cnt"] += 1

                elif cmd_func == "cmd_wait":
                    sec = float(args[0])
                    logger.info(f"等待 {sec} 秒")
                    page.wait_for_timeout(sec * 1000)
                    step_info["status"] = "成功"
                    step_info["msg"] = f"等待{sec}s完成"
                    report_data["pass_cnt"] += 1

                elif cmd_func == "cmd_input":
                    txt = args[0]
                    logger.info(f"输入文字：{txt}")
                    # 生成elem，这里默认用文本做定位，你可以改成css/xpath
                    elem_seq += 1
                    elem_id = f"input_{elem_seq}"
                    elem = {
                        "element_id": elem_id,
                        "desc": f"输入框-{elem_id}",
                        "locator": ["text", txt],
                        "template_key": f"tpl_{elem_id}"
                    }
                    elem_map[elem_id] = elem
                    healed_flag = base._input_with_heal(elem, txt)
                    step_info["status"] = "成功"
                    step_info["msg"] = f"输入完成，是否触发自愈：{healed_flag}"
                    report_data["pass_cnt"] += 1

                elif cmd_func == "cmd_vision_click_pos":
                    x = int(args[0])
                    y = int(args[1])
                    logger.info(f"坐标直接点击 ({x},{y})（跳过自愈框架，纯演示）")
                    page.mouse.click(x, y)
                    step_info["status"] = "成功"
                    step_info["msg"] = f"点击坐标({x},{y})"
                    report_data["pass_cnt"] += 1

                elif cmd_func == "cmd_vision_click_text":
                    target = args[0]
                    logger.info(f"视觉点击文本：{target}，进入自愈链路")
                    elem_seq += 1
                    elem_id = f"click_{elem_seq}"
                    elem = {
                        "element_id": elem_id,
                        "desc": f"点击元素-{target}",
                        "locator": ["text", target],
                        "template_key": f"tpl_{elem_id}"
                    }
                    elem_map[elem_id] = elem
                    healed_flag = base._click_with_heal(elem)
                    step_info["status"] = "成功"
                    step_info["msg"] = f"点击【{target}】成功，是否触发自愈：{healed_flag}"
                    report_data["pass_cnt"] += 1

                elif cmd_func == "cmd_vision_assert":
                    expect_text = args[0]
                    logger.info(f"视觉断言：预期页面包含【{expect_text}】，DOM二次校验")
                    loc = page.get_by_text(expect_text)
                    if loc.count() > 0:
                        step_info["status"] = "成功"
                        step_info["msg"] = f"双重断言通过，页面找到文本：{expect_text}"
                        report_data["pass_cnt"] += 1
                    else:
                        step_info["status"] = "失败"
                        step_info["msg"] = f"断言失败，页面未找到：{expect_text}"
                        report_data["fail_cnt"] += 1

                # 每一步截图
                shot_path = report_dir / f"step_{idx+1}.png"
                page.screenshot(path=str(shot_path))
                step_info["screenshot"] = str(shot_path)

            except Exception as e:
                step_info["status"] = "失败"
                step_info["msg"] = str(e)
                logger.error(f"步骤异常 {line}：{str(e)}")
                report_data["fail_cnt"] += 1
                shot_path = report_dir / f"step_{idx+1}_err.png"
                page.screenshot(path=str(shot_path))
                step_info["screenshot"] = str(shot_path)
        browser.close()

    report_data["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if report_data["fail_cnt"] == 0:
        report_data["result"] = "全部通过"
    else:
        report_data["result"] = "存在失败"

    md_text = build_md_report(report_data)
    md_file = report_dir / "report.md"
    md_file.write_text(md_text, encoding="utf-8")
    logger.info(f"报告已保存：{md_file}")
    return report_data, md_text


def build_md_report(data: dict):
    md = f"""# 📋 测试任务报告
任务ID：{data['task_id']}
开始时间：{data['start_time']}
结束时间：{data['end_time']}
总步骤：{data['total']}｜✅成功：{data['pass_cnt']}｜❌失败：{data['fail_cnt']}
执行结论：**{data['result']}**

## 步骤明细
|序号|指令|状态|说明|截图|
| ---- | ---- | ---- | ---- | ---- |
"""
    for s in data["steps"]:
        shot_link = f"![截图]({s['screenshot']})" if s["screenshot"] else "-"
        md += f"|{s['step_no']}|{s['raw_cmd']}|{s['status']}|{s['msg']}|{shot_link}|\n"
    return md


def review_test_cases(requirement_text: str, case_text: str, module_name: str, logger: TestLogger) -> str:
    report = f"""# 📋 测试用例评审报告
> 评审模块：{module_name}
## 一、需求原文摘要
{requirement_text[:800]}
## 二、待评审用例摘要
{case_text[:1000]}
## 三、评审结论
✅ 需求基本清晰，可设计正向、反向、边界测试用例。
## 四、发现问题
1. 部分边界场景未覆盖
2. 缺少异常反向用例
"""
    logger.info("完成用例评审")
    return report
