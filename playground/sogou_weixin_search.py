import asyncio

from dotenv import load_dotenv

from cogents_bu import Agent, BrowserProfile

load_dotenv()


async def main():
    import time

    start_time = time.time()

    query = "甲骨文 星际计划"

    task = f"""
    1. access https://weixin.sogou.com/weixin?ie=utf8&s_from=input&_sug_=y&_sug_type_=&type=2&query={query}
    2. extract search result items and extract original weixin (WeChat) link from the redirect link. 

    Example:
    Original link: https://weixin.sogou.com/link?url=dn9a_-gY295K0Rci_xozVXfdMkSQTLW6cwJThYulHEtVjXrGTiVgS7ROGf8sroaACUzps5rcR2xNdJQTgPRzn1qXa8Fplpd9CRmQ1bnXd1hU2D8lghzZ3uXrp4MA19-kKc-TDAzLBd0RVC9bG1QOXLb_RveaA41jRsNOpBTWTUXnyhwAnHlJoKEscDNqZRK8xhwfeAvTY2_DAUviqC0BwoV1cw6TNSguv9ECkoY5si5nwFqJn3WbVKNUBEJ3Nvb-NANWRCa0gws5eBgmN3LoYQ..&type=2&query=%E7%94%B2%E9%AA%A8%E6%96%87&token=9E4589BA912658310B0D35DBAF5B64A30B1F4F8D68C7AA3F&k=82&h=X

    Extracted link: https://mp.weixin.qq.com/s?src=11&timestamp=1757915711&ver=6237&signature=rLp*uMBMi*KZgbGjqIcW*LXG29ScdFo9dKVQgwn2UQFg-k*F4JzuwKjUuDYYTpsFEFi1wbFJLZpjxLLug*TnGa0ous45yD04WxJa1SGFnwkpmMIs*ItmNtOUYOIugPlX&new=1
    """

    browser_profile = BrowserProfile(headless=False)

    agent = Agent(
        task=task,
        max_steps=50,
        browser_profile=browser_profile,
    )
    await agent.run()
    print(agent.file_system_path)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
