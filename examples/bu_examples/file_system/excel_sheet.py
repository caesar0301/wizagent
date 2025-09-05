import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from wizagent.bu import Agent
from wizagent.bu.llm.google.chat import ChatGoogle

llm = ChatGoogle(model="gemini-2.5-flash")


task = "Find current stock price of companies Meta and Amazon. Then, make me a CSV file with 2 columns: company name, stock price."

agent = Agent(task=task, llm=llm)


async def main():
    import time

    start_time = time.time()
    history = await agent.run()
    # token usage
    print(history.usage)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


if __name__ == "__main__":
    asyncio.run(main())
