# AI Visual Automation 视觉自愈自动化测试框架

基于 Playwright 实现 UI 自动化自愈框架，解决前端迭代时 DOM 的 id/class/selector 改动，导致传统自动化脚本直接失效的痛点。优先 DOM 定位，失败后自动走视觉识别自愈链路；内置 Mock 视觉 Agent 用于本地调试，支持无缝切换 GLM-4V/Ollama 多模态模型。

## ✨ 核心特性

1. 定位降级策略：优先原生选择器定位，DOM 定位失败自动触发视觉自愈
2. 可插拔视觉 Agent：Mock 演示模式（固定坐标）、真实 VLM 模型模式
3. 自愈风控组件
   - 元素坐标缓存：YAML 持久化 + TTL 过期，减少大模型调用、降低耗时
   - 置信度校验：低于阈值直接判定识别失败，规避误识别
   - 时间窗口熔断：短时间连续识别失败触发熔断，防止雪崩调用
   - 元素黑白名单：精准管控需要自愈的元素
4. 测试体系：pytest 用例集，覆盖缓存命中、熔断、DOM 变异自愈场景
5. 测试报告：支持 pytest-html 单文件内嵌报告、Allure 报告
6. 失败自动截图，方便排查问题

## 📁 项目目录

```text
ai_visual_automation/
├── healing/
│   ├── __init__.py
│   ├── vision_agent.py              # BaseVisionAgent、MockVisionAgent
│   ├── cache_service.py             # ElementCacheService 坐标缓存 TTL 持久化
│   ├── filter.py                    # ElementFilter 置信度 + 黑白名单
│   ├── circuit_breaker.py           # TimeWindowCircuitBreaker 时间窗口熔断
│   ├── exceptions.py                # 自定义异常
│   └── coord_config.py
├── core/
│   └── settings.py                  # 全局配置：置信阈值、黑白名单
├── tests/
│   ├── test_healing_cache_hit.py    # 缓存命中场景
│   ├── test_healing_circuit.py      # 熔断场景（xfailed，预期失败）
│   ├── test_healing_demo.py         # 基础自愈演示
│   ├── test_healing_mutate.py       # SauceDemo DOM 变异自愈
│   └── test_healing_mutate_local.py # 本地页面 DOM 变异自愈
├── assets/
│   └── element_repair.yaml          # 缓存持久化文件
├── conftest.py                      # pytest fixture、失败截图钩子
├── requirements.txt
└── README.md
```

## 🧩 技术栈

- Python 3.10+
- Playwright：浏览器自动化
- Pytest：测试执行框架
- PyYAML：缓存持久化、配置读取
- pytest-html / allure-pytest：测试报告
- 可扩展：GLM-4V / Ollama 多模态视觉大模型

## 🚀 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 chromium 浏览器
playwright install chromium

# 执行全部用例，生成单文件 html 报告（无需 Java）
pytest tests/ --html=report.html --self-contained-html
```

执行结果说明：

- 4 passed：自愈、缓存、DOM 变异等正向场景
- 1 xfailed：熔断用例，属于预期失败，用来验证熔断保护逻辑

## 📌 核心执行链路

flowchart TD
    A[测试用例启动] --> B[尝试DOM选择器定位元素]
    B -->|定位成功| C[执行页面动作：输入/点击]
    B -->|定位失败| D[页面截图]
    D --> E[调用 VisionAgent 视觉识别]
    E --> F{ElementFilter校验}
    F -->|置信度不足 / 黑名单| G[识别失败，重试计数+1]
    F -->|校验通过| H[写入TTL坐标缓存]
    H --> C
    G --> I{是否达到熔断阈值}
    I -->|未达到| D
    I -->|达到阈值| J[触发时间窗口熔断，终止任务]
    C --> K[用例执行结束，输出日志&截图]
    J --> K

## 🧩 系统模块分层架构

flowchart LR
    subgraph 测试层
        T[pytest 测试用例<br/>缓存/熔断/DOM变异场景]
    end
    subgraph 自愈核心层
        S[自愈调度主逻辑]
        F[ElementFilter<br/>置信度 + 黑白名单]
        C[ElementCacheService<br/>YAML TTL缓存]
        B[TimeWindowCircuitBreaker<br/>时间窗口熔断]
    end
    subgraph 视觉接入层
        Base[BaseVisionAgent 抽象接口]
        Mock[MockVisionAgent<br/>本地调试]
        VLM[真实VLM实现<br/>GLM-4V / Ollama 扩展]
    end

    T --> S
    S --> F
    S --> C
    S --> B
    S --> Base
    Base --> Mock
    Base --> VLM

## 📌 核心执行链路

```text
尝试 DOM 选择器定位元素
    ↓ 定位成功 → 执行点击/输入动作
    ↓ 定位失败 → 页面截图 → 调用视觉 Agent 识别坐标
    ↓ 识别成功（置信度达标）→ 写入缓存 → 执行动作
    ↓ 多次识别失败 → 触发熔断，终止任务，抛出异常
```

## 🧩 扩展接入真实视觉大模型

继承抽象类 `BaseVisionAgent`，重写 `find_element_coordinates` 方法：

1. 将截图 base64 传入 VLM（GLM-4V/Ollama）
2. 解析返回坐标、置信度、提示信息
3. 返回 `(x, y, confidence, msg)` 四元组，原有自愈逻辑完全不用改动

## 📸 截图占位

- 测试报告概览截图
- DOM 变异自愈执行日志截图
- 缓存 yaml 文件示例截图

## 📄 版本说明

当前版本：v1.0.0

- ✅ 已完成：自愈引擎、Mock 视觉 Agent、TTL 缓存、置信度过滤、黑白名单、时间窗口熔断、DOM 变异测试套件、html 测试报告
- ⏳ 待扩展：Streamlit 可视化后台、自然语言指令编排、图像对比、AI 用例评审

## License

MIT
