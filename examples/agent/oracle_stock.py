import asyncio
import logging

from wizagent.wizagent import WizAgent

logger = logging.getLogger(__name__)


async def demo_oracle_stock_wechat():
    wiz_agent = WizAgent()
    try:
        result = await wiz_agent.research(
            instruction="甲骨文星际之门项目最新进展",
            search_engines=["wechat"],
            max_results_per_engine=5,
            search_timeout=30,
        )
        logger.info(f"✅ Oracle stock wechat completed: {result}")
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"❌ Oracle stock wechat demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(demo_oracle_stock_wechat())
