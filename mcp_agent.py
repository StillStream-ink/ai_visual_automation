import asyncio
import os
import base64
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

load_dotenv()
SCREENSHOT_FOLDER = "./screenshots"
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)


async def run_test_task(prompt: str):
    log_lines = []
    log_lines.append("🚀 正在启动 Playwright MCP 服务...")

    mcp_client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": [
                "-y", "@playwright/mcp@latest"
            ],
            "transport": "stdio"
        }
    })
    try:
        async with mcp_client.session("playwright") as session:
            tools = await load_mcp_tools(session)
            log_lines.append(f"✅ 成功加载了 {len(tools)} 个浏览器操作工具！")

            llm = ChatOpenAI(
                model="glm-4-flash",
                api_key=os.environ.get("ZHIPUAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                temperature=0
            )

            agent = create_react_agent(llm, tools)
            log_lines.append("🤖 AI 开始执行测试任务...")
            response = await agent.ainvoke({"messages": prompt})
            result_text = response["messages"][-1].content

            base64_img_list = []
            # 从MCP返回消息提取image_url格式的base64截图
            for msg in response["messages"]:
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "image_url":
                            img_data = part["image_url"]["url"]
                            if img_data.startswith("data:image/png;base64,"):
                                b64 = img_data.split(",")[1]
                                base64_img_list.append(b64)

            log_text = "\n".join(log_lines)
            return result_text, base64_img_list, log_text

    except Exception as e:
        log_lines.append(f"❌ 执行异常：{str(e)}")
        log_text = "\n".join(log_lines)
        return "执行失败", [], log_text


def run_test(prompt: str):
    return asyncio.run(run_test_task(prompt))


if __name__ == "__main__":
    res, img_b64_list, log = run_test("""
使用Playwright完成下面测试任务：
1. 访问 https://www.saucedemo.com/
2. 在用户名输入框填入 standard_user
3. 在密码输入框填入 secret_sauce
4. 点击登录按钮完成登录
5. 执行页面截图，不要保存为本地文件，直接返回base64图片数据
6. 判断登录是否成功，输出测试结论。
""")
    print(log)
    print("\n===测试结果===")
    print(res)
    print(f"\n捕获base64截图数量：{len(img_b64_list)}")