import asyncio
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from cogents_core.llm import BaseLLMClient

from cogents_wiz.bu.llm.views import ChatInvokeCompletion


class BULLMAdapter:
    """Adapter to make cogents LLM clients compatible with browser-use."""

    def __init__(self, cogents_client: BaseLLMClient):
        self.cogents_client = cogents_client
        self.model = getattr(cogents_client, "model", "unknown")
        self._verified_api_keys = True  # Assume the cogents client is properly configured

    @property
    def provider(self) -> str:
        """Return the provider name."""
        return getattr(self.cogents_client, "provider", "cogents")

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
                    if hasattr(self.cogents_client, "structured_completion"):
                        if asyncio.iscoroutinefunction(self.cogents_client.structured_completion):
                            structured_response = await self.cogents_client.structured_completion(
                                cogents_messages, output_format
                            )
                        else:
                            structured_response = self.cogents_client.structured_completion(
                                cogents_messages, output_format
                            )
                        return ChatInvokeCompletion(completion=structured_response, usage=None)
                    else:
                        # Fall back to regular completion + JSON parsing if structured_completion not available
                        if asyncio.iscoroutinefunction(self.cogents_client.completion):
                            response = await self.cogents_client.completion(cogents_messages)
                        else:
                            response = self.cogents_client.completion(cogents_messages)

                        # Try to parse as JSON and create structured object
                        import json

                        response_str = str(response)
                        try:
                            parsed_data = json.loads(response_str)
                            if isinstance(parsed_data, dict):
                                parsed_object = output_format(**parsed_data)
                                return ChatInvokeCompletion(completion=parsed_object, usage=None)
                            else:
                                raise ValueError("Parsed JSON is not a dictionary")
                        except (json.JSONDecodeError, ValueError, TypeError) as parse_error:
                            logger.error(
                                f"Failed to parse response as JSON for {output_format.__name__}: {parse_error}"
                            )
                            logger.error(f"Response content: {response_str}")
                            # Create minimal fallback structured object
                            if hasattr(output_format, "model_fields") and "action" in output_format.model_fields:
                                fallback_data = {
                                    "thinking": f"Parse error: {str(parse_error)}",
                                    "evaluation_previous_goal": "Unable to parse structured response",
                                    "memory": response_str[:500],  # Truncate for safety
                                    "next_goal": "Retry with simpler approach",
                                    "action": [],
                                }
                                try:
                                    parsed_object = output_format(**fallback_data)
                                    return ChatInvokeCompletion(completion=parsed_object, usage=None)
                                except Exception:
                                    pass
                            raise parse_error

                except Exception as e:
                    logger.error(f"Error in structured completion: {e}")
                    raise
            else:
                # Use regular completion for string output
                if asyncio.iscoroutinefunction(self.cogents_client.completion):
                    response = await self.cogents_client.completion(cogents_messages)
                else:
                    response = self.cogents_client.completion(cogents_messages)

                return ChatInvokeCompletion(completion=str(response), usage=None)

        except Exception as e:
            logger.error(f"Error in LLM adapter: {e}")
            raise
