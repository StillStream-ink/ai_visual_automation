# tools/clear_heal_cache.py
from pathlib import Path
import yaml
import sys

REPAIR_YAML_PATH = Path("assets/element_repair.yaml")
CIRCUIT_BREAK_PATH = Path("assets/circuit_break_cache.json")
LOG_PATH = Path("logs/healing.jsonl")

def clear_all_cache():
    # 清空自愈yaml
    if REPAIR_YAML_PATH.exists():
        REPAIR_YAML_PATH.unlink()
        print("✅ 自愈定位yaml缓存已清空")
    else:
        print("ℹ️ yaml缓存文件不存在")

    # 清空熔断缓存
    if CIRCUIT_BREAK_PATH.exists():
        CIRCUIT_BREAK_PATH.unlink()
        print("✅ 熔断缓存已清空")
    else:
        print("ℹ️ 熔断缓存文件不存在")

    # 清空自愈日志
    if LOG_PATH.exists():
        LOG_PATH.unlink()
        print("✅ 自愈日志文件已清空")
    else:
        print("ℹ️ 自愈日志文件不存在")

def remove_one(element_id: str):
    if not REPAIR_YAML_PATH.exists():
        print("ℹ️ 缓存文件不存在")
        return
    with open(REPAIR_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if element_id in data:
        del data[element_id]
        with open(REPAIR_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"✅ [{element_id}] 缓存删除成功")
    else:
        print(f"ℹ️ [{element_id}] 无缓存记录")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        clear_all_cache()
    elif len(sys.argv) == 2:
        remove_one(sys.argv[1])
    else:
        print("用法：")
        print("  python tools/clear_heal_cache.py        # 清空全部缓存+熔断+日志")
        print("  python tools/clear_heal_cache.py username_input # 删除指定元素缓存")