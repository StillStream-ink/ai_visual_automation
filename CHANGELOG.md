### ✅ 新增
- 抽象 BaseVisionAgent，统一视觉识别接口，MockAgent本地调试
- ElementCacheService：坐标缓存，yaml持久化，支持TTL过期
- ElementFilter：置信度阈值校验、元素黑白名单过滤
- TimeWindowCircuitBreaker 时间窗口熔断组件
- 5条pytest测试用例：基础自愈、缓存命中、熔断、SauceDemo DOM变异、本地页面DOM变异
- pytest-html单文件内嵌报告，无需Java依赖；兼容Allure报告
- 失败自动截图钩子，便于问题定位

### ✅ 能力闭环
- DOM属性篡改后，传统选择器失效，框架依靠视觉识别完成定位、输入、登录
- 缓存优先策略，减少视觉调用开销
- 多层防护：低置信度拦截、熔断防服务雪崩

### 📋 待迭代规划
- Streamlit可视化后台：用例管理、指标看板、实时日志
- 自然语言指令编排（MCP思路）
- 接入GLM-4V/Ollama真实多模态模型
- 图像对比、AI用例评审