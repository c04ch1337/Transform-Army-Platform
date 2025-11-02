"""Integration tests for LLM functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.llm.client import LLMClient, LLMConfig, LLMResponse
from src.llm.providers.base import Message, CompletionResponse, ProviderType
from src.llm.providers.openai import OpenAIProvider
from src.llm.providers.anthropic import AnthropicProvider
from src.llm.tools import ToolRegistry, Tool, ToolCall, ToolResult
from src.llm.token_counter import TokenCounter, UsageStats
from src.llm.prompt_builder import PromptBuilder


@pytest.fixture
def llm_config():
    """Create test LLM configuration."""
    return LLMConfig(
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=1000,
        enable_streaming=True,
        enable_cost_tracking=True
    )


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_choice = Mock()
    mock_choice.message.content = "Test response"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"
    
    mock_usage = Mock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.model = "gpt-4-turbo"
    mock_response.usage = mock_usage
    
    return mock_response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    mock_block = Mock()
    mock_block.type = "text"
    mock_block.text = "Test response from Claude"
    
    mock_usage = Mock()
    mock_usage.input_tokens = 15
    mock_usage.output_tokens = 25
    
    mock_response = Mock()
    mock_response.content = [mock_block]
    mock_response.model = "claude-3-5-sonnet-20240620"
    mock_response.usage = mock_usage
    mock_response.stop_reason = "end_turn"
    
    return mock_response


class TestLLMClient:
    """Test LLM client functionality."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, llm_config):
        """Test LLM client initialization."""
        client = LLMClient(llm_config)
        
        assert client.config.provider == "openai"
        assert client.config.model == "gpt-4-turbo"
        assert not client._initialized
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, llm_config, mock_openai_response):
        """Test chat completion."""
        client = LLMClient(llm_config)
        
        with patch.object(client, '_get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.chat.return_value = CompletionResponse(
                content="Test response",
                model="gpt-4-turbo",
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                },
                finish_reason="stop"
            )
            mock_get_provider.return_value = mock_provider
            
            messages = [
                Message(role="system", content="You are a helpful assistant"),
                Message(role="user", content="Hello")
            ]
            
            response = await client.chat(messages, tenant_id="test-tenant")
            
            assert response.content == "Test response"
            assert response.model == "gpt-4-turbo"
            assert response.usage.total_tokens == 30
            assert response.cost_usd is not None
    
    @pytest.mark.asyncio
    async def test_streaming(self, llm_config):
        """Test streaming responses."""
        client = LLMClient(llm_config)
        
        async def mock_stream():
            from src.llm.providers.base import StreamChunk
            yield StreamChunk(content="Hello ")
            yield StreamChunk(content="world")
            yield StreamChunk(content="!", finish_reason="stop")
        
        with patch.object(client, '_get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.stream.return_value = mock_stream()
            mock_get_provider.return_value = mock_provider
            
            messages = [Message(role="user", content="Test")]
            
            chunks = []
            async for chunk in client.stream(messages):
                chunks.append(chunk.content)
            
            assert "".join(chunks) == "Hello world!"
    
    @pytest.mark.asyncio
    async def test_token_counting(self, llm_config):
        """Test token counting."""
        client = LLMClient(llm_config)
        
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello world")
        ]
        
        token_count = client.count_tokens(messages)
        
        assert token_count > 0
        assert isinstance(token_count, int)
    
    @pytest.mark.asyncio
    async def test_budget_tracking(self, llm_config):
        """Test budget tracking."""
        client = LLMClient(llm_config)
        
        # Set budget limit
        client.set_budget_limit("test-tenant", 10.0)
        
        # Check budget
        budget = client.check_budget("test-tenant")
        
        assert budget["has_limit"]
        assert budget["limit"] == 10.0
        assert budget["within_budget"]


class TestOpenAIProvider:
    """Test OpenAI provider."""
    
    @pytest.mark.asyncio
    async def test_provider_initialization(self):
        """Test provider initialization."""
        from src.llm.providers.base import ProviderConfig
        
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4-turbo",
            temperature=0.7
        )
        
        provider = OpenAIProvider(config)
        
        assert provider.provider_type == ProviderType.OPENAI
        assert provider.config.model == "gpt-4-turbo"
    
    @pytest.mark.asyncio
    async def test_format_tool_call(self):
        """Test tool call formatting."""
        from src.llm.providers.base import ProviderConfig
        
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4-turbo"
        )
        
        provider = OpenAIProvider(config)
        
        tool_call = {
            "name": "search",
            "description": "Search for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
        
        formatted = provider.format_tool_call(tool_call)
        
        assert formatted["type"] == "function"
        assert formatted["function"]["name"] == "search"
    
    def test_token_counting(self):
        """Test token counting."""
        from src.llm.providers.base import ProviderConfig
        
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4-turbo"
        )
        
        provider = OpenAIProvider(config)
        
        messages = [
            Message(role="user", content="Hello world")
        ]
        
        count = provider.count_tokens(messages)
        
        assert count > 0


class TestAnthropicProvider:
    """Test Anthropic provider."""
    
    @pytest.mark.asyncio
    async def test_provider_initialization(self):
        """Test provider initialization."""
        from src.llm.providers.base import ProviderConfig
        
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet-20240620",
            temperature=0.7,
            max_tokens=4096
        )
        
        provider = AnthropicProvider(config)
        
        assert provider.provider_type == ProviderType.ANTHROPIC
        assert provider.config.model == "claude-3-5-sonnet-20240620"
    
    @pytest.mark.asyncio
    async def test_format_tool_call(self):
        """Test tool call formatting for Anthropic."""
        from src.llm.providers.base import ProviderConfig
        
        config = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096
        )
        
        provider = AnthropicProvider(config)
        
        tool_call = {
            "function": {
                "name": "search",
                "description": "Search for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        }
        
        formatted = provider.format_tool_call(tool_call)
        
        assert formatted["name"] == "search"
        assert "input_schema" in formatted


class TestToolRegistry:
    """Test tool registry."""
    
    @pytest.fixture
    def registry(self):
        """Create fresh tool registry."""
        registry = ToolRegistry()
        registry.clear()
        return registry
    
    @pytest.mark.asyncio
    async def test_register_tool(self, registry):
        """Test tool registration."""
        async def test_handler(**kwargs):
            return {"result": "success"}
        
        tool = registry.register(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            },
            handler=test_handler,
            category="test"
        )
        
        assert tool.name == "test_tool"
        assert tool.category == "test"
        assert registry.get_tool_count() == 1
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, registry):
        """Test tool execution."""
        async def test_handler(query: str, **kwargs):
            return f"Result for: {query}"
        
        registry.register(
            name="search",
            description="Search tool",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        tool_call = ToolCall(
            id="call_123",
            name="search",
            arguments={"query": "test"}
        )
        
        result = await registry.execute(tool_call)
        
        assert result.success
        assert result.result == "Result for: test"
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self, registry):
        """Test tool error handling."""
        async def failing_handler(**kwargs):
            raise ValueError("Test error")
        
        registry.register(
            name="failing_tool",
            description="Tool that fails",
            parameters={"type": "object"},
            handler=failing_handler
        )
        
        tool_call = ToolCall(
            id="call_123",
            name="failing_tool",
            arguments={}
        )
        
        result = await registry.execute(tool_call)
        
        assert not result.success
        assert "Test error" in result.error
    
    def test_get_schemas(self, registry):
        """Test getting tool schemas."""
        async def test_handler(**kwargs):
            return {}
        
        registry.register(
            name="tool1",
            description="First tool",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        registry.register(
            name="tool2",
            description="Second tool",
            parameters={"type": "object"},
            handler=test_handler
        )
        
        schemas = registry.get_schemas(provider="openai")
        
        assert len(schemas) == 2
        assert schemas[0]["type"] == "function"


class TestTokenCounter:
    """Test token counter."""
    
    @pytest.fixture
    def counter(self):
        """Create token counter."""
        return TokenCounter()
    
    def test_count_tokens(self, counter):
        """Test token counting."""
        text = "Hello, world!"
        count = counter.count_tokens(text, "gpt-4-turbo")
        
        assert count > 0
        assert isinstance(count, int)
    
    def test_calculate_cost(self, counter):
        """Test cost calculation."""
        cost = counter.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4-turbo"
        )
        
        assert cost > 0
    
    def test_track_usage(self, counter):
        """Test usage tracking."""
        stats = UsageStats(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model="gpt-4-turbo"
        )
        
        counter.track_usage("test-tenant", stats)
        
        usage = counter.get_tenant_usage("test-tenant")
        
        assert usage is not None
        assert usage.total_tokens == 150
        assert usage.request_count == 1
    
    def test_budget_enforcement(self, counter):
        """Test budget enforcement."""
        counter.set_budget_limit("test-tenant", 0.01)  # Very low limit
        
        # Add usage that exceeds budget
        stats = UsageStats(
            prompt_tokens=100000,
            completion_tokens=50000,
            total_tokens=150000,
            model="gpt-4-turbo"
        )
        
        counter.track_usage("test-tenant", stats)
        
        # Should raise error on enforce
        with pytest.raises(ValueError, match="Budget limit exceeded"):
            counter.enforce_budget("test-tenant")


class TestPromptBuilder:
    """Test prompt builder."""
    
    @pytest.fixture
    def builder(self):
        """Create prompt builder."""
        return PromptBuilder()
    
    def test_variable_substitution(self, builder):
        """Test variable substitution."""
        template = "Hello {{name}}, your email is {email}"
        variables = {"name": "John", "email": "john@example.com"}
        
        result = builder._substitute_variables(template, variables)
        
        assert "John" in result
        assert "john@example.com" in result
    
    def test_token_estimation(self, builder):
        """Test token estimation."""
        text = "This is a test message with some content"
        
        tokens = builder.estimate_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_context_window_truncation(self, builder):
        """Test context window truncation."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
        ]
        
        truncated = builder.truncate_to_context_window(
            messages,
            max_tokens=100,
            preserve_recent=2
        )
        
        # Should keep system message and recent messages
        assert len(truncated) >= 3
        assert truncated[0]["role"] == "system"
        assert truncated[-1]["role"] == "user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])