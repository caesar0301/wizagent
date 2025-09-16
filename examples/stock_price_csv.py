import asyncio
import os
import sys

from cogents_tools.integrations.bu import Agent, BrowserProfile, ProxySettings
from cogents_tools.integrations.llm import get_llm_client_bu_compatible
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    import time

    start_time = time.time()

    task = """
    Find historical stock price of companies Alibaba and Google for the last 3 months. Then, make me a CSV file with 2 columns: company name, stock price. 
    """

    browser_profile = BrowserProfile(
        headless=True, proxy=ProxySettings(server="http://127.0.0.1:7890", bypass="localhost,127.0.0.1,*.internal,*.cn")
    )

    agent = Agent(
        task=task,
        llm=get_llm_client_bu_compatible(),
        max_steps=50,
        browser_profile=browser_profile,
    )
    await agent.run()
    print(agent.file_system_path)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
