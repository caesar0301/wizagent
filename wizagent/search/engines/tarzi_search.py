import asyncio

import tarzi
from cogents_core.utils import get_logger
from pydantic import BaseModel, Field

from ..base import BaseSearch, SearchResult, SourceItem

logger = get_logger(__name__)


class TarziSearchError(Exception):
    """Custom exception for Tarzi Search errors."""


class TarziSearchConfig(BaseModel):
    search_engine: str = Field(default="brave", description="Search engine to use")
    max_results: int = Field(default=10, description="Maximum number of results to return")
    timeout: int = Field(default=15, description="Timeout in seconds")
    web_driver: str = Field(default="chromedriver", description="Web driver to use")
    headless: bool = Field(default=True, description="If enable headless browser")
    output_format: str = Field(default="markdown", description="Output format (html|markdown|json|yaml)")


class TarziSearch(BaseSearch):
    def __init__(self, config: TarziSearchConfig):
        self.tarzi_config = config
        fetch_mode = "browser_headless" if config.headless else "browser_head"
        _config_str = f"""
[fetcher]
timeout = {config.timeout}
format = "{config.output_format}"
web_driver = "{config.web_driver}"
mode = "{fetch_mode}"
[search]
engine = "{config.search_engine}"
limit = {config.max_results}
"""
        self._config = tarzi.Config.from_str(_config_str)
        self._engine = tarzi.SearchEngine.from_config(self._config)

    def search(self, query: str) -> SearchResult:
        """Perform a synchronous search query."""
        try:
            results = self._engine.search(query, self.tarzi_config.max_results)
            return self._convert_to_search_result(results, query)
        except Exception as e:
            logger.error(f"Tarzi search failed for query '{query}': {e}")
            raise TarziSearchError(f"Search failed: {e}")

    async def async_search(self, query: str) -> SearchResult:
        """Perform an asynchronous search query."""
        try:
            # Run the synchronous search in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._engine.search, query, self.tarzi_config.max_results)
            return self._convert_to_search_result(results, query)
        except Exception as e:
            logger.error(f"Tarzi async search failed for query '{query}': {e}")
            raise TarziSearchError(f"Async search failed: {e}")

    def _convert_to_search_result(self, results: tarzi.SearchResult, query: str) -> SearchResult:
        """Convert tarzi SearchResult to our SearchResult format."""
        try:
            sources = []

            # Convert each result to SourceItem
            for result in results:
                source_item = SourceItem(
                    url=result.url,
                    title=result.title,
                    content=result.snippet,  # Use snippet as content
                    score=result.rank,
                    raw_content=None,
                )
                sources.append(source_item)

            # Create SearchResult
            search_result = SearchResult(
                query=query,
                answer=None,  # Tarzi doesn't provide AI-generated answers
                images=[],  # Tarzi doesn't provide images
                sources=sources,
                response_time=None,  # Tarzi doesn't provide response time
                raw_response=results,  # Store original results
                follow_up_questions=None,  # Tarzi doesn't provide follow-up questions
            )

            return search_result

        except Exception as e:
            logger.error(f"Failed to convert tarzi results: {e}")
            raise TarziSearchError(f"Result conversion failed: {e}")

    def cleanup(self):
        """Clean up resources and shutdown the search engine."""
        try:
            if hasattr(self, "_engine") and self._engine:
                self._engine.shutdown()
        except Exception as e:
            logger.warning(f"Error during engine cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        self.cleanup()
