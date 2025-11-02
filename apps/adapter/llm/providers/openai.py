"""OpenAI LLM provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI
import tiktoken

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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation.
    
    Supports:
    - GPT-4, GPT-4-turbo, GPT-3.5-turbo models
    - Function calling
    - Streaming responses
    - Embeddings (text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large)
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self._tokenizer: Optional[tiktoken.Encoding] = None
    
    @property
    def provider_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.OPENAI
    
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                organization=self.config.organization,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
            
            # Initialize tokenizer
            try:
                self._tokenizer = tiktoken.encoding_for_model(self.config.model)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            
            logger.info(
                f"Initialized OpenAI provider with model: {self.config.model}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}", exc_info=e)
            raise
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """Send chat completion request to OpenAI."""
        if not self._client:
            await self.initialize()
        
        # Convert messages to OpenAI format
        openai_messages = [
            self._message_to_openai(msg) for msg in messages
        ]
        
        # Build request parameters
        params = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            **kwargs
        }
        
        if max_tokens or self.config.max_tokens:
            params["max_tokens"] = max_tokens or self.config.max_tokens
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        try:
            response = await self._client.chat.completions.create(**params)
            
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Extract tool calls if present
            tool_calls_data = None
            if choice.message.tool_calls:
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            
            return CompletionResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls_data,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}", exc_info=e)
            raise
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from OpenAI."""
        if not self._client:
            await self.initialize()
        
        # Convert messages
        openai_messages = [
            self._message_to_openai(msg) for msg in messages
        ]
        
        # Build parameters
        params = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": True,
            **kwargs
        }
        
        if max_tokens or self.config.max_tokens:
            params["max_tokens"] = max_tokens or self.config.max_tokens
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        try:
            stream = await self._client.chat.completions.create(**params)
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                content = delta.content or ""
                finish_reason = choice.finish_reason
                
                # Extract tool calls if present
                tool_calls_data = None
                if delta.tool_calls:
                    tool_calls_data = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name if tc.function else None,
                                "arguments": tc.function.arguments if tc.function else None,
                            }
                        }
                        for tc in delta.tool_calls
                        if tc.function
                    ]
                
                yield StreamChunk(
                    content=content,
                    finish_reason=finish_reason,
                    tool_calls=tool_calls_data
                )
                
        except Exception as e:
            logger.error(f"OpenAI stream failed: {e}", exc_info=e)
            raise
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        if not self._client:
            await self.initialize()
        
        embedding_model = model or "text-embedding-3-small"
        
        try:
            response = await self._client.embeddings.create(
                model=embedding_model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(
                f"Generated {len(embeddings)} embeddings with model {embedding_model}"
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embeddings failed: {e}", exc_info=e)
            raise
    
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens using tiktoken."""
        if not self._tokenizer:
            try:
                self._tokenizer = tiktoken.encoding_for_model(self.config.model)
            except KeyError:
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
        
        total_tokens = 0
        
        for message in messages:
            # Count tokens in role
            total_tokens += len(self._tokenizer.encode(message.role))
            
            # Count tokens in content
            if message.content:
                total_tokens += len(self._tokenizer.encode(message.content))
            
            # Count tokens in tool calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_str = json.dumps(tool_call)
                    total_tokens += len(self._tokenizer.encode(tool_str))
            
            # Add overhead for message formatting (approximate)
            total_tokens += 4
        
        # Add overhead for response priming
        total_tokens += 3
        
        return total_tokens
    
    def format_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call for OpenAI.
        
        OpenAI expects:
        {
            "type": "function",
            "function": {
                "name": "function_name",
                "description": "...",
                "parameters": {...}
            }
        }
        """
        return {
            "type": "function",
            "function": {
                "name": tool_call.get("name"),
                "description": tool_call.get("description", ""),
                "parameters": tool_call.get("parameters", {}),
            }
        }
    
    def parse_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAI tool call to generic format."""
        function = tool_call.get("function", {})
        
        # Parse arguments if they're a string
        arguments = function.get("arguments", "{}")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool arguments: {arguments}")
                arguments = {}
        
        return {
            "id": tool_call.get("id"),
            "name": function.get("name"),
            "arguments": arguments,
        }
    
    def _message_to_openai(self, message: Message) -> Dict[str, Any]:
        """Convert generic message to OpenAI format."""
        openai_msg = {
            "role": message.role,
            "content": message.content,
        }
        
        if message.name:
            openai_msg["name"] = message.name
        
        if message.tool_calls:
            openai_msg["tool_calls"] = message.tool_calls
        
        if message.tool_call_id:
            openai_msg["tool_call_id"] = message.tool_call_id
        
        return openai_msg
    
    async def close(self) -> None:
        """Close OpenAI client."""
        if self._client:
            await self._client.close()
            logger.debug("Closed OpenAI client")