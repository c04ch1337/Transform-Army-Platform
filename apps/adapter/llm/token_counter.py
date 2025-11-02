"""Token counting and cost tracking for LLM usage."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import tiktoken

from ..core.logging import get_logger

logger = get_logger(__name__)


# Model pricing (cost per 1K tokens)
MODEL_PRICING = {
    # OpenAI GPT-4
    "gpt-4": {"input": Decimal("0.03"), "output": Decimal("0.06")},
    "gpt-4-32k": {"input": Decimal("0.06"), "output": Decimal("0.12")},
    "gpt-4-turbo": {"input": Decimal("0.01"), "output": Decimal("0.03")},
    "gpt-4-turbo-preview": {"input": Decimal("0.01"), "output": Decimal("0.03")},
    
    # OpenAI GPT-3.5
    "gpt-3.5-turbo": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
    "gpt-3.5-turbo-16k": {"input": Decimal("0.001"), "output": Decimal("0.002")},
    
    # Anthropic Claude 3
    "claude-3-opus-20240229": {"input": Decimal("0.015"), "output": Decimal("0.075")},
    "claude-3-sonnet-20240229": {"input": Decimal("0.003"), "output": Decimal("0.015")},
    "claude-3-haiku-20240307": {"input": Decimal("0.00025"), "output": Decimal("0.00125")},
    
    # Claude 3.5
    "claude-3-5-sonnet-20240620": {"input": Decimal("0.003"), "output": Decimal("0.015")},
    
    # Embeddings
    "text-embedding-ada-002": {"input": Decimal("0.0001"), "output": Decimal("0")},
    "text-embedding-3-small": {"input": Decimal("0.00002"), "output": Decimal("0")},
    "text-embedding-3-large": {"input": Decimal("0.00013"), "output": Decimal("0")},
}


@dataclass
class UsageStats:
    """Token usage statistics."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_cost(self) -> Decimal:
        """Calculate cost for this usage.
        
        Returns:
            Cost in USD
        """
        pricing = MODEL_PRICING.get(self.model)
        
        if not pricing:
            logger.warning(f"Unknown model pricing: {self.model}")
            return Decimal("0")
        
        input_cost = (Decimal(self.prompt_tokens) / Decimal("1000")) * pricing["input"]
        output_cost = (Decimal(self.completion_tokens) / Decimal("1000")) * pricing["output"]
        
        return input_cost + output_cost
    
    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "cost_usd": float(self.calculate_cost()),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TenantUsage:
    """Usage tracking for a tenant."""
    
    tenant_id: str
    total_tokens: int = 0
    total_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    request_count: int = 0
    last_request: Optional[datetime] = None
    usage_by_model: Dict[str, int] = field(default_factory=dict)
    
    def add_usage(self, stats: UsageStats) -> None:
        """Add usage stats.
        
        Args:
            stats: Usage statistics to add
        """
        self.total_tokens += stats.total_tokens
        self.total_cost += stats.calculate_cost()
        self.request_count += 1
        self.last_request = stats.timestamp
        
        # Track by model
        if stats.model not in self.usage_by_model:
            self.usage_by_model[stats.model] = 0
        self.usage_by_model[stats.model] += stats.total_tokens
    
    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "tenant_id": self.tenant_id,
            "total_tokens": self.total_tokens,
            "total_cost_usd": float(self.total_cost),
            "request_count": self.request_count,
            "last_request": self.last_request.isoformat() if self.last_request else None,
            "usage_by_model": self.usage_by_model,
        }


class TokenCounter:
    """Token counter and cost tracker.
    
    Provides:
    - Token counting for different model families
    - Cost calculation per request
    - Usage tracking by tenant
    - Budget enforcement
    """
    
    def __init__(self):
        """Initialize token counter."""
        self._tokenizers: Dict[str, tiktoken.Encoding] = {}
        self._tenant_usage: Dict[str, TenantUsage] = {}
        self._budget_limits: Dict[str, Decimal] = {}
        
        logger.info("Initialized TokenCounter")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for given model.
        
        Args:
            text: Text to count
            model: Model name
            
        Returns:
            Token count
        """
        # Get tokenizer for model
        encoding = self._get_tokenizer(model)
        
        if encoding:
            return len(encoding.encode(text))
        else:
            # Fallback estimation: ~4 chars per token
            return len(text) // 4
    
    def count_messages(self, messages: List[Dict[str, str]], model: str) -> int:
        """Count tokens in message list.
        
        Args:
            messages: List of messages
            model: Model name
            
        Returns:
            Total token count
        """
        total = 0
        
        for message in messages:
            # Count role tokens
            total += self.count_tokens(message.get("role", ""), model)
            
            # Count content tokens
            content = message.get("content", "")
            if content:
                total += self.count_tokens(content, model)
            
            # Add message formatting overhead
            total += 4
        
        # Add response priming overhead
        total += 3
        
        return total
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> Decimal:
        """Calculate cost for token usage.
        
        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            model: Model name
            
        Returns:
            Cost in USD
        """
        stats = UsageStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model
        )
        
        return stats.calculate_cost()
    
    def track_usage(
        self,
        tenant_id: str,
        stats: UsageStats
    ) -> None:
        """Track usage for tenant.
        
        Args:
            tenant_id: Tenant identifier
            stats: Usage statistics
        """
        if tenant_id not in self._tenant_usage:
            self._tenant_usage[tenant_id] = TenantUsage(tenant_id=tenant_id)
        
        self._tenant_usage[tenant_id].add_usage(stats)
        
        logger.debug(
            f"Tracked usage for tenant {tenant_id}",
            extra={
                "tokens": stats.total_tokens,
                "cost": float(stats.calculate_cost()),
                "model": stats.model
            }
        )
    
    def get_tenant_usage(self, tenant_id: str) -> Optional[TenantUsage]:
        """Get usage stats for tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant usage or None
        """
        return self._tenant_usage.get(tenant_id)
    
    def set_budget_limit(self, tenant_id: str, limit_usd: float) -> None:
        """Set budget limit for tenant.
        
        Args:
            tenant_id: Tenant identifier
            limit_usd: Budget limit in USD
        """
        self._budget_limits[tenant_id] = Decimal(str(limit_usd))
        
        logger.info(
            f"Set budget limit for tenant {tenant_id}: ${limit_usd}"
        )
    
    def check_budget(self, tenant_id: str) -> Dict[str, any]:
        """Check if tenant is within budget.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Budget status dict
        """
        usage = self._tenant_usage.get(tenant_id)
        limit = self._budget_limits.get(tenant_id)
        
        if not limit:
            return {
                "has_limit": False,
                "within_budget": True,
                "used": float(usage.total_cost) if usage else 0.0,
                "limit": None,
                "remaining": None,
                "percentage": 0.0
            }
        
        used = usage.total_cost if usage else Decimal("0")
        remaining = limit - used
        percentage = float((used / limit) * Decimal("100")) if limit > 0 else 0.0
        
        return {
            "has_limit": True,
            "within_budget": remaining > 0,
            "used": float(used),
            "limit": float(limit),
            "remaining": float(remaining),
            "percentage": percentage
        }
    
    def enforce_budget(self, tenant_id: str) -> bool:
        """Check if tenant can make more requests.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if within budget, False if exceeded
            
        Raises:
            ValueError: If budget exceeded
        """
        budget = self.check_budget(tenant_id)
        
        if budget["has_limit"] and not budget["within_budget"]:
            logger.warning(
                f"Budget exceeded for tenant {tenant_id}",
                extra=budget
            )
            raise ValueError(
                f"Budget limit exceeded. Used: ${budget['used']:.4f}, "
                f"Limit: ${budget['limit']:.4f}"
            )
        
        # Warn at 80% threshold
        if budget["has_limit"] and budget["percentage"] >= 80:
            logger.warning(
                f"Budget threshold warning for tenant {tenant_id}",
                extra=budget
            )
        
        return True
    
    def get_model_pricing(self, model: str) -> Optional[Dict[str, Decimal]]:
        """Get pricing for model.
        
        Args:
            model: Model name
            
        Returns:
            Pricing dict or None
        """
        return MODEL_PRICING.get(model)
    
    def list_supported_models(self) -> List[str]:
        """List models with known pricing.
        
        Returns:
            List of model names
        """
        return list(MODEL_PRICING.keys())
    
    def reset_tenant_usage(self, tenant_id: str) -> None:
        """Reset usage stats for tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        if tenant_id in self._tenant_usage:
            del self._tenant_usage[tenant_id]
            logger.info(f"Reset usage for tenant {tenant_id}")
    
    def get_all_usage(self) -> Dict[str, Dict]:
        """Get usage for all tenants.
        
        Returns:
            Dict of tenant_id -> usage dict
        """
        return {
            tenant_id: usage.to_dict()
            for tenant_id, usage in self._tenant_usage.items()
        }
    
    def _get_tokenizer(self, model: str) -> Optional[tiktoken.Encoding]:
        """Get or create tokenizer for model.
        
        Args:
            model: Model name
            
        Returns:
            Tokenizer or None
        """
        if model in self._tokenizers:
            return self._tokenizers[model]
        
        try:
            # Try to get model-specific encoding
            encoding = tiktoken.encoding_for_model(model)
            self._tokenizers[model] = encoding
            return encoding
        except KeyError:
            # Use cl100k_base as fallback (GPT-4/3.5 encoding)
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                self._tokenizers[model] = encoding
                logger.debug(f"Using cl100k_base encoding for model: {model}")
                return encoding
            except Exception as e:
                logger.warning(f"Could not get tokenizer for model {model}: {e}")
                return None


# Global counter instance
_global_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """Get global token counter instance.
    
    Returns:
        Global token counter
    """
    global _global_counter
    
    if _global_counter is None:
        _global_counter = TokenCounter()
    
    return _global_counter