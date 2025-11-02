"""Prompt builder for constructing agent prompts."""

import os
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template with variable substitution."""
    
    name: str
    system_prompt: str
    user_template: Optional[str] = None
    variables: Dict[str, str] = None
    few_shot_examples: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize variables and examples."""
        if self.variables is None:
            self.variables = {}
        if self.few_shot_examples is None:
            self.few_shot_examples = []
        if self.metadata is None:
            self.metadata = {}


class PromptBuilder:
    """Builder for constructing agent prompts from templates.
    
    Handles:
    - Loading prompts from packages/prompt-pack
    - Variable substitution
    - Few-shot example injection
    - Context window management
    - System + user message construction
    """
    
    def __init__(self, prompt_pack_dir: Optional[str] = None):
        """Initialize prompt builder.
        
        Args:
            prompt_pack_dir: Path to prompt-pack directory
        """
        if prompt_pack_dir:
            self.prompt_pack_dir = Path(prompt_pack_dir)
        else:
            # Default to packages/prompt-pack relative to project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent
            self.prompt_pack_dir = project_root / "packages" / "prompt-pack"
        
        self._templates: Dict[str, PromptTemplate] = {}
        self._system_prompts: Dict[str, str] = {}
        
        logger.info(f"Initialized PromptBuilder with dir: {self.prompt_pack_dir}")
    
    def load_template(self, agent_type: str) -> Optional[PromptTemplate]:
        """Load prompt template for agent type.
        
        Args:
            agent_type: Agent type (bdr_concierge, support_concierge, etc.)
            
        Returns:
            Loaded template or None if not found
        """
        if agent_type in self._templates:
            return self._templates[agent_type]
        
        # Try to load from templates directory
        template_file = self.prompt_pack_dir / "templates" / f"{agent_type.replace('_', '-')}-template.md"
        
        if not template_file.exists():
            logger.warning(f"Template not found for agent: {agent_type}")
            return None
        
        try:
            content = template_file.read_text(encoding="utf-8")
            
            # Parse template (assuming markdown format with sections)
            system_prompt = self._extract_section(content, "System Prompt", "User Template")
            user_template = self._extract_section(content, "User Template", "Examples")
            
            template = PromptTemplate(
                name=agent_type,
                system_prompt=system_prompt,
                user_template=user_template,
                metadata={"source": str(template_file)}
            )
            
            self._templates[agent_type] = template
            
            logger.info(f"Loaded template for agent: {agent_type}")
            
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template for {agent_type}: {e}", exc_info=e)
            return None
    
    def load_system_prompt(self, name: str) -> Optional[str]:
        """Load a system prompt from files.
        
        Args:
            name: System prompt name (escalation-protocol, tool-usage-guidelines, etc.)
            
        Returns:
            Prompt content or None if not found
        """
        if name in self._system_prompts:
            return self._system_prompts[name]
        
        prompt_file = self.prompt_pack_dir / "system" / f"{name}.md"
        
        if not prompt_file.exists():
            logger.warning(f"System prompt not found: {name}")
            return None
        
        try:
            content = prompt_file.read_text(encoding="utf-8")
            self._system_prompts[name] = content
            
            logger.debug(f"Loaded system prompt: {name}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to load system prompt {name}: {e}", exc_info=e)
            return None
    
    def build_system_message(
        self,
        agent_type: str,
        additional_context: Optional[str] = None,
        include_guidelines: bool = True
    ) -> str:
        """Build system message for agent.
        
        Args:
            agent_type: Agent type
            additional_context: Additional context to include
            include_guidelines: Whether to include tool usage guidelines
            
        Returns:
            Complete system message
        """
        template = self.load_template(agent_type)
        
        if not template:
            # Fallback to basic template
            return self._get_fallback_system_prompt(agent_type)
        
        parts = [template.system_prompt]
        
        # Add tool usage guidelines
        if include_guidelines:
            guidelines = self.load_system_prompt("tool-usage-guidelines")
            if guidelines:
                parts.append("\n\n## Tool Usage Guidelines\n\n" + guidelines)
        
        # Add escalation protocol
        escalation = self.load_system_prompt("escalation-protocol")
        if escalation:
            parts.append("\n\n## Escalation Protocol\n\n" + escalation)
        
        # Add additional context
        if additional_context:
            parts.append("\n\n## Additional Context\n\n" + additional_context)
        
        return "\n".join(parts)
    
    def build_user_message(
        self,
        agent_type: str,
        variables: Dict[str, Any],
        include_examples: bool = False
    ) -> str:
        """Build user message with variable substitution.
        
        Args:
            agent_type: Agent type
            variables: Variables to substitute
            include_examples: Whether to include few-shot examples
            
        Returns:
            Complete user message
        """
        template = self.load_template(agent_type)
        
        if not template or not template.user_template:
            # Fallback to simple variable dump
            return self._format_variables(variables)
        
        # Substitute variables
        message = self._substitute_variables(template.user_template, variables)
        
        # Add few-shot examples
        if include_examples and template.few_shot_examples:
            examples_text = self._format_examples(template.few_shot_examples)
            message = f"{examples_text}\n\n{message}"
        
        return message
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Uses rough approximation: ~4 characters per token.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def truncate_to_context_window(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        preserve_recent: int = 3
    ) -> List[Dict[str, str]]:
        """Truncate messages to fit context window.
        
        Args:
            messages: List of messages
            max_tokens: Maximum tokens allowed
            preserve_recent: Number of recent messages to always preserve
            
        Returns:
            Truncated message list
        """
        if len(messages) <= preserve_recent:
            return messages
        
        # Calculate tokens
        total_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        
        if total_tokens <= max_tokens:
            return messages
        
        # Keep system message (first) and recent messages
        result = [messages[0]]  # System message
        recent = messages[-preserve_recent:]
        
        # Try to fit older messages
        remaining_tokens = max_tokens - sum(
            self.estimate_tokens(m.get("content", "")) for m in [messages[0]] + recent
        )
        
        for msg in messages[1:-preserve_recent]:
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if msg_tokens <= remaining_tokens:
                result.append(msg)
                remaining_tokens -= msg_tokens
            else:
                break
        
        # Add recent messages
        result.extend(recent)
        
        logger.debug(
            f"Truncated messages from {len(messages)} to {len(result)} "
            f"(estimated {total_tokens} -> ~{max_tokens} tokens)"
        )
        
        return result
    
    def _extract_section(
        self,
        content: str,
        start_marker: str,
        end_marker: Optional[str] = None
    ) -> str:
        """Extract section from markdown content.
        
        Args:
            content: Full content
            start_marker: Section start marker
            end_marker: Section end marker (optional)
            
        Returns:
            Extracted section
        """
        # Find start
        start_pattern = f"#{1,3}\\s+{re.escape(start_marker)}"
        start_match = re.search(start_pattern, content, re.IGNORECASE)
        
        if not start_match:
            return ""
        
        start_pos = start_match.end()
        
        # Find end
        if end_marker:
            end_pattern = f"#{1,3}\\s+{re.escape(end_marker)}"
            end_match = re.search(end_pattern, content[start_pos:], re.IGNORECASE)
            
            if end_match:
                end_pos = start_pos + end_match.start()
                return content[start_pos:end_pos].strip()
        
        return content[start_pos:].strip()
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template.
        
        Supports: {{variable}}, {variable}, $variable
        
        Args:
            template: Template string
            variables: Variable values
            
        Returns:
            String with variables substituted
        """
        result = template
        
        for key, value in variables.items():
            # Convert value to string
            value_str = str(value) if value is not None else ""
            
            # Replace various formats
            result = result.replace(f"{{{{{key}}}}}", value_str)  # {{var}}
            result = result.replace(f"{{{key}}}", value_str)      # {var}
            result = result.replace(f"${key}", value_str)         # $var
        
        return result
    
    def _format_variables(self, variables: Dict[str, Any]) -> str:
        """Format variables as text.
        
        Args:
            variables: Variables to format
            
        Returns:
            Formatted text
        """
        lines = []
        for key, value in variables.items():
            lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format few-shot examples.
        
        Args:
            examples: List of example dicts with 'input' and 'output'
            
        Returns:
            Formatted examples
        """
        formatted = ["## Examples\n"]
        
        for i, example in enumerate(examples, 1):
            formatted.append(f"### Example {i}")
            formatted.append(f"**Input:** {example.get('input', '')}")
            formatted.append(f"**Output:** {example.get('output', '')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _get_fallback_system_prompt(self, agent_type: str) -> str:
        """Get fallback system prompt when template not found.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Basic system prompt
        """
        return f"""You are a helpful AI assistant configured as a {agent_type.replace('_', ' ')} agent.

Your responsibilities:
- Process user requests accurately and efficiently
- Use available tools to gather information and perform actions
- Provide clear, professional responses
- Ask for clarification when needed

Always maintain a professional, helpful tone."""

    def clear_cache(self) -> None:
        """Clear cached templates and prompts."""
        self._templates.clear()
        self._system_prompts.clear()
        logger.debug("Cleared prompt cache")