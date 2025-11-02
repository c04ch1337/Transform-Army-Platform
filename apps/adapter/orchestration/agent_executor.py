"""Agent executor for running individual agent steps."""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional, List, Dict
from uuid import UUID

from ..core.logging import get_logger
from ..core.exceptions import AdapterException
from ..llm.client import LLMClient, LLMConfig
from ..llm.providers.base import Message
from ..llm.tools import ToolRegistry, ToolCall, get_tool_registry
from ..llm.prompt_builder import PromptBuilder

logger = get_logger(__name__)


class AgentTimeoutError(AdapterException):
    """Raised when agent execution times out."""
    
    def __init__(self, agent_id: str, timeout: int):
        super().__init__(
            message=f"Agent {agent_id} timed out after {timeout} seconds"
        )
        self.agent_id = agent_id
        self.timeout = timeout


class AgentExecutionError(AdapterException):
    """Raised when agent execution fails."""
    
    def __init__(self, agent_id: str, error: str):
        super().__init__(
            message=f"Agent {agent_id} execution failed: {error}"
        )
        self.agent_id = agent_id
        self.original_error = error


class AgentExecutor:
    """Executes individual agent steps within workflows.
    
    This class handles the execution of agent steps, including:
    - Calling LLM with agent configuration
    - Handling tool calling
    - Timeout management
    - Error handling and retries
    - Returning structured results
    
    Attributes:
        default_timeout: Default timeout in seconds for agent execution
        max_retries: Maximum number of retries for failed executions
        max_tool_iterations: Maximum tool calling iterations
    """
    
    def __init__(
        self,
        default_timeout: int = 300,
        max_retries: int = 3,
        max_tool_iterations: int = 10,
        llm_config: Optional[LLMConfig] = None
    ):
        """Initialize agent executor.
        
        Args:
            default_timeout: Default timeout in seconds
            max_retries: Maximum number of retries
            max_tool_iterations: Maximum tool calling iterations
            llm_config: LLM client configuration
        """
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.max_tool_iterations = max_tool_iterations
        
       # Initialize LLM client and tools
        self.llm_client = LLMClient(llm_config)
        self.tool_registry = get_tool_registry()
        self.prompt_builder = PromptBuilder()
        
        logger.info(
            f"Initialized AgentExecutor with timeout={default_timeout}s, "
            f"max_retries={max_retries}, max_tool_iterations={max_tool_iterations}"
        )
    
    async def execute(
        self,
        agent_config: dict[str, Any],
        input_data: dict[str, Any],
        timeout: Optional[int] = None
    ) -> dict[str, Any]:
        """Execute an agent step with the given configuration and input.
        
        Args:
            agent_config: Agent configuration including ID, model, tools, etc.
            input_data: Input data for the agent
            timeout: Execution timeout in seconds (uses default if not provided)
            
        Returns:
            Dictionary containing agent execution results
            
        Raises:
            AgentTimeoutError: If execution times out
            AgentExecutionError: If execution fails
        """
        agent_id = agent_config.get("agent_id", "unknown")
        timeout = timeout or self.default_timeout
        
        logger.info(
            f"Starting agent execution: {agent_id}",
            extra={"agent_id": agent_id, "timeout": timeout}
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_agent(agent_config, input_data),
                timeout=timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Agent execution completed: {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Agent execution timed out: {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "timeout": timeout,
                    "execution_time": execution_time
                }
            )
            raise AgentTimeoutError(agent_id, timeout)
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Agent execution failed: {agent_id}",
                exc_info=e,
                extra={
                    "agent_id": agent_id,
                    "execution_time": execution_time,
                    "error": str(e)
                }
            )
            raise AgentExecutionError(agent_id, str(e))
    
    async def _execute_agent(
        self,
        agent_config: dict[str, Any],
        input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Internal method to execute agent logic with real LLM calls.
        
        This method:
        1. Builds system prompt from agent configuration
        2. Calls LLM with input data and available tools
        3. Handles tool calls iteratively (up to max_tool_iterations)
        4. Returns structured results with token usage
        
        Args:
            agent_config: Agent configuration
            input_data: Input data
            
        Returns:
            Execution results
        """
        agent_id = agent_config.get("agent_id", "unknown")
        agent_type = agent_config.get("agent_type", "generic")
        tenant_id = input_data.get("tenant_id")
        
        logger.debug(
            f"Executing agent {agent_id} of type {agent_type} with LLM",
            extra={"agent_id": agent_id, "agent_type": agent_type}
        )
        
        # Initialize LLM client if needed
        if not self.llm_client._initialized:
            await self.llm_client.initialize()
        
        # Build system prompt
        system_prompt = self.prompt_builder.build_system_message(
            agent_type=agent_type,
            additional_context=agent_config.get("additional_context")
        )
        
        # Build user message
        user_message = self.prompt_builder.build_user_message(
            agent_type=agent_type,
            variables=input_data
        )
        
        # Get available tools for this agent
        tool_names = agent_config.get("tools", [])
        tools_schemas = None
        if tool_names:
            tools_schemas = self.tool_registry.get_schemas(
                provider=self.llm_client.config.provider,
                tool_names=tool_names
            )
        
        # Initialize conversation
        messages: List[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message)
        ]
        
        # Tool calling loop
        tool_calls_made = []
        total_tokens = 0
        iteration = 0
        
        while iteration < self.max_tool_iterations:
            iteration += 1
            
            logger.debug(
                f"Agent iteration {iteration}/{self.max_tool_iterations}",
                extra={"agent_id": agent_id}
            )
            
            # Call LLM
            try:
                response = await self.llm_client.chat(
                    messages=messages,
                    tools=tools_schemas,
                    temperature=agent_config.get("temperature"),
                    max_tokens=agent_config.get("max_tokens"),
                    tenant_id=tenant_id
                )
                
                total_tokens += response.usage.total_tokens
                
                # Add assistant response to conversation
                messages.append(
                    Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls
                    )
                )
                
                # Check if there are tool calls
                if not response.tool_calls:
                    # No tool calls, we're done
                    logger.info(
                        f"Agent completed without tool calls",
                        extra={
                            "agent_id": agent_id,
                            "iterations": iteration,
                            "total_tokens": total_tokens
                        }
                    )
                    
                    return {
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "status": "completed",
                        "output": {
                            "message": response.content,
                            "data": input_data,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "tool_calls": tool_calls_made,
                        "tokens_used": total_tokens,
                        "model": response.model,
                        "cost_usd": response.cost_usd,
                        "iterations": iteration,
                        "finish_reason": response.finish_reason
                    }
                
                # Execute tool calls
                logger.debug(
                    f"Executing {len(response.tool_calls)} tool calls",
                    extra={"agent_id": agent_id}
                )
                
                for tool_call_data in response.tool_calls:
                    # Parse tool call
                    provider = await self.llm_client._get_provider(
                        self.llm_client.config.provider
                    )
                    parsed_call = provider.parse_tool_call(tool_call_data)
                    
                    # Create tool call
                    tool_call = ToolCall(
                        id=parsed_call["id"],
                        name=parsed_call["name"],
                        arguments=parsed_call["arguments"]
                    )
                    
                    # Execute tool
                    tool_result = await self.tool_registry.execute(
                        tool_call,
                        context={"tenant_id": tenant_id}
                    )
                    
                    # Track tool call
                    tool_calls_made.append({
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                        "result": tool_result.result,
                        "success": tool_result.success,
                        "error": tool_result.error
                    })
                    
                    # Add tool result to conversation
                    messages.append(
                        Message(
                            role="tool",
                            content=tool_result.to_message_content(),
                            tool_call_id=tool_call.id,
                            name=tool_call.name
                        )
                    )
                    
                    logger.debug(
                        f"Tool executed: {tool_call.name}",
                        extra={
                            "agent_id": agent_id,
                            "success": tool_result.success,
                            "execution_time_ms": tool_result.execution_time_ms
                        }
                    )
                
                # Check finish reason
                if response.finish_reason == "length":
                    logger.warning(
                        f"Agent hit token limit",
                        extra={"agent_id": agent_id, "tokens": total_tokens}
                    )
                    break
                
            except Exception as e:
                logger.error(
                    f"LLM call failed during agent execution: {e}",
                    exc_info=e,
                    extra={"agent_id": agent_id, "iteration": iteration}
                )
                raise
        
        # If we get here, we hit max iterations
        logger.warning(
            f"Agent hit max tool iterations",
            extra={
                "agent_id": agent_id,
                "max_iterations": self.max_tool_iterations,
                "tool_calls": len(tool_calls_made)
            }
        )
        
        # Return final result
        final_message = messages[-1].content if messages else "Max iterations reached"
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "status": "completed",
            "output": {
                "message": final_message,
                "data": input_data,
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "Max tool iterations reached"
            },
            "tool_calls": tool_calls_made,
            "tokens_used": total_tokens,
            "model": agent_config.get("model", self.llm_client.config.model),
            "iterations": iteration,
            "finish_reason": "max_iterations"
        }
    
    async def execute_with_retry(
        self,
        agent_config: dict[str, Any],
        input_data: dict[str, Any],
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> dict[str, Any]:
        """Execute agent with automatic retry on failure.
        
        Args:
            agent_config: Agent configuration
            input_data: Input data
            timeout: Execution timeout in seconds
            max_retries: Maximum number of retries (uses default if not provided)
            
        Returns:
            Execution results
            
        Raises:
            AgentTimeoutError: If execution times out
            AgentExecutionError: If all retries fail
        """
        agent_id = agent_config.get("agent_id", "unknown")
        max_retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Agent execution attempt {attempt + 1}/{max_retries}: {agent_id}",
                    extra={"agent_id": agent_id, "attempt": attempt + 1}
                )
                
                result = await self.execute(agent_config, input_data, timeout)
                
                if attempt > 0:
                    logger.info(
                        f"Agent execution succeeded after {attempt + 1} attempts: {agent_id}",
                        extra={"agent_id": agent_id, "attempts": attempt + 1}
                    )
                
                return result
                
            except AgentTimeoutError:
                # Don't retry on timeout
                raise
                
            except AgentExecutionError as e:
                last_error = e
                
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Agent execution failed, retrying in {wait_time}s: {agent_id}",
                        extra={
                            "agent_id": agent_id,
                            "attempt": attempt + 1,
                            "wait_time": wait_time,
                            "error": str(e)
                        }
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Agent execution failed after {max_retries} attempts: {agent_id}",
                        extra={"agent_id": agent_id, "attempts": max_retries}
                    )
        
        # All retries failed
        if last_error:
            raise last_error
        else:
            raise AgentExecutionError(agent_id, "All retry attempts failed")
    
    def validate_agent_config(self, agent_config: dict[str, Any]) -> bool:
        """Validate agent configuration.
        
        Args:
            agent_config: Agent configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ["agent_id", "agent_type"]
        
        for field in required_fields:
            if field not in agent_config:
                raise ValueError(f"Agent configuration missing required field: {field}")
        
        # Validate agent_type
        valid_types = [
            "bdr_concierge",
            "support_concierge",
            "research_recon",
            "ops_sapper",
            "knowledge_librarian",
            "qa_auditor",
            "custom"
        ]
        
        agent_type = agent_config["agent_type"]
        if agent_type not in valid_types:
            logger.warning(
                f"Unknown agent type: {agent_type}",
                extra={"agent_type": agent_type}
            )
        
        logger.debug(
            f"Validated agent configuration: {agent_config['agent_id']}",
            extra={"agent_id": agent_config["agent_id"]}
        )
        
        return True
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Call a tool with the given parameters.
        
        This is a placeholder for tool calling functionality.
        In a full implementation, this would:
        1. Look up the tool by name
        2. Validate parameters
        3. Execute the tool
        4. Return results
        
        Args:
            tool_name: Name of the tool to call
            tool_parameters: Tool parameters
            
        Returns:
            Tool execution results
        """
        logger.debug(
            f"Calling tool: {tool_name}",
            extra={"tool_name": tool_name, "parameters": tool_parameters}
        )
        
        # Placeholder implementation
        # In the real version, this integrates with the provider system
        result = {
            "tool": tool_name,
            "parameters": tool_parameters,
            "result": f"Tool {tool_name} executed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result