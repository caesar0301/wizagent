import logging
from typing import Any, Dict, List, Optional, Union

from cogents_tools.integrations.utils.llm_adapter import BaseLLMClient, BULLMAdapter, get_llm_client
from pydantic import BaseModel

from .base import BaseWebPage, BaseWebSurfer, ObserveResult

try:
    from cogents_tools.integrations.bu import Agent, BrowserSession, Tools
    from wizagent.buagent.views import AgentSettings
except ImportError as e:
    raise ImportError(f"Failed to import browser-use components: {e}")

logger = logging.getLogger(__name__)


class WebSurferPage(BaseWebPage):
    """Web page implementation using browser-use."""

    def __init__(self, browser_session: BrowserSession):
        self.browser_session = browser_session
        self.llm_client: BaseLLMClient = get_llm_client()
        self.tools = Tools()

    async def navigate(self, url: str, **kwargs) -> None:
        """Navigates to the specified URL."""
        try:
            # Navigate using browser session event system
            from wizagent.bubrowser.events import NavigateToUrlEvent

            event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=url))
            await event
            await event.event_result(raise_if_any=True, raise_if_none=False)

            logger.info(f"Successfully navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    async def act(self, instruction: str, observe_results: Optional[ObserveResult] = None, **kwargs) -> Any:
        """
        Executes an action on the page using natural language.
        Uses browser-use Agent for autonomous action execution.
        """
        try:
            if not self.llm_client:
                raise ValueError("LLM client is required for action execution")

            # Create a browser-use compatible LLM adapter
            llm_adapter = BULLMAdapter(self.llm_client)

            # Create agent for this specific action
            agent = Agent(
                task=instruction,
                llm=llm_adapter,
                browser=self.browser_session,
                settings=AgentSettings(use_vision=True, max_failures=2, max_actions_per_step=3),
            )

            # Execute the action
            history = await agent.run()

            # Return the final result
            final_result = history.final_result() if history else None
            logger.info(f"Action '{instruction}' completed with result: {final_result}")

            return final_result

        except Exception as e:
            logger.error(f"Failed to execute action '{instruction}': {e}")
            raise

    async def extract(
        self, instruction: str, schema: Union[Dict, BaseModel], selector: Optional[str] = None, **kwargs
    ) -> Union[Dict, BaseModel]:
        """
        Extracts structured data from the page based on a Pydantic-like schema.
        """
        try:
            if not self.llm_client:
                raise ValueError("LLM client is required for data extraction")

            # Create a browser-use compatible LLM adapter
            llm_adapter = BULLMAdapter(self.llm_client)

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
                llm=llm_adapter,
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

    async def observe(self, instruction: str, with_actions: bool = True, **kwargs) -> List[ObserveResult]:
        """
        Discovers available actions or elements on the page based on a natural language query.
        """
        try:
            if not self.llm_client:
                raise ValueError("LLM client is required for page observation")

            # Create a browser-use compatible LLM adapter
            llm_adapter = BULLMAdapter(self.llm_client)

            # Create observation task
            observe_task = f"Analyze the current page and identify elements that match: {instruction}"
            if with_actions:
                observe_task += " Provide recommended actions for each identified element."

            # Create agent for observation
            agent = Agent(
                task=observe_task,
                llm=llm_adapter,
                browser=self.browser_session,
                settings=AgentSettings(
                    use_vision=True, max_failures=1, max_actions_per_step=1  # Just observe, don't act
                ),
            )

            # Execute observation
            history = await agent.run()
            result = history.final_result() if history else None

            # Parse result into ObserveResult format
            observe_results = []
            if result:
                # This is a simplified parsing - in a real implementation,
                # you might want to use browser-use's DOM inspection capabilities
                observe_results.append(
                    ObserveResult(
                        selector="xpath=//body",  # Placeholder selector
                        description=str(result),
                        backendNodeId=0,  # Placeholder
                        method="click" if with_actions else "observe",
                        arguments=[] if not with_actions else [""],
                    )
                )

            logger.info(f"Observation completed, found {len(observe_results)} elements")
            return observe_results

        except Exception as e:
            logger.error(f"Failed to observe page with instruction '{instruction}': {e}")
            raise


class WebSurfer(BaseWebSurfer):
    """Web surfer implementation using browser-use."""

    def __init__(self):
        self.llm_client: BaseLLMClient = get_llm_client()
        self.browser_session = None
        self._browser = None

    async def launch(self, headless: bool = True, browser_type: str = "chromium", **kwargs) -> BaseWebPage:
        """
        Launches a new browser instance and returns a BaseWebPage.
        """
        try:
            # Create browser instance with configuration
            self._browser = BrowserSession(headless=headless, **kwargs)

            # Launch browser
            await self._browser.start()

            self.browser_session = self._browser

            # Create and return WebSurferPage
            page = WebSurferPage(self.browser_session, self.llm_client)

            logger.info(f"Browser launched successfully (headless={headless}, type={browser_type})")
            return page

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def close(self):
        """Closes the browser instance."""
        try:
            if self.browser_session:
                await self.browser_session.stop()
                self.browser_session = None
                self._browser = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")
            raise

    async def agent(self, prompt: str, **kwargs) -> "Agent":
        """
        Creates an autonomous agent that can execute complex web workflows.
        Returns the browser-use Agent directly for full functionality access.
        """
        try:
            if not self.llm_client:
                raise ValueError("LLM client is required for autonomous agent")

            if not self.browser_session:
                # Auto-launch browser if not already launched
                await self.launch(headless=kwargs.get("headless", True))

            # Create browser-use compatible LLM adapter
            llm_adapter = BULLMAdapter(self.llm_client)

            # Create browser-use agent
            browser_use_agent = Agent(
                task=prompt,
                llm=llm_adapter,
                browser=self.browser_session,
                settings=AgentSettings(
                    use_vision=kwargs.get("use_vision", True),
                    max_failures=kwargs.get("max_failures", 3),
                    max_actions_per_step=kwargs.get("max_actions_per_step", 4),
                ),
            )

            logger.info(f"Autonomous browser-use agent created for task: {prompt}")

            # Return the browser-use agent directly
            return browser_use_agent

        except Exception as e:
            logger.error(f"Failed to create agent for prompt '{prompt}': {e}")
            raise
