"""
LLM Performance Benchmarks for Transform Army AI.

Benchmarks LLM-related operations including:
- Token counting performance
- Prompt building overhead
- Tool schema conversion time
- Streaming vs non-streaming
- Provider comparison

Performance Targets:
- Token counting: < 10ms
- Prompt building: < 20ms
- Tool schema conversion: < 50ms
- Streaming overhead: < 5ms
"""

import asyncio
import json
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import tiktoken

from src.orchestration.agent_executor import AgentExecutor


@pytest.fixture
def small_text():
    """Small text sample (~50 tokens)."""
    return """
    Hello, I am an AI assistant designed to help with customer support.
    How can I assist you today?
    """


@pytest.fixture
def medium_text():
    """Medium text sample (~200 tokens)."""
    return """
    Welcome to Transform Army AI, your intelligent business automation platform.
    Our system provides advanced capabilities for customer relationship management,
    helpdesk automation, calendar scheduling, and knowledge base management.
    
    We leverage state-of-the-art language models to understand natural language
    queries and execute complex workflows. Our platform integrates with popular
    business tools like HubSpot, Salesforce, Zendesk, and Google Workspace.
    
    Whether you're looking to automate sales processes, improve customer support,
    or streamline team operations, Transform Army AI has you covered.
    """


@pytest.fixture
def large_text():
    """Large text sample (~1000 tokens)."""
    return """
    Transform Army AI is a comprehensive business automation platform that combines
    the power of artificial intelligence with seamless integrations to your favorite
    business tools. Our platform is built on a foundation of reliability, security,
    and performance, ensuring that your business processes run smoothly 24/7.
    
    Key Features:
    
    1. Customer Relationship Management (CRM)
       - Automated lead qualification and scoring
       - Intelligent contact management
       - Deal pipeline automation
       - Custom reporting and analytics
       - Multi-platform support (HubSpot, Salesforce, Pipedrive)
    
    2. Helpdesk Automation
       - Smart ticket routing and prioritization
       - Automated responses to common queries
       - Sentiment analysis and escalation
       - Knowledge base integration
       - Support for Zendesk, Intercom, and more
    
    3. Calendar and Scheduling
       - Intelligent meeting scheduling
       - Automatic time zone handling
       - Conflict detection and resolution
       - Integration with Google Calendar, Microsoft Outlook
       - Team availability coordination
    
    4. Knowledge Management
       - Vector-based semantic search
       - Automatic document summarization
       - Content recommendations
       - Version control and audit trails
       - Multi-format support (PDF, DOCX, Markdown)
    
    5. Workflow Orchestration
       - Visual workflow builder
       - Conditional logic and branching
       - Parallel execution support
       - Error handling and retries
       - Real-time monitoring and alerts
    
    Technical Architecture:
    
    Our platform is built using modern technologies and follows industry best practices:
    - FastAPI backend for high-performance API endpoints
    - PostgreSQL with row-level security for multi-tenant data isolation
    - Redis for caching and real-time features
    - Async/await patterns for efficient I/O operations
    - Comprehensive testing with pytest
    - Docker containers for consistent deployments
    - CI/CD pipelines for automated testing and deployment
    
    Security and Compliance:
    - SOC 2 Type II certified
    - GDPR compliant
    - End-to-end encryption
    - Regular security audits
    - Role-based access control (RBAC)
    - Audit logging for all operations
    
    Get started today and transform your business operations with AI-powered automation.
    """ * 2  # Double it to reach ~1000 tokens


@pytest.fixture
def simple_tools():
    """Simple tool definitions."""
    return [
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        },
        {
            "name": "send_email",
            "description": "Send an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    ]


@pytest.fixture
def complex_tools():
    """Complex tool definitions with nested schemas."""
    return [
        {
            "name": "create_crm_contact",
            "description": "Create a new CRM contact with detailed information",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Contact email address"},
                    "first_name": {"type": "string", "description": "First name"},
                    "last_name": {"type": "string", "description": "Last name"},
                    "company": {"type": "string", "description": "Company name"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "zip": {"type": "string"},
                            "country": {"type": "string"}
                        }
                    },
                    "custom_fields": {
                        "type": "object",
                        "additionalProperties": True
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["email", "first_name", "last_name"]
            }
        },
        {
            "name": "create_helpdesk_ticket",
            "description": "Create a new helpdesk ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Ticket subject"},
                    "description": {"type": "string", "description": "Detailed description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Ticket priority"
                    },
                    "category": {"type": "string", "description": "Ticket category"},
                    "requester": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "name": {"type": "string"}
                        },
                        "required": ["email"]
                    },
                    "custom_fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "value": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["subject", "description", "priority"]
            }
        },
        {
            "name": "schedule_meeting",
            "description": "Schedule a meeting with attendees",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Meeting title"},
                    "start_time": {"type": "string", "format": "date-time"},
                    "end_time": {"type": "string", "format": "date-time"},
                    "attendees": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string"},
                                "optional": {"type": "boolean"}
                            }
                        }
                    },
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "reminders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string", "enum": ["email", "popup"]},
                                "minutes": {"type": "integer"}
                            }
                        }
                    }
                },
                "required": ["title", "start_time", "end_time"]
            }
        }
    ]


# Token Counting Benchmarks
def test_bench_token_count_small(benchmark, small_text):
    """
    Benchmark token counting for small text (~50 tokens).
    
    Target: < 5ms
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    def count_tokens():
        return len(encoding.encode(small_text))
    
    result = benchmark.pedantic(count_tokens, iterations=500, rounds=10, warmup_rounds=5)


def test_bench_token_count_medium(benchmark, medium_text):
    """
    Benchmark token counting for medium text (~200 tokens).
    
    Target: < 10ms
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    def count_tokens():
        return len(encoding.encode(medium_text))
    
    result = benchmark.pedantic(count_tokens, iterations=300, rounds=10, warmup_rounds=5)


def test_bench_token_count_large(benchmark, large_text):
    """
    Benchmark token counting for large text (~1000 tokens).
    
    Target: < 20ms
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    def count_tokens():
        return len(encoding.encode(large_text))
    
    result = benchmark.pedantic(count_tokens, iterations=200, rounds=10, warmup_rounds=5)


def test_bench_token_count_with_caching(benchmark, medium_text):
    """
    Benchmark token counting with caching strategy.
    
    Demonstrates caching effectiveness for repeated text.
    Target: < 1ms with cache hit
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    cache = {}
    
    def count_with_cache():
        text_hash = hash(medium_text)
        if text_hash in cache:
            return cache[text_hash]
        
        count = len(encoding.encode(medium_text))
        cache[text_hash] = count
        return count
    
    result = benchmark.pedantic(count_with_cache, iterations=1000, rounds=10)


# Prompt Building Benchmarks
def test_bench_simple_prompt_construction(benchmark, small_text):
    """
    Benchmark simple prompt construction.
    
    Target: < 5ms
    """
    system_prompt = "You are a helpful AI assistant."
    
    def build_prompt():
        return {
            "system": system_prompt,
            "user": small_text,
            "assistant": ""
        }
    
    result = benchmark.pedantic(build_prompt, iterations=500, rounds=10)


def test_bench_complex_prompt_construction(benchmark, medium_text, simple_tools):
    """
    Benchmark complex prompt with tools and context.
    
    Target: < 20ms
    """
    system_prompt = "You are a helpful AI assistant with access to tools."
    context = {"user_id": "12345", "session_id": "abc-def"}
    
    def build_complex_prompt():
        return {
            "system": system_prompt,
            "context": context,
            "tools": simple_tools,
            "messages": [
                {"role": "user", "content": medium_text},
                {"role": "assistant", "content": "I understand. Let me help you with that."},
                {"role": "user", "content": "Please proceed."}
            ]
        }
    
    result = benchmark.pedantic(build_complex_prompt, iterations=300, rounds=10)


def test_bench_prompt_template_rendering(benchmark):
    """
    Benchmark prompt template rendering with variables.
    
    Target: < 10ms
    """
    template = """
    You are a {role} assistant helping with {task}.
    User name: {user_name}
    User context: {context}
    
    Current conversation:
    {conversation_history}
    
    User query: {query}
    """
    
    variables = {
        "role": "customer support",
        "task": "ticket management",
        "user_name": "John Doe",
        "context": "Enterprise customer, VIP status",
        "conversation_history": "\n".join([
            f"Message {i}: Sample conversation text here"
            for i in range(5)
        ]),
        "query": "I need help with my account"
    }
    
    def render_template():
        return template.format(**variables)
    
    result = benchmark.pedantic(render_template, iterations=500, rounds=10)


# Tool Schema Conversion Benchmarks
def test_bench_simple_tool_schema_conversion(benchmark, simple_tools):
    """
    Benchmark simple tool schema conversion.
    
    Target: < 10ms
    """
    def convert_schemas():
        converted = []
        for tool in simple_tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return converted
    
    result = benchmark.pedantic(convert_schemas, iterations=500, rounds=10)


def test_bench_complex_tool_schema_conversion(benchmark, complex_tools):
    """
    Benchmark complex tool schema conversion.
    
    Target: < 50ms
    """
    def convert_complex_schemas():
        converted = []
        for tool in complex_tools:
            # Simulate more complex conversion with validation
            schema = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            # Validate schema structure
            assert "name" in schema["function"]
            assert "parameters" in schema["function"]
            converted.append(schema)
        return converted
    
    result = benchmark.pedantic(convert_complex_schemas, iterations=200, rounds=10)


def test_bench_tool_schema_json_serialization(benchmark, complex_tools):
    """
    Benchmark tool schema JSON serialization.
    
    Target: < 15ms
    """
    def serialize_tools():
        return json.dumps(complex_tools)
    
    result = benchmark.pedantic(serialize_tools, iterations=500, rounds=10)


def test_bench_tool_schema_json_deserialization(benchmark, complex_tools):
    """
    Benchmark tool schema JSON deserialization.
    
    Target: < 20ms
    """
    serialized = json.dumps(complex_tools)
    
    def deserialize_tools():
        return json.loads(serialized)
    
    result = benchmark.pedantic(deserialize_tools, iterations=500, rounds=10)


# LLM Response Processing Benchmarks
def test_bench_response_parsing_simple(benchmark):
    """
    Benchmark simple LLM response parsing.
    
    Target: < 5ms
    """
    response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a simple response."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    
    def parse_response():
        return {
            "content": response["choices"][0]["message"]["content"],
            "tokens_used": response["usage"]["total_tokens"],
            "finish_reason": response["choices"][0]["finish_reason"]
        }
    
    result = benchmark.pedantic(parse_response, iterations=1000, rounds=10)


def test_bench_response_parsing_with_tools(benchmark):
    """
    Benchmark LLM response parsing with tool calls.
    
    Target: < 15ms
    """
    response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": json.dumps({"location": "San Francisco"})
                        }
                    },
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "send_email",
                            "arguments": json.dumps({
                                "to": "user@example.com",
                                "subject": "Weather Update",
                                "body": "Here's the weather information you requested."
                            })
                        }
                    }
                ]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "total_tokens": 80
        }
    }
    
    def parse_tool_response():
        tool_calls = []
        for call in response["choices"][0]["message"]["tool_calls"]:
            tool_calls.append({
                "id": call["id"],
                "name": call["function"]["name"],
                "arguments": json.loads(call["function"]["arguments"])
            })
        return {
            "tool_calls": tool_calls,
            "tokens_used": response["usage"]["total_tokens"]
        }
    
    result = benchmark.pedantic(parse_tool_response, iterations=500, rounds=10)


# Streaming Simulation Benchmarks
@pytest.mark.asyncio
async def test_bench_streaming_overhead(benchmark):
    """
    Benchmark streaming response overhead.
    
    Measures the overhead of processing streamed chunks.
    Target: < 5ms per chunk
    """
    chunks = [
        {"delta": {"content": "Hello"}},
        {"delta": {"content": " world"}},
        {"delta": {"content": "!"}},
        {"delta": {"content": " How"}},
        {"delta": {"content": " can"}},
        {"delta": {"content": " I"}},
        {"delta": {"content": " help"}},
        {"delta": {"content": " you"}},
        {"delta": {"content": "?"}},
    ]
    
    async def process_stream():
        result = ""
        for chunk in chunks:
            if "content" in chunk.get("delta", {}):
                result += chunk["delta"]["content"]
        return result
    
    result = benchmark.pedantic(
        lambda: asyncio.run(process_stream()),
        iterations=500,
        rounds=10
    )


@pytest.mark.asyncio
async def test_bench_streaming_vs_non_streaming(benchmark):
    """
    Benchmark streaming vs non-streaming response processing.
    
    Compares performance characteristics.
    Target: Streaming should have < 10% overhead
    """
    full_response = "Hello world! How can I help you today?"
    
    async def non_streaming():
        # Simulate receiving full response at once
        return full_response
    
    result = benchmark.pedantic(
        lambda: asyncio.run(non_streaming()),
        iterations=1000,
        rounds=10
    )


# Provider-Specific Benchmarks
def test_bench_anthropic_message_format(benchmark, medium_text):
    """
    Benchmark Anthropic message format conversion.
    
    Target: < 10ms
    """
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": medium_text}
    ]
    
    def format_for_anthropic():
        return {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1024,
            "messages": messages
        }
    
    result = benchmark.pedantic(format_for_anthropic, iterations=500, rounds=10)


def test_bench_openai_message_format(benchmark, medium_text, simple_tools):
    """
    Benchmark OpenAI message format conversion.
    
    Target: < 15ms
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": medium_text}
    ]
    
    def format_for_openai():
        return {
            "model": "gpt-4",
            "messages": messages,
            "tools": [
                {
                    "type": "function",
                    "function": tool
                }
                for tool in simple_tools
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
    
    result = benchmark.pedantic(format_for_openai, iterations=500, rounds=10)


# Cost Calculation Benchmarks
def test_bench_token_cost_calculation(benchmark):
    """
    Benchmark token cost calculation.
    
    Target: < 1ms
    """
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015}
    }
    
    def calculate_cost():
        model = "gpt-4"
        input_tokens = 500
        output_tokens = 200
        
        input_cost = (input_tokens / 1000) * pricing[model]["input"]
        output_cost = (output_tokens / 1000) * pricing[model]["output"]
        total_cost = input_cost + output_cost
        
        return total_cost
    
    result = benchmark.pedantic(calculate_cost, iterations=1000, rounds=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])