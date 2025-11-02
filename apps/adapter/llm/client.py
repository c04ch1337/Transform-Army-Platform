"""Main LLM client for agent orchestration."""

from typing import Any, AsyncIterator, Dict, List, Optional
from dataclasses import dataclass

from .providers.base import (
    BaseLLMProvider,
    ProviderConfig,
    ProviderType,
    Message,
    CompletionResponse,
    StreamChunk,
)
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .token_counter import TokenCounter, UsageStats, get_token_counter
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    
    provider: str = "openai"
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    enable_streaming: bool = True
    enable_cost_tracking: bool = True
    
    @classmethod
    def from_settings(cls) -> "LLMConfig":
        """Create config from application settings."""
        return cls(
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            top_p=settings.llm_top_p,
            enable_streaming=settings.llm_enable_streaming,
            enable_cost_tracking=settings.llm_enable_cost_tracking,
        )


@dataclass
class LLMResponse:
    """Response from LLM."""
    
    content: str
    model: str
    usage: UsageStats
    finish_reason: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    cost_usd: Optional[float] = None


@dataclass
class StreamingChunk:
    """Chunk from streaming response."""
    
    content: str
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class LLMClient:
    """Main LLM client for agent orchestration.
    
    Provides unified interface to multiple LLM providers with:
    - Chat completion
    - Streaming responses
    - Embeddings
    - Token counting and cost tracking
    - Rate limiting
    - Error handling and retries
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client.
        
        Args:
            config: Client configuration (uses settings if not provided)
        """
        self.config = config or LLMConfig.from_settings()
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._token_counter = get_token_counter()
        self._initialized = False
        
        logger.info(
            f"Initialized LLMClient with provider: {self.config.provider}, "
            f"model: {self.config.model}"
        )
    
    async def initialize(self) -> None:
        """Initialize LLM providers."""
        if self._initialized:
            return
        
        # Initialize configured providers
        await self._initialize_provider(self.config.provider)
        
        self._initialized = True
        logger.info("LLM client initialized")
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat completion request.
        
        Args:
            messages: List of chat messages
            tools: Optional tool definitions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            tenant_id: Tenant ID for usage tracking
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response with content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Check budget if tracking enabled
        if self.config.enable_cost_tracking and tenant_id:
            self._check_budget(tenant_id)
        
        # Get provider
        provider = await self._get_provider(self.config.provider)
        
        # Send request
        try:
            response = await provider.chat(
                messages=messages,
                tools=tools,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs
            )
            
            # Track usage
            usage_stats = UsageStats(
                prompt_tokens=response.usage["prompt_tokens"],
                completion_tokens=response.usage["completion_tokens"],
                total_tokens=response.usage["total_tokens"],
                model=response.model
            )
            
            cost_usd = None
            if self.config.enable_cost_tracking and tenant_id:
                self._token_counter.track_usage(tenant_id, usage_stats)
                cost_usd = float(usage_stats.calculate_cost())
            
            logger.info(
                f"Chat completion successful",
                extra={
                    "model": response.model,
                    "tokens": usage_stats.total_tokens,
                    "cost": cost_usd,
                    "tenant_id": tenant_id
                }
            )
            
            return LLMResponse(
                content=response.content,
                model=response.model,
                usage=usage_stats,
                finish_reason=response.finish_reason,
                tool_calls=response.tool_calls,
                cost_usd=cost_usd
            )
            
        except Exception as e:
            logger.error(
                f"Chat completion failed: {e}",
                exc_info=e,
                extra={"provider": self.config.provider, "model": self.config.model}
            )
            raise
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tenant_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamingChunk]:
        """Stream chat completion response.
        
        Args:
            messages: List of chat messages
            tools: Optional tool definitions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            tenant_id: Tenant ID for usage tracking
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Streaming chunks with partial content
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_streaming:
            raise ValueError("Streaming is disabled in configuration")
        
        # Check budget
        if self.config.enable_cost_tracking and tenant_id:
            self._check_budget(tenant_id)
        
        # Get provider
        provider = await self._get_provider(self.config.provider)
        
        try:
            async for chunk in provider.stream(
                messages=messages,
                tools=tools,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs
            ):
                yield StreamingChunk(
                    content=chunk.content,
                    finish_reason=chunk.finish_reason,
                    tool_calls=chunk.tool_calls
                )
                
        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=e)
            raise
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts.
        
        Args:
            texts: Texts to embed
            model: Override default embedding model
            provider: Override default provider (defaults to OpenAI)
            
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()
        
        # Use OpenAI for embeddings by default
        provider_name = provider or "openai"
        llm_provider = await self._get_provider(provider_name)
        
        try:
            embeddings = await llm_provider.embed(texts, model)
            
            logger.debug(
                f"Generated {len(embeddings)} embeddings",
                extra={"provider": provider_name, "model": model}
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=e)
            raise
    
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages.
        
        Args:
            messages: Messages to count
            
        Returns:
            Token count
        """
        return self._token_counter.count_messages(
            [{"role": m.role, "content": m.content} for m in messages],
            self.config.model
        )
    
    def get_usage(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get usage stats for tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Usage statistics dictionary
        """
        usage = self._token_counter.get_tenant_usage(tenant_id)
        return usage.to_dict() if usage else None
    
    def check_budget(self, tenant_id: str) -> Dict[str, Any]:
        """Check budget status for tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Budget status dictionary
        """
        return self._token_counter.check_budget(tenant_id)
    
    def set_budget_limit(self, tenant_id: str, limit_usd: float) -> None:
        """Set budget limit for tenant.
        
        Args:
            tenant_id: Tenant identifier
            limit_usd: Budget limit in USD
        """
        self._token_counter.set_budget_limit(tenant_id, limit_usd)
    
    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self._providers.values():
            await provider.close()
        
        logger.info("Closed LLM client")
    
    async def _initialize_provider(self, provider_name: str) -> None:
        """Initialize a specific provider.
        
        Args:
            provider_name: Provider to initialize
        """
        if provider_name in self._providers:
            return
        
        provider_type = ProviderType(provider_name)
        
        # Get API key from settings
        if provider_type == ProviderType.OPENAI:
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            
            config = ProviderConfig(
                provider_type=provider_type,
                api_key=api_key,
                model=self.config.model if provider_name == self.config.provider else "gpt-4-turbo",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                base_url=settings.openai_base_url,
                organization=settings.openai_organization,
            )
            
            provider = OpenAIProvider(config)
            
        elif provider_type == ProviderType.ANTHROPIC:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            
            config = ProviderConfig(
                provider_type=provider_type,
                api_key=api_key,
                model=self.config.model if provider_name == self.config.provider else "claude-3-5-sonnet-20240620",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 4096,
                top_p=self.config.top_p,
                base_url=settings.anthropic_base_url,
            )
            
            provider = AnthropicProvider(config)
            
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        await provider.initialize()
        self._providers[provider_name] = provider
        
        logger.info(f"Initialized provider: {provider_name}")
    
    async def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        """Get or initialize provider.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Provider instance
        """
        if provider_name not in self._providers:
            await self._initialize_provider(provider_name)
        
        return self._providers[provider_name]
    
    def _check_budget(self, tenant_id: str) -> None:
        """Check budget and raise error if exceeded.
        
        Args:
            tenant_id: Tenant identifier
            
        Raises:
            ValueError: If budget exceeded and enforcement enabled
        """
        if not settings.llm_enable_budget_enforcement:
            return
        
        self._token_counter.enforce_budget(tenant_id)