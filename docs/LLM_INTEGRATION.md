# LLM Integration Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-02  
**System:** Transform Army AI LLM Integration

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Models and Providers](#supported-models-and-providers)
3. [Configuration](#configuration)
4. [Architecture](#architecture)
5. [Using the LLM Client](#using-the-llm-client)
6. [Tool Calling](#tool-calling)
7. [Prompt Engineering](#prompt-engineering)
8. [Streaming Responses](#streaming-responses)
9. [Token Management](#token-management)
10. [Cost Tracking](#cost-tracking)
11. [Adding New Providers](#adding-new-providers)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The Transform Army AI LLM integration provides a unified interface to multiple Large Language Model providers, enabling intelligent agent orchestration with:

- **Multi-provider support**: OpenAI, Anthropic, and extensible to others
- **Function calling**: Agents can use tools to interact with external systems
- **Streaming**: Real-time token-by-token response streaming
- **Cost tracking**: Automatic usage monitoring and budget enforcement
- **Token management**: Context window optimization and token counting
- **Rate limiting**: Per-tenant request throttling

### Key Components

```
src/llm/
├── client.py              # Main LLM client interface
├── providers/
│   ├── base.py           # Base provider interface
│   ├── openai.py         # OpenAI implementation
│   └── anthropic.py      # Anthropic implementation
├── tools.py              # Tool registry for function calling
├── prompt_builder.py     # Prompt template management
└── token_counter.py      # Token counting and cost tracking
```

---

## Supported Models and Providers

### OpenAI

| Model | Context Window | Input Cost | Output Cost | Best For |
|-------|---------------|------------|-------------|----------|
| `gpt-4-turbo` | 128K tokens | $0.01/1K | $0.03/1K | Complex reasoning, coding |
| `gpt-4` | 8K tokens | $0.03/1K | $0.06/1K | High accuracy tasks |
| `gpt-3.5-turbo` | 16K tokens | $0.0005/1K | $0.0015/1K | Fast, cost-effective |

**Embeddings:**
- `text-embedding-3-small`: $0.00002/1K tokens, 1536 dimensions
- `text-embedding-3-large`: $0.00013/1K tokens, 3072 dimensions

### Anthropic

| Model | Context Window | Input Cost | Output Cost | Best For |
|-------|---------------|------------|-------------|----------|
| `claude-3-5-sonnet-20240620` | 200K tokens | $0.003/1K | $0.015/1K | Balanced performance |
| `claude-3-opus-20240229` | 200K tokens | $0.015/1K | $0.075/1K | Complex tasks, highest quality |
| `claude-3-haiku-20240307` | 200K tokens | $0.00025/1K | $0.00125/1K | Fast, cost-effective |

**Note:** Anthropic does not provide embedding models. Use OpenAI for embeddings.

---

## Configuration

### Environment Variables

Add to [`apps/adapter/.env`](apps/adapter/.env):

```bash
# LLM Configuration
ADAPTER_LLM_PROVIDER=openai                    # Primary provider (openai, anthropic)
ADAPTER_LLM_MODEL=gpt-4-turbo                 # Default model
ADAPTER_LLM_TEMPERATURE=0.7                   # Response creativity (0.0-2.0)
ADAPTER_LLM_MAX_TOKENS=4096                   # Max tokens per response
ADAPTER_LLM_TOP_P=1.0                         # Nucleus sampling (0.0-1.0)

# Provider API Keys
ADAPTER_OPENAI_API_KEY=sk-...                 # OpenAI API key
ADAPTER_OPENAI_ORGANIZATION=org-...           # Optional: OpenAI org ID
ADAPTER_ANTHROPIC_API_KEY=sk-ant-...          # Anthropic API key

# Usage Limits
ADAPTER_LLM_TOKEN_LIMIT_PER_REQUEST=128000    # Max tokens per request
ADAPTER_LLM_REQUESTS_PER_MINUTE=60            # Rate limit per tenant
ADAPTER_LLM_BUDGET_LIMIT_USD=100.0            # Monthly budget per tenant

# Cost Tracking
ADAPTER_LLM_ENABLE_COST_TRACKING=true         # Track usage and costs
ADAPTER_LLM_ENABLE_BUDGET_ENFORCEMENT=false   # Reject requests over budget
ADAPTER_LLM_BUDGET_WARNING_THRESHOLD=0.8      # Warn at 80% budget

# Streaming
ADAPTER_LLM_ENABLE_STREAMING=true             # Enable SSE streaming
```

### Configuration Object

```python
from src.llm.client import LLMClient, LLMConfig

# Use default settings from environment
client = LLMClient()

# Or provide custom config
config = LLMConfig(
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.7,
    max_tokens=2000,
    enable_streaming=True,
    enable_cost_tracking=True
)

client = LLMClient(config)
```

---

## Architecture

### Provider Interface

All LLM providers implement the [`BaseLLMProvider`](apps/adapter/src/llm/providers/base.py) interface:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> CompletionResponse:
        """Send chat completion request."""
        
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion."""
        
    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings."""
```

### Message Format

```python
from src.llm.providers.base import Message

# System message
system_msg = Message(
    role="system",
    content="You are a helpful AI assistant."
)

# User message
user_msg = Message(
    role="user",
    content="What is the capital of France?"
)

# Assistant message
assistant_msg = Message(
    role="assistant",
    content="The capital of France is Paris."
)

# Tool result message
tool_result_msg = Message(
    role="tool",
    content='{"result": "success"}',
    tool_call_id="call_123",
    name="search_database"
)
```

---

## Using the LLM Client

### Basic Chat Completion

```python
from src.llm.client import LLMClient
from src.llm.providers.base import Message

# Initialize client
client = LLMClient()
await client.initialize()

# Create messages
messages = [
    Message(role="system", content="You are a helpful assistant."),
    Message(role="user", content="Explain quantum computing in simple terms.")
]

# Get response
response = await client.chat(
    messages=messages,
    temperature=0.7,
    max_tokens=500,
    tenant_id="tenant_123"
)

print(f"Response: {response.content}")
print(f"Tokens used: {response.usage.total_tokens}")
print(f"Cost: ${response.cost_usd:.4f}")
```

### Streaming Responses

```python
from src.llm.client import LLMClient
from src.llm.providers.base import Message

client = LLMClient()
await client.initialize()

messages = [
    Message(role="user", content="Write a short story about a robot.")
]

# Stream response
async for chunk in client.stream(messages, tenant_id="tenant_123"):
    print(chunk.content, end="", flush=True)
    
    if chunk.finish_reason:
        print(f"\n\nFinished: {chunk.finish_reason}")
```

### Embeddings

```python
from src.llm.client import LLMClient

client = LLMClient()
await client.initialize()

texts = [
    "Machine learning is a subset of AI",
    "Deep learning uses neural networks",
    "Natural language processing handles text"
]

# Generate embeddings
embeddings = await client.embed(
    texts=texts,
    model="text-embedding-3-small"
)

print(f"Generated {len(embeddings)} embeddings")
print(f"Dimension: {len(embeddings[0])}")
```

---

## Tool Calling

### Registering Tools

```python
from src.llm.tools import ToolRegistry, get_tool_registry

registry = get_tool_registry()

# Define tool handler
async def search_database(query: str, limit: int = 10, **kwargs) -> dict:
    """Search the database."""
    # Perform search
    results = await db.search(query, limit=limit)
    return {"results": results, "count": len(results)}

# Register tool
registry.register(
    name="search_database",
    description="Search the company database for information",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return",
                "default": 10
            }
        },
        "required": ["query"]
    },
    handler=search_database,
    category="database"
)
```

### Using Tools with LLM

```python
from src.llm.client import LLMClient
from src.llm.providers.base import Message
from src.llm.tools import get_tool_registry

client = LLMClient()
await client.initialize()

registry = get_tool_registry()

# Get tool schemas
tools = registry.get_schemas(
    provider="openai",
    tool_names=["search_database", "create_ticket"]
)

# Call LLM with tools
messages = [
    Message(role="user", content="Find all customers in California")
]

response = await client.chat(
    messages=messages,
    tools=tools,
    tenant_id="tenant_123"
)

# Execute tool calls if present
if response.tool_calls:
    for tool_call in response.tool_calls:
        # Parse and execute
        from src.llm.tools import ToolCall
        
        parsed = provider.parse_tool_call(tool_call)
        tc = ToolCall(
            id=parsed["id"],
            name=parsed["name"],
            arguments=parsed["arguments"]
        )
        
        result = await registry.execute(tc, context={"tenant_id": "tenant_123"})
        print(f"Tool result: {result.result}")
```

### Tool Execution Loop

The [`AgentExecutor`](apps/adapter/src/orchestration/agent_executor.py) handles the complete tool calling loop:

```python
from src.orchestration.agent_executor import AgentExecutor

executor = AgentExecutor()

agent_config = {
    "agent_id": "agent_001",
    "agent_type": "support_concierge",
    "tools": ["search_knowledge", "create_ticket"],
    "temperature": 0.7
}

input_data = {
    "user_query": "How do I reset my password?",
    "tenant_id": "tenant_123"
}

# Execute with automatic tool calling
result = await executor.execute(agent_config, input_data)

print(f"Agent response: {result['output']['message']}")
print(f"Tools used: {len(result['tool_calls'])}")
print(f"Total tokens: {result['tokens_used']}")
```

---

## Prompt Engineering

### Loading Templates

Prompts are stored in [`packages/prompt-pack/`](packages/prompt-pack/):

```
packages/prompt-pack/
├── templates/              # Agent-specific templates
│   ├── bdr-concierge-template.md
│   ├── support-concierge-template.md
│   └── ...
└── system/                 # Reusable system prompts
    ├── escalation-protocol.md
    └── tool-usage-guidelines.md
```

### Building Prompts

```python
from src.llm.prompt_builder import PromptBuilder

builder = PromptBuilder()

# Load agent template
template = builder.load_template("support_concierge")

# Build system message
system_prompt = builder.build_system_message(
    agent_type="support_concierge",
    additional_context="Customer is VIP tier",
    include_guidelines=True
)

# Build user message with variables
user_message = builder.build_user_message(
    agent_type="support_concierge",
    variables={
        "ticket_id": "TICKET-123",
        "customer_name": "John Doe",
        "issue": "Cannot log in"
    }
)
```

### Variable Substitution

Templates support multiple formats:

```markdown
# Template Example

Hello {{customer_name}},

Thank you for contacting us about {issue}.

Your ticket ID is $ticket_id.
```

```python
variables = {
    "customer_name": "John Doe",
    "issue": "login problem",
    "ticket_id": "TICKET-123"
}

result = builder._substitute_variables(template, variables)
# Replaces {{customer_name}}, {issue}, and $ticket_id
```

### Context Window Management

```python
from src.llm.prompt_builder import PromptBuilder

builder = PromptBuilder()

# Long conversation
messages = [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "Message 1"},
    {"role": "assistant", "content": "Response 1"},
    # ... many more messages
]

# Truncate to fit context window
truncated = builder.truncate_to_context_window(
    messages=messages,
    max_tokens=4000,
    preserve_recent=5  # Keep last 5 messages
)

# Truncated list preserves:
# - System message (always kept)
# - As many older messages as fit
# - Last 5 messages (always kept)
```

---

## Streaming Responses

### Backend Streaming

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.get("/agent/stream")
async def stream_agent():
    """Stream agent responses."""
    
    async def event_generator():
        client = LLMClient()
        await client.initialize()
        
        messages = [Message(role="user", content="Tell me a story")]
        
        async for chunk in client.stream(messages, tenant_id="tenant_123"):
            # Send Server-Sent Event
            yield f"data: {json.dumps({'content': chunk.content})}\n\n"
            
            if chunk.finish_reason:
                yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Frontend Consumption

```typescript
// React example
const [content, setContent] = useState("");

const streamResponse = async () => {
  const response = await fetch("/api/agent/stream");
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");
    
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6));
        if (data.content) {
          setContent(prev => prev + data.content);
        }
      }
    }
  }
};
```

---

## Token Management

### Token Counting

```python
from src.llm.token_counter import TokenCounter, get_token_counter

counter = get_token_counter()

# Count tokens in text
text = "Hello, how are you today?"
tokens = counter.count_tokens(text, model="gpt-4-turbo")
print(f"Tokens: {tokens}")

# Count tokens in messages
messages = [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"}
]
tokens = counter.count_messages(messages, model="gpt-4-turbo")
print(f"Total tokens: {tokens}")
```

### Cost Calculation

```python
from src.llm.token_counter import TokenCounter

counter = TokenCounter()

# Calculate cost
cost = counter.calculate_cost(
    prompt_tokens=1000,
    completion_tokens=500,
    model="gpt-4-turbo"
)

print(f"Cost: ${float(cost):.4f}")
```

---

## Cost Tracking

### Per-Tenant Tracking

```python
from src.llm.client import LLMClient
from src.llm.token_counter import UsageStats

client = LLMClient()

# Usage is automatically tracked when tenant_id is provided
response = await client.chat(
    messages=messages,
    tenant_id="tenant_123"
)

# Get usage stats
usage = client.get_usage("tenant_123")
print(f"Total tokens: {usage['total_tokens']}")
print(f"Total cost: ${usage['total_cost_usd']:.4f}")
print(f"Requests: {usage['request_count']}")
```

### Budget Management

```python
from src.llm.client import LLMClient

client = LLMClient()

# Set monthly budget limit
client.set_budget_limit("tenant_123", limit_usd=100.0)

# Check budget status
budget = client.check_budget("tenant_123")
print(f"Used: ${budget['used']:.2f}")
print(f"Remaining: ${budget['remaining']:.2f}")
print(f"Percentage: {budget['percentage']:.1f}%")

# Budget enforcement (if enabled in config)
# Will raise ValueError if budget exceeded
try:
    response = await client.chat(messages, tenant_id="tenant_123")
except ValueError as e:
    print(f"Budget exceeded: {e}")
```

### Usage Reports

```python
from src.llm.token_counter import get_token_counter

counter = get_token_counter()

# Get all tenant usage
all_usage = counter.get_all_usage()

for tenant_id, usage in all_usage.items():
    print(f"\nTenant: {tenant_id}")
    print(f"  Tokens: {usage['total_tokens']}")
    print(f"  Cost: ${usage['total_cost_usd']:.4f}")
    print(f"  Requests: {usage['request_count']}")
    print(f"  By model: {usage['usage_by_model']}")
```

---

## Adding New Providers

### 1. Create Provider Class

Create [`apps/adapter/src/llm/providers/your_provider.py`](apps/adapter/src/llm/providers/):

```python
from typing import AsyncIterator, List
from .base import BaseLLMProvider, ProviderType, Message, CompletionResponse, StreamChunk

class YourProvider(BaseLLMProvider):
    """Your LLM provider implementation."""
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.YOUR_PROVIDER
    
    async def initialize(self) -> None:
        """Initialize provider client."""
        # Initialize your client
        self._client = YourProviderClient(api_key=self.config.api_key)
    
    async def chat(self, messages: List[Message], **kwargs) -> CompletionResponse:
        """Implement chat completion."""
        # Convert messages to provider format
        # Call provider API
        # Return CompletionResponse
        pass
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[StreamChunk]:
        """Implement streaming."""
        # Stream from provider
        # Yield StreamChunk objects
        pass
    
    async def embed(self, texts: List[str], model: str = None) -> List[List[float]]:
        """Implement embeddings."""
        pass
    
    def count_tokens(self, messages: List[Message]) -> int:
        """Count tokens."""
        # Implement token counting
        pass
    
    def format_tool_call(self, tool_call: dict) -> dict:
        """Format tool call for your provider."""
        pass
    
    def parse_tool_call(self, tool_call: dict) -> dict:
        """Parse provider tool call to generic format."""
        pass
```

### 2. Register Provider

Update [`apps/adapter/src/llm/providers/__init__.py`](apps/adapter/src/llm/providers/__init__.py):

```python
from .your_provider import YourProvider

__all__ = [
    "BaseLLMProvider",
    "ProviderConfig",
    "OpenAIProvider",
    "AnthropicProvider",
    "YourProvider",  # Add your provider
]
```

### 3. Add to LLM Client

Update [`apps/adapter/src/llm/client.py`](apps/adapter/src/llm/client.py):

```python
async def _initialize_provider(self, provider_name: str) -> None:
    # ... existing code ...
    
    elif provider_type == ProviderType.YOUR_PROVIDER:
        api_key = settings.your_provider_api_key
        if not api_key:
            raise ValueError("YOUR_PROVIDER_API_KEY not configured")
        
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            model=self.config.model,
            # ... other config
        )
        
        provider = YourProvider(config)
```

### 4. Add Pricing

Update [`apps/adapter/src/llm/token_counter.py`](apps/adapter/src/llm/token_counter.py):

```python
MODEL_PRICING = {
    # ... existing models ...
    
    # Your provider models
    "your-model-name": {
        "input": Decimal("0.001"),
        "output": Decimal("0.002")
    },
}
```

---

## Best Practices

### 1. Model Selection

- **GPT-4-Turbo**: Complex reasoning, code generation, detailed analysis
- **GPT-3.5-Turbo**: Fast responses, simple tasks, high-volume use cases
- **Claude 3.5 Sonnet**: Balanced performance, large context windows
- **Claude 3 Haiku**: Cost-effective, simple queries

### 2. Temperature Settings

```python
# Deterministic outputs (summaries, structured data)
temperature = 0.0

# Balanced creativity (chat, Q&A)
temperature = 0.7

# High creativity (brainstorming, creative writing)
temperature = 1.0
```

### 3. Token Optimization

```python
# Truncate old conversation history
messages = builder.truncate_to_context_window(
    messages, 
    max_tokens=8000,
    preserve_recent=10
)

# Use smaller models for simple tasks
if is_simple_query(user_input):
    config.model = "gpt-3.5-turbo"
```

### 4. Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_llm_with_retry():
    try:
        return await client.chat(messages, tenant_id=tenant_id)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise
```

### 5. Caching

```python
from functools import lru_cache

# Cache embeddings
@lru_cache(maxsize=1000)
async def get_cached_embedding(text: str) -> List[float]:
    embeddings = await client.embed([text])
    return embeddings[0]
```

---

## Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error:** `ValueError: OPENAI_API_KEY not configured`

**Solution:**
```bash
# Set in .env file
ADAPTER_OPENAI_API_KEY=sk-your-key-here

# Or set environment variable
export ADAPTER_OPENAI_API_KEY=sk-your-key-here
```

#### 2. Budget Exceeded

**Error:** `ValueError: Budget limit exceeded`

**Solution:**
```python
# Increase budget limit
client.set_budget_limit("tenant_123", limit_usd=200.0)

# Or disable enforcement
# In .env:
ADAPTER_LLM_ENABLE_BUDGET_ENFORCEMENT=false
```

#### 3. Token Limit Exceeded

**Error:** `Invalid request: maximum context length exceeded`

**Solution:**
```python
# Truncate messages
from src.llm.prompt_builder import PromptBuilder

builder = PromptBuilder()
messages = builder.truncate_to_context_window(
    messages,
    max_tokens=4000  # Adjust based on model
)
```

#### 4. Rate Limit Exceeded

**Error:** `Rate limit reached for requests`

**Solution:**
```python
# Implement exponential backoff
import asyncio
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=60))
async def call_with_backoff():
    return await client.chat(messages)
```

### Debug Logging

Enable debug logging in [`.env`](apps/adapter/.env):

```bash
ADAPTER_LOG_LEVEL=DEBUG
```

Check logs:

```python
from src.core.logging import get_logger

logger = get_logger(__name__)
logger.debug("LLM request details", extra={"messages": messages})
```

---

## Performance Optimization

### 1. Connection Pooling

The LLM client maintains connection pools automatically:

```python
# Reuse the same client instance
client = LLMClient()
await client.initialize()

# Make multiple requests
for i in range(10):
    response = await client.chat(messages)
```

### 2. Parallel Requests

```python
import asyncio

# Execute multiple requests in parallel
tasks = [
    client.chat(messages1, tenant_id="tenant_1"),
    client.chat(messages2, tenant_id="tenant_2"),
    client.chat(messages3, tenant_id="tenant_3"),
]

responses = await asyncio.gather(*tasks)
```

### 3. Batching

```python
# Batch embeddings
texts = ["text 1", "text 2", "text 3", ..., "text 100"]

# More efficient than individual calls
embeddings = await client.embed(texts)
```

---

## Monitoring

### Metrics to Track

1. **Token Usage:**
   - Prompt tokens per request
   - Completion tokens per request
   - Total tokens per tenant

2. **Costs:**
   - Cost per request
   - Daily/monthly spend per tenant
   - Budget utilization percentage

3. **Performance:**
   - Request latency
   - Time to first token (streaming)
   - Tool call execution time

4. **Quality:**
   - Tool call success rate
   - Response completion rate
   - Error rate by type

### Example Monitoring

```python
from src.llm.token_counter import get_token_counter
import time

counter = get_token_counter()

start = time.time()
response = await client.chat(messages, tenant_id="tenant_123")
latency = time.time() - start

# Log metrics
logger.info(
    "LLM request completed",
    extra={
        "tenant_id": "tenant_123",
        "model": response.model,
        "tokens": response.usage.total_tokens,
        "cost": response.cost_usd,
        "latency_ms": latency * 1000,
        "tool_calls": len(response.tool_calls or [])
    }
)
```

---

## Security Considerations

1. **API Key Management:**
   - Store keys in environment variables
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys regularly
   - Never commit keys to version control

2. **Input Validation:**
   ```python
   def validate_input(user_input: str) -> str:
       # Sanitize input
       if len(user_input) > 10000:
           raise ValueError("Input too long")
       
       # Check for injection attempts
       if "<script>" in user_input.lower():
           raise ValueError("Invalid input")
       
       return user_input
   ```

3. **Output Filtering:**
   ```python
   def filter_output(response: str) -> str:
       # Remove sensitive information
       # Check for harmful content
       # Apply content policy
       return filtered_response
   ```

4. **Rate Limiting:**
   - Enforce per-tenant limits
   - Implement request throttling
   - Monitor for abuse

---

## Next Steps

1. **Implement Agent Workflows:** Use the LLM client in [agent orchestration](docs/agent-orchestration.md)
2. **Add Custom Tools:** Register tools for your specific use cases
3. **Optimize Prompts:** Iterate on prompt templates for better results
4. **Monitor Usage:** Set up cost tracking and alerting
5. **Scale:** Add more providers or models as needed

---

**Document Control**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-02 | Initial LLM integration documentation |