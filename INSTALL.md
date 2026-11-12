# 安装部署文档

## 环境要求

Python >= 3.10
推荐使用 Anaconda / Miniconda 独立虚拟环境，避免包版本冲突

### 1. 创建虚拟环境

```bash
conda create -n visual_auto python=3.10
conda activate visual_auto
```

### 2. 依赖安装

```
pip install -r requirements.txt
# 安装playwright chromium浏览器驱动
playwright install chromium
```

### 3. 配置说明

1. 可选配置文件 `config.yaml`：浏览器参数、自愈开关、置信度、熔断阈值等基础配置
2. `.env`：环境私有变量，优先级高于 yaml，存放模型地址、密钥等敏感信息

> 示例 .env

```
LLM_API_KEY=xxx
OLLAMA_BASE_URL=http://127.0.0.1:11434
VISION_MODEL=llava
CONFIDENCE_THRESHOLD=0.8
CIRCUIT_WINDOW_SECONDS=10
CIRCUIT_LIMIT=3
VIEWPORT_WIDTH=1280
VIEWPORT_HEIGHT=720
```

### 4. 启动命令

```
# 启动Streamlit可视化后台
streamlit run app.py

# 执行底层自愈demo测试用例
pytest tests/test_healing_demo.py -v
```

## 常见问题

1. Allure 报错：缺少 Java 环境，可以跳过 Allure，直接使用平台内置 Markdown 报告
2. Ollama 识别失败：确认 ollama 服务正常运行，多模态模型已经提前 pull 到本地
3. 截图 / 日志写入失败：logs、screenshots、reports 目录程序会自动创建；自动创建失败时手动新建即可
4. 端口占用：streamlit 默认 8501 端口，可指定端口启动

```
streamlit run app.py --server.port=8502
```
