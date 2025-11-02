"""Tool registry for LLM function calling."""

import json
from typing import Any, Callable, Dict, List, Optional, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """Tool definition for LLM function calling."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    category: str = "general"
    requires_auth: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_schema(self, provider: str = "openai") -> Dict[str, Any]:
        """Convert tool to LLM provider schema.
        
        Args:
            provider: Target provider (openai, anthropic, etc.)
            
        Returns:
            Provider-specific tool schema
        """
        if provider == "openai":
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters,
                }
            }
        elif provider == "anthropic":
            return {
                "name": self.name,
                "description": self.description,
                "input_schema": self.parameters,
            }
        else:
            # Generic format
            return {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }


@dataclass
class ToolCall:
    """Representation of a tool call request."""
    
    id: str
    name: str
    arguments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ToolResult:
    """Result from tool execution."""
    
    tool_call_id: str
    name: str
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_message_content(self) -> str:
        """Convert result to message content for LLM."""
        if self.success:
            if isinstance(self.result, (dict, list)):
                return json.dumps(self.result, indent=2)
            return str(self.result)
        else:
            return f"Error: {self.error}"


class ToolRegistry:
    """Registry for managing agent tools.
    
    The tool registry maintains a collection of available tools that
    agents can use during execution. It handles tool discovery,
    validation, execution, and result formatting.
    """
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.info("Initialized ToolRegistry")
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Awaitable[Any]],
        category: str = "general",
        requires_auth: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tool:
        """Register a new tool.
        
        Args:
            name: Tool name (must be unique)
            description: Description of what the tool does
            parameters: JSON schema of tool parameters
            handler: Async function to execute the tool
            category: Tool category (crm, email, calendar, etc.)
            requires_auth: Whether tool requires authentication
            metadata: Additional metadata
            
        Returns:
            Registered tool
            
        Raises:
            ValueError: If tool name already exists
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            category=category,
            requires_auth=requires_auth,
            metadata=metadata or {}
        )
        
        self._tools[name] = tool
        
        # Add to category index
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)
        
        logger.info(
            f"Registered tool: {name}",
            extra={"category": category, "requires_auth": requires_auth}
        )
        
        return tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool.
        
        Args:
            name: Tool name to remove
        """
        if name not in self._tools:
            logger.warning(f"Tool '{name}' not found for unregistration")
            return
        
        tool = self._tools[name]
        
        # Remove from category index
        if tool.category in self._categories:
            self._categories[tool.category].remove(name)
        
        del self._tools[name]
        
        logger.info(f"Unregistered tool: {name}")
    
    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        requires_auth: Optional[bool] = None
    ) -> List[Tool]:
        """List available tools.
        
        Args:
            category: Filter by category
            requires_auth: Filter by auth requirement
            
        Returns:
            List of tools matching filters
        """
        tools = list(self._tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if requires_auth is not None:
            tools = [t for t in tools if t.requires_auth == requires_auth]
        
        return tools
    
    def get_schemas(
        self,
        provider: str = "openai",
        category: Optional[str] = None,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get tool schemas for LLM provider.
        
        Args:
            provider: Target provider (openai, anthropic, etc.)
            category: Filter by category
            tool_names: Specific tools to include (if None, includes all)
            
        Returns:
            List of tool schemas
        """
        tools = self.list_tools(category=category)
        
        # Filter by specific names if provided
        if tool_names:
            tools = [t for t in tools if t.name in tool_names]
        
        return [tool.to_schema(provider) for tool in tools]
    
    async def execute(
        self,
        tool_call: ToolCall,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a tool call.
        
        Args:
            tool_call: Tool call to execute
            context: Execution context (tenant_id, user_id, etc.)
            
        Returns:
            Tool execution result
        """
        start_time = datetime.utcnow()
        
        tool = self.get(tool_call.name)
        if not tool:
            logger.error(f"Tool not found: {tool_call.name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                result=None,
                success=False,
                error=f"Tool '{tool_call.name}' not found"
            )
        
        try:
            logger.debug(
                f"Executing tool: {tool_call.name}",
                extra={"arguments": tool_call.arguments}
            )
            
            # Execute tool handler
            if context:
                result = await tool.handler(**tool_call.arguments, **context)
            else:
                result = await tool.handler(**tool_call.arguments)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"Tool execution successful: {tool_call.name}",
                extra={
                    "execution_time_ms": execution_time,
                    "tool_call_id": tool_call.id
                }
            )
            
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                result=result,
                success=True,
                execution_time_ms=int(execution_time)
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                f"Tool execution failed: {tool_call.name}",
                exc_info=e,
                extra={
                    "tool_call_id": tool_call.id,
                    "error": str(e),
                    "execution_time_ms": execution_time
                }
            )
            
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                result=None,
                success=False,
                error=str(e),
                execution_time_ms=int(execution_time)
            )
    
    async def execute_batch(
        self,
        tool_calls: List[ToolCall],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ToolResult]:
        """Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool calls to execute
            context: Execution context
            
        Returns:
            List of tool results in same order
        """
        import asyncio
        
        tasks = [
            self.execute(tool_call, context)
            for tool_call in tool_calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Tool batch execution failed for call {i}",
                    exc_info=result
                )
                processed_results.append(
                    ToolResult(
                        tool_call_id=tool_calls[i].id,
                        name=tool_calls[i].name,
                        result=None,
                        success=False,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_categories(self) -> List[str]:
        """Get list of all tool categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_tool_count(self, category: Optional[str] = None) -> int:
        """Get count of registered tools.
        
        Args:
            category: Optional category to count
            
        Returns:
            Number of tools
        """
        if category:
            return len(self._categories.get(category, []))
        return len(self._tools)
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        logger.info("Cleared all tools from registry")


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance.
    
    Returns:
        Global tool registry
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ToolRegistry()
    
    return _global_registry


def register_provider_tools(registry: ToolRegistry) -> None:
    """Register standard provider tools.
    
    This function registers tools for CRM, helpdesk, email, calendar,
    and knowledge operations that agents can use.
    
    Args:
        registry: Tool registry to register tools in
    """
    # CRM Tools
    from ..providers.crm import get_crm_provider
    
    async def crm_search_contacts(**kwargs):
        """Search CRM contacts."""
        provider = await get_crm_provider(kwargs.get("tenant_id"))
        return await provider.search_contacts(**kwargs)
    
    registry.register(
        name="crm_search_contacts",
        description="Search for contacts in CRM by email, name, or company",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (email, name, or company)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        },
        handler=crm_search_contacts,
        category="crm"
    )
    
    # Add more tools as needed
    logger.info("Registered standard provider tools")