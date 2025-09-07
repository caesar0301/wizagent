import asyncio
import os
import sys
from pathlib import Path

from wizagent.bu.browser.profile import BrowserProfile, ProxySettings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


from cogents_core.llm.prompt import PromptManager

from wizagent.bu import Agent
from wizagent.llm_adapter import BULLMAdapter

template_dir = os.path.join(Path(__file__).parent.parent, "wizagent", "prompt_template")
manager = PromptManager(template_dirs=[str(template_dir)])
use_cheatsheet = True


async def main():
    import time

    start_time = time.time()
    messages = manager.render_prompt("agent_episodic_memory.md")

    extended_system_message = ""
    for message in messages:
        if message.role == "system":
            extended_system_message += message.content

    task = """
    Find historical stock price of companies Alibaba and Google for the last 3 months. Then, make me a CSV file with 2 columns: company name, stock price. 
    """

    if use_cheatsheet:
        with open(os.path.join("wiz-memory-store", "wizpage-stock-data.md"), "r", encoding="utf-8") as f:
            task += "\n" + f.read()

    print(task)

    browser_profile = BrowserProfile(
        headless=True, proxy=ProxySettings(server="http://127.0.0.1:7890", bypass="localhost,127.0.0.1,*.internal,*.cn")
    )

    agent = Agent(
        task=task,
        llm=BULLMAdapter(),
        extend_system_message=extended_system_message,
        max_steps=50,
        browser_profile=browser_profile,
    )
    history = await agent.run()

    # token usage
    print(agent.file_system_path)
    print(history.usage)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
