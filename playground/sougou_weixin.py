import asyncio

from dotenv import load_dotenv

from wizagent.bu.browser.profile import BrowserProfile

load_dotenv()


from wizagent.bu import Agent


async def main():
    import time

    start_time = time.time()

    query = "甲骨文核心业务"

    task = f"""
    1. 打开https://weixin.sogou.com/
    2. 在搜索框输入：{query}，并点击搜文章
    2. 根据返回的文章列表，获取前两页的搜索结果，并返回每个搜索结果的标题、概要、发布机构、发布时间、文章链接
    5. 以Markdown格式返回
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
