import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

import dotenv
from cogents_core.llm import BaseLLMClient
from cogents_core.llm import get_llm_client as _get_llm_client

from wizagent.bu.llm.views import ChatInvokeCompletion

dotenv.load_dotenv()


def get_llm_client(instructor=True) -> BaseLLMClient:
    """
    Get an LLM client with optional memory system compatibility

    Args:
        instructor: Whether to enable instructor mode for structured output
        memory_compatible: Whether to wrap client for memory system compatibility

    Returns:
        BaseLLMClient: Configured LLM client
    """
    provider = os.getenv("WIZAGENT_LLM_PROVIDER", "openai")
    base_url = os.getenv("WIZAGENT_LLM_BASE_URL", "")
    api_key = os.getenv("WIZAGENT_LLM_API_KEY", "")

    # Extra client configs from .env
    return _get_llm_client(provider=provider, base_url=base_url, api_key=api_key, instructor=instructor)


def get_llm_client_browser_compatible(instructor=True) -> BaseLLMClient:
    """
    Get an LLM client with optional memory system compatibility

    Args:
        instructor: Whether to enable instructor mode for structured output
        memory_compatible: Whether to wrap client for memory system compatibility

    Returns:
        BaseLLMClient: Configured LLM client
    """
    return BULLMAdapter(get_llm_client(instructor=instructor))


def get_llm_client_memory_compatible(instructor=True) -> BaseLLMClient:
    """
    Get an LLM client with optional memory system compatibility

    Args:
        instructor: Whether to enable instructor mode for structured output
        memory_compatible: Whether to wrap client for memory system compatibility

    Returns:
        BaseLLMClient: Configured LLM client
    """
    return MemoryLLMAdapter(get_llm_client(instructor=instructor))


class BaseLLMAdapter:
    """Base class for LLM adapters providing common interface"""

    def __init__(self, llm_client):
        """Initialize adapter with LLM client"""
        self.llm_client = llm_client

        # Forward common attributes
        for attr_name in ["api_key", "base_url", "chat_model", "embed_model"]:
            if hasattr(llm_client, attr_name):
                setattr(self, attr_name, getattr(llm_client, attr_name))

    def completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Forward completion calls to original client"""
        return self.llm_client.completion(messages, **kwargs)

    def structured_completion(self, messages: List[Dict[str, str]], response_model, **kwargs) -> Any:
        """Forward structured completion calls to original client"""
        return self.llm_client.structured_completion(messages, response_model, **kwargs)

    @property
    def provider(self) -> str:
        """Return provider name if available"""
        return getattr(self.llm_client, "provider", "unknown")

    @property
    def model(self) -> str:
        """Return model name"""
        return getattr(self.llm_client, "chat_model", getattr(self.llm_client, "model", "unknown"))


# Adapt cogents llm client to browser-use.
class BULLMAdapter(BaseLLMAdapter):
    """Adapter to make cogents LLM clients compatible with browser-use."""

    def __init__(self, llm_client=None):
        """
        Initialize Browser-Use LLM Adapter

        Args:
            llm_client: Optional cogents LLM client. If None, creates a default one.
        """
        if llm_client is None:
            llm_client = get_llm_client(instructor=True)

        super().__init__(llm_client)
        self._verified_api_keys = True  # Assume the cogents client is properly configured

    @property
    def name(self) -> str:
        """Return the model name."""
        return self.model

    @property
    def model_name(self) -> str:
        """Return the model name for legacy support."""
        return self.model

    async def ainvoke(self, messages: List[Any], output_format: Optional[type] = None, **kwargs) -> Any:
        """Invoke the LLM with messages."""
        try:
            # Convert browser-use messages to cogents format
            cogents_messages = []
            for msg in messages:
                if hasattr(msg, "role"):
                    # Extract text content properly from browser-use message objects
                    content_text = ""
                    if hasattr(msg, "text"):
                        # Use the convenient .text property that handles both string and list formats
                        content_text = msg.text
                    elif hasattr(msg, "content"):
                        # Fallback: handle content directly
                        if isinstance(msg.content, str):
                            content_text = msg.content
                        elif isinstance(msg.content, list):
                            # Extract text from content parts
                            text_parts = []
                            for part in msg.content:
                                if hasattr(part, "text") and hasattr(part, "type") and part.type == "text":
                                    text_parts.append(part.text)
                            content_text = "\n".join(text_parts)
                        else:
                            content_text = str(msg.content)
                    else:
                        content_text = str(msg)

                    cogents_messages.append({"role": msg.role, "content": content_text})
                elif isinstance(msg, dict):
                    # Already in the right format
                    cogents_messages.append(msg)
                else:
                    # Handle other message formats
                    cogents_messages.append({"role": "user", "content": str(msg)})

            # Choose completion method based on output_format
            if output_format is not None:
                # Use structured completion for structured output
                try:
                    if asyncio.iscoroutinefunction(self.llm_client.structured_completion):
                        structured_response = await self.llm_client.structured_completion(
                            cogents_messages, output_format
                        )
                    else:
                        structured_response = self.llm_client.structured_completion(cogents_messages, output_format)
                    return ChatInvokeCompletion(completion=structured_response, usage=None)
                except Exception as e:
                    logger.error(f"Error in structured completion: {e}")
                    raise
            else:
                # Use regular completion for string output
                if asyncio.iscoroutinefunction(self.llm_client.completion):
                    response = await self.llm_client.completion(cogents_messages)
                else:
                    response = self.llm_client.completion(cogents_messages)

                return ChatInvokeCompletion(completion=str(response), usage=None)

        except Exception as e:
            logger.error(f"Error in LLM adapter: {e}")
            raise


class MemoryLLMAdapter(BaseLLMAdapter):
    """Adapter to make cogents LLM clients compatible with memory agent system"""

    def __init__(self, llm_client):
        """Initialize with the original LLM client"""
        super().__init__(llm_client)

    def simple_chat(self, message: str) -> str:
        """
        Simple chat method that wraps the completion method

        Args:
            message: The message to send to the LLM

        Returns:
            str: The LLM response
        """
        try:
            # Convert single message to messages format
            messages = [{"role": "user", "content": message}]

            # Call the completion method
            response = self.llm_client.completion(messages)

            # Return the response as string
            return str(response)

        except Exception as e:
            logger.error(f"Error in simple_chat: {e}")
            raise

    def chat_completion(self, messages: List[Dict[str, str]], tools=None, tool_choice=None, **kwargs) -> Any:
        """
        Chat completion method for automated memory processing

        Args:
            messages: List of message dictionaries
            tools: Optional tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional arguments

        Returns:
            Mock response object for memory agent compatibility
        """
        try:
            # For now, call the regular completion method
            # In a full implementation, this would handle tool calls properly
            response_text = self.llm_client.completion(messages, **kwargs)

            # Create a mock response object that the memory agent expects
            class MockResponse:
                def __init__(self, content, success=True):
                    self.success = success
                    self.content = content
                    self.tool_calls = []  # No function calling in this simplified version
                    self.error = None if success else "Mock error"

            return MockResponse(str(response_text))

        except Exception as e:
            logger.error(f"Error in chat_completion: {e}")

            class MockResponse:
                def __init__(self, error_msg):
                    self.success = False
                    self.content = ""
                    self.tool_calls = []
                    self.error = error_msg

            return MockResponse(str(e))

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using the underlying LLM client

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector
        """
        return self.llm_client.embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using the underlying LLM client

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        return self.llm_client.embed_batch(texts)

    def get_embedding_dimensions(self) -> int:
        """
        Get the embedding dimensions from the underlying LLM client

        Returns:
            int: Embedding dimensions
        """
        return self.llm_client.get_embedding_dimensions()


def create_memory_compatible_client(llm_client=None):
    """
    Create a memory system compatible LLM client

    Args:
        llm_client: Optional cogents LLM client. If None, creates a default one.

    Returns:
        MemoryLLMAdapter: Adapter with simple_chat and chat_completion methods
    """
    if llm_client is None:
        llm_client = get_llm_client(instructor=False)
    return MemoryLLMAdapter(llm_client)


def create_browser_compatible_client(llm_client=None):
    """
    Create a browser-use compatible LLM client

    Args:
        llm_client: Optional cogents LLM client. If None, creates a default one.

    Returns:
        BULLMAdapter: Adapter for browser-use compatibility
    """
    if llm_client is None:
        llm_client = get_llm_client(instructor=True)
    return BULLMAdapter(llm_client)


def create_adapter(adapter_type="memory", llm_client=None):
    """
    Unified factory function to create different types of LLM adapters

    Args:
        adapter_type: Type of adapter ("memory" or "browser")
        llm_client: Optional cogents LLM client. If None, creates a default one.

    Returns:
        Union[MemoryLLMAdapter, BULLMAdapter]: Configured adapter
    """
    if adapter_type == "memory":
        return create_memory_compatible_client(llm_client)
    elif adapter_type == "browser":
        return create_browser_compatible_client(llm_client)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}. Use 'memory' or 'browser'.")


# Convenience functions for common use cases
def get_memory_client(**kwargs):
    """Get a memory-compatible LLM client with optional parameters"""
    return get_llm_client(memory_compatible=True, **kwargs)


def get_browser_client(**kwargs):
    """Get a browser-compatible LLM client with optional parameters"""
    base_client = get_llm_client(**kwargs)
    return BULLMAdapter(base_client)


__all__ = [
    "get_llm_client",
    "BaseLLMClient",
    "BaseLLMAdapter",
    "BULLMAdapter",
    "MemoryLLMAdapter",
    "create_memory_compatible_client",
    "create_browser_compatible_client",
    "create_adapter",
    "get_memory_client",
    "get_browser_client",
]
