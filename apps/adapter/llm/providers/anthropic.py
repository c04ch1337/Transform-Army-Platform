"""Anthropic LLM provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from anthropic import AsyncAnthropic

from .base import (
    BaseLLMProvider,
    ProviderConfig,
    ProviderType,
    Message,
    CompletionResponse,
    StreamChunk,
)
from ...core.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation.
    
    Supports:
    - Claude 3 models (Opus, Sonnet, Haiku)
    - Tool use (function calling)
    - Streaming responses
    - Vision capabilities
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
    
    @property
    def provider_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.ANTHROPIC
    
    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        try:
            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
            
            logger.info(
                f"Initialized Anthropic provider with model: {self.config.model}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}", exc_info=e)
            raise
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """Send chat completion request to Anthropic."""
        if not self._client:
            await self.initialize()
        
        # Extract system message (Anthropic requires separate system parameter)
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append(self._message_to_anthropic(msg))
        
        # Build request parameters
        params = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self.config.max_tokens or 4096,
            "temperature": temperature or self.config.temperature,
            "top_p": self.config.top_p,
            **kwargs
        }
        
        if system_message:
            params["system"] = system_message
        
        if tools:
            # Convert tools to Anthropic format
            anthropic_tools = [self.format_tool_call(tool) for tool in tools]
            params["tools"] = anthropic_tools
        
        try:
            response = await self._client.messages.create(**params)
            
            # Extract content
            content = ""
            tool_calls_data = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls_data.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input),
                        }
                    })
            
            return CompletionResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                tool_calls=tool_calls_data if tool_calls_data else None,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            logger.error(f"Anthropic chat completion failed: {e}", exc_info=e)
            raise
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from Anthropic."""
        if not self._client:
            await self.initialize()
        
        # Extract system message
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append(self._message_to_anthropic(msg))
        
        # Build parameters
        params = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self.config.max_tokens or 4096,
            "temperature": temperature or self.config.temperature,
            "top_p": self.config.top_p,
            "stream": True,
            **kwargs
        }
        
        if system_message:
            params["system"] = system_message
        
        if tools:
            anthropic_tools = [self.format_tool_call(tool) for tool in tools]
            params["tools"] = anthropic_tools
        
        try:
            async with self._client.messages.stream(**params) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)
                        elif hasattr(event.delta, "partial_json"):
                            # Tool use in progress
                            pass
                    
                    elif event.type == "content_block_stop":
                        # Content block completed
                        pass
                    
                    elif event.type == "message_delta":
                        if event.delta.stop_reason:
                            yield StreamChunk(
                                content="",
                                finish_reason=event.delta.stop_reason
                            )
                    
                    elif event.type == "message_stop":
                        # Message completed
                        pass
                
        except Exception as e:
            logger.error(f"Anthropic stream failed: {e}", exc_info=e)
            raise
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings.
        
        Note: Anthropic doesn't provide embeddings directly.
        This method raises NotImplementedError.
        """
        raise NotImplementedError(
            "Anthropic does not provide embedding models. "
            "Use OpenAI or another provider for embeddings."
        )
    
    def count_tokens(self, messages: List[Message]) -> int:
        """Estimate token count for Anthropic.
        
        Anthropic uses a different tokenizer. This provides a rough estimate
        based on character count (~4 chars per token).
        """
        total_chars = 0
        
        for message in messages:
            if message.content:
                total_chars += len(message.content)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_str = json.dumps(tool_call)
                    total_chars += len(tool_str)
        
        # Rough estimate: ~4 characters per token
        estimated_tokens = total_chars // 4
        
        return estimated_tokens
    
    def format_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call for Anthropic.
        
        Anthropic expects:
        {
            "name": "function_name",
            "description": "...",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        # Extract function definition
        if "function" in tool_call:
            function = tool_call["function"]
        else:
            function = tool_call
        
        return {
            "name": function.get("name", ""),
            "description": function.get("description", ""),
            "input_schema": function.get("parameters", {
                "type": "object",
                "properties": {},
            }),
        }
    
    def parse_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Anthropic tool use to generic format."""
        # Anthropic tool use format:
        # {
        #     "id": "toolu_...",
        #     "type": "tool_use",
        #     "name": "function_name",
        #     "input": {...}
        # }
        
        return {
            "id": tool_call.get("id"),
            "name": tool_call.get("name"),
            "arguments": tool_call.get("input", {}),
        }
    
    def _message_to_anthropic(self, message: Message) -> Dict[str, Any]:
        """Convert generic message to Anthropic format."""
        # Anthropic format is simpler than OpenAI
        anthropic_msg = {
            "role": message.role if message.role != "system" else "user",
            "content": message.content or "",
        }
        
        # Handle tool results
        if message.tool_call_id:
            # This is a tool result message
            anthropic_msg["content"] = [
                {
                    "type": "tool_result",
                    "tool_use_id": message.tool_call_id,
                    "content": message.content or "",
                }
            ]
        
        # Handle tool calls in assistant messages
        elif message.tool_calls:
            content_blocks = []
            
            # Add text content if present
            if message.content:
                content_blocks.append({
                    "type": "text",
                    "text": message.content
                })
            
            # Add tool use blocks
            for tool_call in message.tool_calls:
                parsed = self.parse_tool_call(tool_call)
                content_blocks.append({
                    "type": "tool_use",
                    "id": parsed["id"],
                    "name": parsed["name"],
                    "input": parsed["arguments"],
                })
            
            anthropic_msg["content"] = content_blocks
        
        return anthropic_msg
    
    async def close(self) -> None:
        """Close Anthropic client."""
        if self._client:
            await self._client.close()
            logger.debug("Closed Anthropic client")