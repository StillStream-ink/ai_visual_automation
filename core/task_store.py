# core/task_store.py
import json
import uuid
from pathlib import Path
from datetime import datetime

TASK_FILE = Path("assets/tasks.json")
TASK_FILE.parent.mkdir(exist_ok=True)

# ----------------------常量定义（与app.py对应）----------------------
STATUS = {
    "pending": "待执行",
    "running": "执行中",
    "success": "执行成功",
    "fail": "执行失败",
    "paused": "已暂停",
    "canceled": "已取消"
}
MODULES = ["登录模块", "订单模块", "商品模块", "支付模块", "用户管理模块", "MCP‑AI网页自动化测试"]
TYPES = ["功能测试", "回归测试", "兼容性测试", "探索性测试"]
PRIORITIES = ["高", "中", "低"]

STATUS_COLOR = {
    "pending": "#888888",
    "running": "#3498db",
    "success": "#27ae60",
    "fail": "#e74c3c",
    "paused": "#f39c12",
    "canceled": "#95a5a6"
}
PRIORITY_COLOR = {
    "高": "#e74c3c",
    "中": "#f39c12",
    "低": "#7f8c8d"
}

# 每个状态允许的操作按钮
STATUS_ACTIONS = {
    "pending": ["edit", "execute", "delete", "copy"],
    "running": ["pause", "cancel", "detail"],
    "success": ["retry", "detail", "copy", "delete"],
    "fail": ["retry", "edit", "detail", "copy", "delete"],
    "paused": ["continue", "cancel", "detail"],
    "canceled": ["retry", "edit", "detail", "copy", "delete"],
}

# 状态流转：from_status -> {to_status}
ALLOW_TRANSITION = {
    "pending": {"running", "canceled"},
    "running": {"paused", "success", "fail", "canceled"},
    "paused": {"running", "canceled"},
    "success": {"running"},
    "fail": {"running"},
    "canceled": {"running"},
}

def _load_all():
    if not TASK_FILE.exists():
        return []
    with open(TASK_FILE, "r", encoding="utf‑8") as f:
        return json.load(f)

def _save_all(lst):
    with open(TASK_FILE, "w", encoding="utf‑8") as f:
        json.dump(lst, f, ensure_ascii=False, indent=2)

def validate_task(data: dict) -> tuple[bool, str]:
    """校验新建/编辑任务字段"""
    name = data.get("name", "").strip()
    if len(name) < 2 or len(name) > 100:
        return False, "任务名称长度必须2‑100字符"
    lst = _load_all()
    for item in lst:
        if item["name"] == name:
            return False, "任务名称不能重复"
    steps = data.get("steps", "").strip()
    if len(steps) < 10 or len(steps) > 2000:
        return False, "任务步骤长度10‑2000字符"
    expected = data.get("expected", "").strip()
    if len(expected) <10 or len(expected)>1000:
        return False, "预期结果长度10‑1000字符"
    return True, ""

def create_task(data: dict) -> tuple[bool, str]:
    ok, msg = validate_task(data)
    if not ok:
        return False, msg
    all_tasks = _load_all()
    new_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y‑%m‑%d %H:%M:%S")
    task = {
        "id": new_id,
        "name": data["name"].strip(),
        "module": data["module"],
        "task_type": data["task_type"],
        "priority": data["priority"],
        "precondition": data.get("precondition", ""),
        "steps": data["steps"],
        "expected": data["expected"],
        "requirement_docs": data.get("requirement_docs", []),
        "remark": data.get("remark", ""),
        "status": "pending",
        "created_time": now,
        "exec_log": "",
        "source": data.get("source", "")
    }
    all_tasks.append(task)
    _save_all(all_tasks)
    return True, "ok"

def get_task(tid: str):
    for t in _load_all():
        if t["id"] == tid:
            return t
    return None

def update_task(tid: str, data: dict) -> tuple[bool, str]:
    tasks = _load_all()
    idx = None
    for i, t in enumerate(tasks):
        if t["id"] == tid:
            idx = i
            break
    if idx is None:
        return False, "任务不存在"
    old = tasks[idx]
    if old["status"] == "running":
        return False, "执行中任务禁止编辑"
    # 如果名称发生变更才做重名校验
    if data["name"].strip() != old["name"]:
        ok, msg = validate_task(data)
        if not ok:
            return False, msg
    tasks[idx]["name"] = data["name"].strip()
    tasks[idx]["module"] = data["module"]
    tasks[idx]["task_type"] = data["task_type"]
    tasks[idx]["priority"] = data["priority"]
    tasks[idx]["precondition"] = data.get("precondition","")
    tasks[idx]["steps"] = data["steps"]
    tasks[idx]["expected"] = data["expected"]
    tasks[idx]["requirement_docs"] = data.get("requirement_docs",[])
    tasks[idx]["remark"] = data.get("remark","")
    _save_all(tasks)
    return True, "ok"

def delete_task(tid: str) -> tuple[bool, str]:
    tasks = _load_all()
    new_list = [t for t in tasks if t["id"] != tid]
    if len(new_list) == len(tasks):
        return False, "未找到任务"
    _save_all(new_list)
    return True, "ok"

def list_tasks():
    return _load_all()

def transition(tid: str, to_status: str) -> tuple[bool, str]:
    """状态流转"""
    tasks = _load_all()
    target = None
    idx = None
    for i, t in enumerate(tasks):
        if t["id"] == tid:
            target = t
            idx = i
            break
    if target is None:
        return False, "任务不存在"
    frm = target["status"]
    if to_status not in ALLOW_TRANSITION.get(frm, set()):
        return False, f"不允许状态流转 {STATUS[frm]} → {STATUS[to_status]}"
    tasks[idx]["status"] = to_status
    _save_all(tasks)
    return True, "ok"

def filter_tasks(keyword="", module="", ttype="", status="", priority=""):
    lst = list_tasks()
    res = []
    for item in lst:
        if keyword:
            kw = keyword.lower()
            if kw not in item["name"].lower() and kw not in item["steps"].lower():
                continue
        if module and item["module"] != module:
            continue
        if ttype and item["task_type"] != ttype:
            continue
        if status and item["status"] != status:
            continue
        if priority and item["priority"] != priority:
            continue
        res.append(item)
    return res
