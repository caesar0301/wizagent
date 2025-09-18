from typing import Any, Dict, List, Optional, Union

from cogents_core.llm import BaseLLMClient
from cogents_core.utils import get_logger
from pydantic import BaseModel

from wizagent.bu import Agent, BrowserSession
from wizagent.bu.agent.views import AgentSettings
from wizagent.bu.llm_adapter import BaseChatModel
from wizagent.search import SearchResult

logger = get_logger(__name__)


class WizAgent:
    def __init__(self, llm: BaseLLMClient, **kwargs):
        self.llm = llm

    async def search(
        self,
        query: Union[str, List[str]],
        max_results: int = 20,
        crawl_conent: bool = True,
        conent_format: str = "markdown",
        query_rewrite: bool = False,
        adaptive_crawl: bool = False,
        crawl_depth: int = 1,
        search_goal: str = "",
        **kwargs,
    ) -> SearchResult:
        """
        Search the query using the WizSearch.

        Args:
            query: The query to search for.
            query_rewrite: Whether to rewrite the query by LLM.
            max_results: The maximum number of results to return.
            search_goal: The goal of the search to be evaluated by LLM (leave empty to disable LLM evaluation).
            crawl_conent: Whether to crawl the page content of SERP links.
            conent_format: The format of the content to return.
            adaptive_crawl: Whether to use adaptive crawling of Crawl4AI (with embedding similarity).
            crawl_depth: The depth of the crawl (leave 1 to disable deep crawling).
            **kwargs: Additional arguments.

        Returns:
            SearchResult: The search result.
        """

    async def crawl_page(
        self,
        url: str,
        external_links: bool = False,
        adaptive_crawl: bool = False,
        depth: int = 3,
        **kwargs,
    ) -> str:
        """
        Crawl a single page using the Crawl4AI library.

        Args:
            url: The url to crawl.
            external_links: Whether to crawl external links.
            adaptive_crawl: Whether to use adaptive crawling.
            depth: The depth of the crawl.
            **kwargs: Additional arguments.

        Returns:
            str: The crawled content.
        """

    async def extract(
        self,
        url: str,
        instruction: str,
        schema: Union[Dict, BaseModel],
        selector: Optional[str] = None,
        **kwargs,
    ) -> Union[Dict, BaseModel]:
        """
        Extracts structured data from the page based on a Pydantic-like schema.
        """
        try:
            if not self.llm:
                raise ValueError("LLM client is required for data extraction")

            # Prepare task instruction
            task_instruction = f"Extract data from the current page: {instruction}"
            if selector:
                task_instruction += f" Focus on elements matching selector: {selector}"

            # Determine output model
            output_model = None
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                output_model = schema
            elif isinstance(schema, dict):
                # Convert dict schema to Pydantic model if needed
                # For now, we'll extract as text and structure it
                pass

            # Create agent for extraction
            agent = Agent(
                task=task_instruction,
                llm=BaseChatModel(self.llm),
                browser=self.browser_session,
                output_model_schema=output_model,
                settings=AgentSettings(use_vision=True, max_failures=2),
            )

            # Execute extraction
            history = await agent.run()
            result = history.final_result() if history else None

            if output_model and result:
                try:
                    # Try to parse as structured output
                    if isinstance(result, str):
                        return output_model.model_validate_json(result)
                    elif isinstance(result, dict):
                        return output_model.model_validate(result)
                    else:
                        return result
                except Exception as parse_error:
                    logger.warning(f"Failed to parse structured output: {parse_error}")
                    # Fall back to text extraction
                    return {"page_text": str(result)}

            # Return as dict or original schema format
            if isinstance(schema, dict):
                return {"page_text": str(result)} if result else {}
            elif isinstance(result, str):
                return {"page_text": result}
            else:
                return result or {}

        except Exception as e:
            logger.error(f"Failed to extract data with instruction '{instruction}': {e}")
            raise

    async def _launch_browser_session(self, headless: bool = True, **kwargs) -> BrowserSession:
        """
        Launches a new browser instance.
        """
        try:
            _browser = BrowserSession(headless=headless, **kwargs)
            await _browser.start()
            return _browser
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def _close_browser_session(self, session: BrowserSession):
        """Closes the browser instance."""
        try:
            if session:
                await session.stop()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")
            raise

    async def use_browse(
        self,
        instruction: str,
        headless: bool = True,
        use_vision: bool = False,
        max_failures: int = 3,
        max_actions_per_step: int = 3,
        **kwargs,
    ) -> Any:
        try:
            if not self.llm:
                raise ValueError("LLM client is required for autonomous agent")

            session = await self._launch_browser_session(headless)

            # Create browser-use agent
            browser_use_agent = Agent(
                task=instruction,
                llm=BaseChatModel(self.llm),
                browser=session,
                settings=AgentSettings(
                    use_vision=use_vision,
                    max_failures=max_failures,
                    max_actions_per_step=max_actions_per_step,
                ),
            )
            logger.info(f"Autonomous browser-use agent created for task: {instruction}")
            result = await browser_use_agent.run()
            logger.info(f"✅ Autonomous agent completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create agent for instruction '{instruction}': {e}")
            raise
        finally:
            await self._close_browser_session(session)
