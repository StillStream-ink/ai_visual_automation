# 架构说明
## 整体架构
本项目是一套UI自动化自愈框架，采用「Web后台 + 指令引擎 + 自愈核心 + 视觉Agent」四层结构：
1. 接入层：Streamlit Web后台（app.py），提供用例管理、参数配置、实时日志、指标看板、报告预览
2. 指令解析层：mcp_agent.py，负责解析自然语言测试步骤，编排浏览器执行流程
3. 自愈核心层：优先DOM定位，定位失败后触发视觉自愈；内置坐标缓存、时间窗口熔断、置信度校验风控
4. 视觉识别层：vision/vision_agent.py，抽象视觉接口，支持 Mock、录制JSON、Ollama多模态三种实现模式

## 文件模块职责
- app.py：Streamlit可视化后台入口
- mcp_agent.py：自然语言指令解析Agent
- review_agent.py：AI用例评审Agent（开发中）
- vision/vision_agent.py：视觉识别抽象类与多实现
- conftest.py：pytest全局fixture、日志钩子、失败截图
- tests/：自愈能力验证用例
  - test_healing_demo.py：基础登录自愈演示
  - test_healing_mutate.py：DOM变异自愈测试
  - test_healing_cache_hit.py：缓存命中逻辑验证
  - test_healing_circuit.py：熔断机制验证
- tools/：辅助工具
  - clear_heal_cache.py：清空元素缓存
  - parse_healing_log.py：解析自愈日志，统计指标
- file_parser.py：文档解析工具，用于需求文档上传
- healing_logs.json：自愈运行日志持久化存储
- assets/：静态资源、模板文件、项目截图

## 执行流程
读取自然语言用例 → 尝试CSS/XPath DOM定位
→ 定位成功：执行页面动作
→ 定位失败：页面截图 → 调用视觉Agent识别元素
→ 识别成功：写入坐标缓存，执行动作
→ 多次识别失败：触发熔断，终止任务，输出失败日志

## 扩展方向
1. 增加异步任务队列，支持批量用例调度
2. 对外提供HTTP接口，可供其他测试平台调用
3. 完善RAG能力，基于需求文档自动生成测试用例
4. 增强图像对比功能，用于页面快照校验