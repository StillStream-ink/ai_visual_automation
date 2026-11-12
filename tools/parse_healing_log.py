import json
from pathlib import Path
from collections import Counter

LOG_PATH = Path("logs/healing.jsonl")
# 自动创建logs目录
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def parse_healing_log():
    if not LOG_PATH.exists():
        print(f"日志文件不存在：{LOG_PATH}")
        print("👉 原因：本次用例全部原生定位成功，还没有产生自愈日志记录！")
        print("👉 你可以故意改错定位符，触发视觉自愈，运行后就会生成日志")
        return

    counter = Counter()
    case_set = set()
    elem_set = set()
    heal_success_list = []
    heal_fail_list = []
    circuit_break_list = []

    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            status = data.get("status")
            case_name = data.get("case_name")
            elem_id = data.get("element_id")

            counter[status] += 1
            case_set.add(case_name)
            elem_set.add(elem_id)

            if status == "heal_success":
                heal_success_list.append(data)
            elif status == "heal_fail":
                heal_fail_list.append(data)
            elif status == "circuit_break":
                circuit_break_list.append(data)

    print("=" * 60)
    print("📊 自愈日志统计汇总")
    print("=" * 60)
    print(f"总用例数量：{len(case_set)}")
    print(f"涉及元素数量：{len(elem_set)}")
    print("-" * 60)
    print("状态统计：")
    for k, v in counter.most_common():
        print(f"  {k:<22} : {v} 次")
    print("-" * 60)
    print(f"✅ 自愈成功次数：{len(heal_success_list)}")
    print(f"❌ 自愈失败次数：{len(heal_fail_list)}")
    print(f"⛔ 熔断拦截次数：{len(circuit_break_list)}")
    print("=" * 60)

    if heal_success_list:
        print("\n最近5条自愈成功记录：")
        for item in heal_success_list[-5:]:
            extra = item.get("extra", {})
            print(f"  [{item['datetime']}] case:{item['case_name']} | elem:{item['element_id']} | coord:{extra.get('coord')}")

if __name__ == "__main__":
    parse_healing_log()