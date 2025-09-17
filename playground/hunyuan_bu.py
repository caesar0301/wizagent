import asyncio

from dotenv import load_dotenv

from wizagent.bu.browser.profile import BrowserProfile

load_dotenv()


from wizagent.bu import Agent


async def main():
    import time

    start_time = time.time()

    query = "美团未来两个月的股市预测"

    task = f"""
    利用腾讯元宝AI助手获取信息：

    1. 打开https://yuanbao.tencent.com/，在新的会话里输入：{query}
    2. 开启选项【深度思考】和【联网搜索】
    3. 等待AI助手回答
    4. 获取助手回答的结果，以及联网搜索的引用连接
    5. 以Markdown格式返回

    ## 检索结果

    [助手回答]

    ## 引用链接

    1. title, URL
    2. title, URL
    """

    # proxy = ProxySettings(server="http://127.0.0.1:7890", bypass="localhost,127.0.0.1,*.internal,*.cn")
    browser_profile = BrowserProfile(headless=False, enable_default_extensions=False)

    agent = Agent(
        task=task,
        max_steps=50,
        browser_profile=browser_profile,
    )
    await agent.run()

    # token usage
    print(agent.file_system_path)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
