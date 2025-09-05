import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from cogents_core.llm import get_llm_client_instructor

from cogents_wiz.bu import Agent
from cogents_wiz.llm_adapter import BULLMAdapter
from cogents_wiz.prompt.prompt import PromptManager

llm = BULLMAdapter(get_llm_client_instructor(provider="openrouter", chat_model="google/gemini-2.5-flash"))

template_dir = os.path.join(Path(__file__).parent.parent, "cogents_wiz", "prompt_template")
manager = PromptManager(template_dirs=[str(template_dir)])
use_cheatsheet = True


async def main():
    import time

    start_time = time.time()
    messages = manager.render_prompt(
        "stock_price_query.md",
        stock_symbol="Amazon",
        task_type="historical_data",
        time_period="3 months",
    )
    messages += manager.render_prompt("agent_episodic_memory.md")

    extended_system_message = ""
    for message in messages:
        if message.role == "system":
            extended_system_message += message.content

    print(extended_system_message)

    task = """
    Find historical stock price of companies Amazon for the last 3 months. Then, make me a CSV file with 2 columns: company name, stock price. 
    """

    if use_cheatsheet:
        with open(os.path.join("wizbook", "wizpage-stock-data.md"), "r", encoding="utf-8") as f:
            task += "\n" + f.read()

    print(task)

    agent = Agent(
        task=task,
        llm=llm,
        extend_system_message=extended_system_message,
        max_steps=50,
    )
    history = await agent.run()

    # token usage
    print(agent.file_system_path)
    print(history.usage)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
