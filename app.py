import streamlit as st
import uuid
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

# 路径兜底修复
BASE_PATH = Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH))

from core.settings import settings
from core.log_recorder import TestLogger
from core.case_library import save_case, load_case, list_all_cases, remove_case
from review_agent import run_test_task, review_test_cases

st.set_page_config(page_title="AI智能测试平台", layout="wide", page_icon="🤖", initial_sidebar_state="expanded")
REPORT_ROOT = Path(settings.get("storage.report_root"))
REPORT_ROOT.mkdir(parents=True, exist_ok=True)

# ===================== 新增自愈指标全局缓存 =====================
if "task_running" not in st.session_state:
    st.session_state.task_running = False
if "task_script" not in st.session_state:
    st.session_state.task_script = """打开网页：file:///xxx/test_form.html
等待1秒
输入文字：test123
视觉点击@(109,88)
等待1秒
视觉断言：页面显示提交成功"""
if "healing_metrics" not in st.session_state:
    st.session_state.healing_metrics = {
        "total_trigger": 0,
        "success": 0,
        "hit_cache": 0,
        "circuit_break": 0,
        "history": []
    }

# 全局样式：统一侧边栏、按钮、页面基础风格
st.markdown("""
<style>
/* 全局基础 */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
/* 侧边栏整体 */
[data-testid="stSidebar"] {
    background-color: #fbfbfb;
    border-right: 1px solid #eee;
}
[data-testid="stSidebar"] .stSelectbox label {
    font-size:15px;
    color:#333;
    font-weight:500;
}
/* 按钮全局统一 */
.stButton>button {
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    color:#222;
    padding: 6px 16px;
    transition: 0.2s;
}
.stButton>button:hover {
    border-color:#2563eb;
    color:#2563eb;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
}
.stButton>button:disabled {
    background:#f3f4f6;
    color:#999;
    border-color:#eee;
    box-shadow:none;
}
/* 上传组件 */
[data-testid="stFileUploader"] {
    border-radius: 8px;
}
/* 输入框、滑块 */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    border-radius:8px;
    border:1px solid #e8e8e8;
}
[data-testid="stSlider"] > div {
    padding-top:4px;
}
/* metric卡片美化 */
[data-testid="stMetric"]{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:10px;
    padding:12px;
}
</style>
""", unsafe_allow_html=True)

# ===================== 侧边栏美化（方案B） =====================
with st.sidebar:
    st.markdown("# 🤖 AI视觉测试平台")
    st.divider()
    menu = st.selectbox(
        "导航菜单",
        ["🏠 首页总览", "📋 测试用例评审&生成", "🤖 UI视觉自愈自动化", "📄 测试报告中心", "⚙️ 系统配置"]
    )
    st.divider()
    st.caption("AI视觉自愈自动化框架 v1.0")
    st.caption("© 2026 自动化测试Demo")

if menu == "🏠 首页总览":
    st.markdown("""
    <style>
    .main-title{
        font-size:42px;
        font-weight:700;
        color:#111;
        text-align:center;
        margin-bottom:8px;
    }
    .sub-title{
        font-size:20px;
        color:#666;
        text-align:center;
        margin-bottom:36px;
    }
    .card-box{
        background:#ffffff;
        border: 1px solid #e8e8e8;
        border-radius:12px;
        padding:24px 16px;
        text-align:center;
        height:200px;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        transition: 0.2s;
    }
    .card-box:hover{
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .icon{
        font-size:34px;
        margin-bottom:8px;
    }
    .card-name{
        font-size:19px;
        font-weight:600;
        color:#222;
        margin-bottom:6px;
    }
    .card-desc{
        font-size:14px;
        color:#555;
        line-height:1.5;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">🤖 AI智能测试平台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">用例评审｜AI生成｜UI自动化｜视觉自愈</div>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4, gap="medium")
    with c1:
        st.markdown("""
        <div class="card-box">
            <div class="icon">📋</div>
            <div class="card-name">测试用例评审</div>
            <div class="card-desc">上传需求&用例文档<br>AI评审覆盖度、挖掘需求风险</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card-box">
            <div class="icon">✨</div>
            <div class="card-name">AI生成用例</div>
            <div class="card-desc">基于需求自动生成正向、反向、边界测试用例</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="card-box">
            <div class="icon">👁️</div>
            <div class="card-name">视觉自愈自动化</div>
            <div class="card-desc">自然语言编排步骤<br>DOM失败自动降级视觉自愈</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="card-box">
            <div class="icon">📊</div>
            <div class="card-name">报告中心</div>
            <div class="card-desc">历史任务统一管理<br>在线预览、下载报告与截图</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    # ========== 自愈指标看板（新增） ==========
    st.markdown("### 📈 自愈运行指标看板")
    m = st.session_state.healing_metrics
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("自愈触发次数", value=m["total_trigger"])
    s2.metric("自愈成功次数", value=m["success"])
    s3.metric("缓存命中次数", value=m["hit_cache"])
    s4.metric("熔断触发次数", value=m["circuit_break"])
    if m["total_trigger"] > 0:
        rate = round(m["success"] / m["total_trigger"], 2)
        st.metric("✅ 自愈成功率", f"{rate*100:.1f}%")
    else:
        st.metric("✅ 自愈成功率", "0.0%")

    st.divider()
    # 原有任务统计
    s1,s2,s3,s4 = st.columns(4)
    task_dir = Path(settings.get("storage.report_root"))
    task_list = [x for x in task_dir.iterdir() if x.is_dir()] if task_dir.exists() else []
    total_task = len(task_list)
    success_cnt = 0
    fail_cnt = 0
    for t in task_list:
        md = t / "report.md"
        if md.exists():
            content = md.read_text(encoding="utf-8")
            if "✅ 执行成功" in content:
                success_cnt +=1
            elif "❌ 执行失败" in content:
                fail_cnt +=1
    with s1:
        st.metric("累计任务数", total_task)
    with s2:
        st.metric("成功执行", success_cnt)
    with s3:
        st.metric("失败任务", fail_cnt)
    with s4:
        st.metric("Mock演示模式", "开启" if settings.get("llm.use_mock") else "关闭")

elif menu == "📋 测试用例评审&生成":
    st.header("📋 测试用例评审 & 生成")
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        req_file = st.file_uploader("上传需求文档", type=["txt", "docx", "pdf"])
    with col_up2:
        case_file = st.file_uploader("上传测试用例", type=["xlsx", "xls"])
    module_opt = st.selectbox("选择模块", ["登录模块", "提交表单模块", "购物车模块"])
    btn_review, btn_gen, btn_defect = st.columns(3)
    if btn_review.button("开始AI深度评审", disabled=st.session_state.task_running):
        try:
            if not req_file and not case_file:
                st.warning("⚠️ 请上传需求文档或者测试用例文档！")
            else:
                task_id = str(uuid.uuid4())
                logger = TestLogger(task_id)
                req_txt = req_file.read().decode("utf-8", errors="ignore") if req_file else ""
                case_txt = case_file.read().decode("utf-8", errors="ignore") if case_file else ""
                st.session_state.task_running = True
                with st.spinner("评审中..."):
                    res = review_test_cases(req_txt, case_txt, module_opt, logger)
                    st.markdown(res)
                st.success("✅ 评审完成")
        except Exception as e:
            st.error(f"❌ 评审异常：{str(e)}")
            logger = TestLogger(str(uuid.uuid4()))
            logger.logger.exception("评审任务异常")
        finally:
            st.session_state.task_running = False

elif menu == "🤖 UI视觉自愈自动化":
    st.header("🤖 UI视觉自愈自动化执行")
    st.subheader("📁 自动化指令用例库")
    case_options = ["--新建空白用例--"] + list_all_cases()
    selected_case = st.selectbox("选择历史自动化脚本", case_options)

    col1, col2 = st.columns(2)
    with col1:
        if selected_case != "--新建空白用例--":
            if st.button("✅ 加载选中脚本"):
                st.session_state["task_script"] = load_case(selected_case)
                st.rerun()
    with col2:
        if selected_case != "--新建空白用例--":
            if st.button("🗑️ 删除脚本", type="secondary"):
                remove_case(selected_case)
                st.success("已删除")
                st.rerun()

    case_name = st.text_input("脚本命名（保存到用例库）")
    if st.button("💾 保存当前指令脚本"):
        if case_name.strip() and st.session_state.get("task_script", ""):
            save_case(case_name.strip(), st.session_state["task_script"])
            st.success("✅ 保存成功！")
            st.rerun()
        else:
            st.warning("脚本名称和指令内容不能为空")

    task_script = st.text_area("MCP自动化测试指令脚本", height=220, key="task_script")

    run_btn = st.button("▶ 开始执行任务", disabled=st.session_state.task_running)
    log_container = st.container()
    report_container = st.container()
    if run_btn:
        try:
            tid = str(uuid.uuid4())
            logger = TestLogger(tid)
            st.session_state.task_running = True
            with st.spinner("执行中..."):
                data, md = run_test_task(task_script, logger)
                logger.render_streamlit(log_container)
                report_container.markdown(md)
            st.success("✅ 自动化任务执行完成，查看上方日志与报告")

            # ========== 【重点】跑完任务回写自愈指标 ==========
            # data 里面就是自愈返回指标，你run_test_task返回的data需要是字典：{"total":3,"succ":3,"cache":0,"break":0}
            if isinstance(data, dict):
                st.session_state.healing_metrics["total_trigger"] += data.get("total",0)
                st.session_state.healing_metrics["success"] += data.get("succ",0)
                st.session_state.healing_metrics["hit_cache"] += data.get("cache",0)
                st.session_state.healing_metrics["circuit_break"] += data.get("break",0)
                st.session_state.healing_metrics["history"].append({
                    "time": tid[:8],
                    "succ": data.get("succ",0),
                    "fail": data.get("total",0) - data.get("succ",0)
                })
        except Exception as e:
            st.error(f"❌ 自动化执行异常：{str(e)}")
            logger = TestLogger(str(uuid.uuid4()))
            logger.logger.exception("自动化任务异常")
        finally:
            st.session_state.task_running = False

elif menu == "📄 测试报告中心":
    st.header("📄 历史测试报告")
    try:
        task_list = [p.name for p in REPORT_ROOT.iterdir() if p.is_dir()]
        select_task = st.selectbox("选择任务", ["-"] + task_list)
        if select_task != "-":
            md_path = REPORT_ROOT / select_task / "report.md"
            if md_path.exists():
                st.markdown(md_path.read_text(encoding="utf-8"))
                st.download_button("下载Markdown报告", md_path.read_text(encoding="utf-8"), file_name=f"{select_task}_report.md")
            else:
                st.warning("该任务报告文件丢失")
    except Exception as e:
        st.error(f"❌ 读取报告目录失败：{str(e)}")

    # ========== 进阶：自愈趋势图表 ==========
    st.divider()
    st.markdown("### 📊 自愈执行趋势图")
    hist = st.session_state.healing_metrics["history"]
    if hist:
        df = pd.DataFrame(hist)
        fig = px.line(df, x="time", y=["succ","fail"], title="历次自愈成功/失败次数", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无历史运行数据，执行自动化任务后生成趋势图")

elif menu == "⚙️ 系统配置":
    st.header("⚙️ 平台参数配置")
    try:
        mock_flag = st.checkbox("开启Mock演示模式", value=settings.get("llm.use_mock"))
        conf_th = st.slider("置信度阈值", min_value=0.0, max_value=1.0, value=settings.get("healing.confidence_threshold"), step=0.05)
        max_retry = st.number_input("最大重试次数", min_value=0, value=settings.get("healing.max_retry"))
        circuit_limit = st.number_input("熔断阈值(连续失败次数)", min_value=1, value=settings.get("healing.circuit_break_limit"))
        api_key = st.text_input("LLM API_KEY", value=settings.get("llm.api_key"), type="password")
        if st.button("保存配置", disabled=st.session_state.task_running):
            settings.set("llm.use_mock", mock_flag)
            settings.set("healing.confidence_threshold", conf_th)
            settings.set("healing.max_retry", max_retry)
            settings.set("healing.circuit_break_limit", circuit_limit)
            settings.set("llm.api_key", api_key)
            st.success("✅ 配置已写入yaml，重启服务生效")
    except Exception as e:
        st.error(f"❌ 配置读取/保存异常：{str(e)}")
