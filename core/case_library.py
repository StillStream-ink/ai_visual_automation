import yaml
from pathlib import Path

# 用例存放目录，放在项目根目录
CASE_DIR = Path("./case_library")
CASE_DIR.mkdir(exist_ok=True)


def save_case(case_name: str, script: str):
    """保存自动化指令用例"""
    save_path = CASE_DIR / f"{case_name}.yaml"
    data = {
        "case_name": case_name,
        "script": script
    }
    with open(save_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def load_case(case_name: str) -> str:
    """读取用例，返回指令脚本"""
    load_path = CASE_DIR / f"{case_name}.yaml"
    with open(load_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["script"]


def list_all_cases() -> list[str]:
    """获取全部自动化用例名称"""
    yaml_files = list(CASE_DIR.glob("*.yaml"))
    return [file.stem for file in yaml_files]


def remove_case(case_name: str):
    """删除自动化用例"""
    del_path = CASE_DIR / f"{case_name}.yaml"
    if del_path.exists():
        del_path.unlink()
