import tarzi
from cogents_core.utils import get_logger
from pydantic import BaseModel, Field

from ..base import BaseSearch

logger = get_logger(__name__)


class TarziSearchError(Exception):
    """Custom exception for Tarzi Search errors."""


class TarziSearchConfig(BaseModel):
    search_engine: str = Field(default="brave", description="Search engine to use")
    max_results: int = Field(default=10, description="Maximum number of results to return")
    timeout: int = Field(default=30, description="Timeout in seconds")
    web_driver: str = Field(default="chromedriver", description="Web driver to use")
    headless: bool = Field(default=True, description="If enable headless browser")


class TarziSearch(BaseSearch):
    def __init__(self, config: TarziSearchConfig):
        self.config = config
        tarzi_config = tarzi.Config()
        tarzi_config.search.engine = config.search_engine
        tarzi_config.search.limit = config.max_results
        tarzi_config.fetcher.web_driver = config.web_driver
        tarzi_config.fetcher.timeout = config.timeout
        if config.headless:
            tarzi_config.fetcher.fetch_mode = "browser_headless"
        else:
            tarzi_config.fetcher.fetch_mode = "browser_head"
        self.tarzi_engine = tarzi.SearchEngine.from_config(tarzi_config)

    def search(self, query: str):
        results = self.tarzi_engine.search(query)
        return results

    async def async_search(self, query: str):
        return await self.tarzi_engine.async_search(query)
