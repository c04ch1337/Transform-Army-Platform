"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    
    provider_type: ProviderType
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    max_retries: int = 3
    base_url: Optional[str] = None
    organization: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "provider_type": self.provider_type.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "base_url": self.base_url,
            "organization": self.organization,
        }


@dataclass
class Message:
    """Chat message."""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class CompletionResponse:
    """Response from LLM completion."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class StreamChunk:
    """Chunk from streaming response."""
    content: str
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers.
    
    All provider implementations must inherit from this class and implement
    the abstract methods for chat completion, streaming, and embeddings.
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._client = None
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get provider type."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client.
        
        This method should create and configure the underlying client
        (e.g., OpenAI client, Anthropic client) with the provided config.
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """Send a chat completion request.
        
        Args:
            messages: List of chat messages
            tools: Optional tool definitions for function calling
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Completion response with content and metadata
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response.
        
        Args:
            messages: List of chat messages
            tools: Optional tool definitions for function calling
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Stream chunks with partial content
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            model: Optional embedding model override
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages.
        
        Args:
            messages: List of messages to count
            
        Returns:
            Total token count
        """
        pass
    
    @abstractmethod
    def format_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call to provider-specific format.
        
        Args:
            tool_call: Generic tool call definition
            
        Returns:
            Provider-specific tool call format
        """
        pass
    
    @abstractmethod
    def parse_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Parse provider-specific tool call to generic format.
        
        Args:
            tool_call: Provider-specific tool call
            
        Returns:
            Generic tool call format
        """
        pass
    
    async def close(self) -> None:
        """Close client connections.
        
        Override this method if the provider client needs cleanup.
        """
        pass
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.config.model})"