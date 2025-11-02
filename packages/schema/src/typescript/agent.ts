/**
 * Agent schema definitions for Transform Army AI platform.
 * 
 * This module defines Zod schemas for agent configuration, roles, state management,
 * and multi-agent workflow orchestration.
 */

import { z } from 'zod';

/**
 * Predefined agent roles in the system.
 */
export const AgentRoleSchema = z.enum([
  // Generic roles
  'orchestrator',
  'researcher',
  'analyst',
  'writer',
  'reviewer',
  'executor',
  'specialist',
  'custom',
  
  // Business-specific agent roles
  'bdr_concierge',
  'support_concierge',
  'research_recon',
  'ops_sapper',
  'knowledge_librarian',
  'qa_auditor',
]);
export type AgentRole = z.infer<typeof AgentRoleSchema>;

/**
 * Agent execution status.
 */
export const AgentStatusSchema = z.enum([
  'idle',
  'active',
  'thinking',
  'working',
  'waiting',
  'completed',
  'failed',
  'paused',
]);
export type AgentStatus = z.infer<typeof AgentStatusSchema>;

/**
 * Role of a message sender.
 */
export const MessageRoleSchema = z.enum(['system', 'user', 'assistant', 'function', 'tool']);
export type MessageRole = z.infer<typeof MessageRoleSchema>;

/**
 * Status of a multi-agent workflow.
 */
export const WorkflowStatusSchema = z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']);
export type WorkflowStatus = z.infer<typeof WorkflowStatusSchema>;

/**
 * A specific capability or skill that an agent possesses.
 */
export const AgentCapabilitySchema = z.object({
  name: z.string().describe('Capability name'),
  description: z.string().describe('Capability description'),
  enabled: z.boolean().default(true).describe('Whether capability is enabled'),
  tools: z.array(z.string()).optional().describe('Available tools for this capability'),
  confidence_threshold: z.number().min(0).max(1).optional().describe('Minimum confidence required to use this capability'),
});
export type AgentCapability = z.infer<typeof AgentCapabilitySchema>;

/**
 * Agent configuration model.
 */
export const AgentConfigSchema = z.object({
  agent_id: z.string().describe('Unique agent identifier'),
  name: z.string().describe('Agent display name'),
  role: AgentRoleSchema.describe('Agent role'),
  description: z.string().optional().describe('Agent description'),
  model: z.string().default('gpt-4').describe("LLM model to use (e.g., 'gpt-4', 'claude-3')"),
  temperature: z.number().min(0).max(2).default(0.7).describe('Model temperature parameter'),
  max_tokens: z.number().int().min(1).optional().describe('Maximum tokens in response'),
  capabilities: z.array(AgentCapabilitySchema).describe('Agent capabilities and tools'),
  system_prompt: z.string().describe('System prompt defining agent behavior'),
  enabled: z.boolean().default(true).describe('Whether agent is enabled'),
  metadata: z.record(z.any()).optional().describe('Additional agent metadata'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Agent creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
});
export type AgentConfig = z.infer<typeof AgentConfigSchema>;

/**
 * Message in an agent conversation.
 */
export const AgentMessageSchema = z.object({
  id: z.string().describe('Unique message identifier'),
  role: MessageRoleSchema.describe('Message sender role'),
  content: z.string().describe('Message content'),
  agent_id: z.string().optional().describe('Agent that sent this message'),
  timestamp: z.string().datetime().or(z.date()).describe('Message timestamp'),
  tool_calls: z.array(z.record(z.any())).optional().describe('Tool/function calls made in this message'),
  tool_results: z.array(z.record(z.any())).optional().describe('Results from tool/function calls'),
  metadata: z.record(z.any()).optional().describe('Additional message metadata'),
});
export type AgentMessage = z.infer<typeof AgentMessageSchema>;

/**
 * Agent execution state.
 */
export const AgentStateSchema = z.object({
  agent_id: z.string().describe('Agent identifier'),
  session_id: z.string().optional().describe('Session identifier'),
  status: AgentStatusSchema.describe('Current agent status'),
  current_task: z.string().optional().describe('Description of current task'),
  context: z.record(z.any()).describe('Agent execution context and variables'),
  message_history: z.array(AgentMessageSchema).describe('Conversation history'),
  tools_used: z.array(z.string()).describe('Tools used in this session'),
  errors: z.array(z.string()).optional().describe('Errors encountered during execution'),
  started_at: z.string().datetime().or(z.date()).describe('Session start time'),
  updated_at: z.string().datetime().or(z.date()).describe('Last update time'),
  completed_at: z.string().datetime().or(z.date()).optional().describe('Session completion time'),
  metadata: z.record(z.any()).optional().describe('Additional state metadata'),
});
export type AgentState = z.infer<typeof AgentStateSchema>;

/**
 * Configuration for a single workflow step.
 */
export const WorkflowStepConfigSchema = z.object({
  retry_on_failure: z.boolean().default(true).describe('Whether to retry step on failure'),
  max_retries: z.number().int().min(0).default(3).describe('Maximum retry attempts'),
  timeout_seconds: z.number().int().min(0).optional().describe('Step timeout in seconds'),
  required: z.boolean().default(true).describe('Whether step is required for workflow completion'),
  depends_on: z.array(z.string()).optional().describe('IDs of steps that must complete before this one'),
});
export type WorkflowStepConfig = z.infer<typeof WorkflowStepConfigSchema>;

/**
 * Step in a multi-agent workflow.
 */
export const WorkflowStepSchema = z.object({
  step_id: z.string().describe('Unique step identifier'),
  agent_id: z.string().describe('Agent executing this step'),
  name: z.string().describe('Step name'),
  description: z.string().optional().describe('Step description'),
  status: WorkflowStatusSchema.default('pending').describe('Step execution status'),
  input: z.record(z.any()).optional().describe('Step input parameters'),
  output: z.record(z.any()).optional().describe('Step output results'),
  error: z.string().optional().describe('Error message if step failed'),
  config: WorkflowStepConfigSchema.optional().describe('Step configuration'),
  retry_count: z.number().int().min(0).default(0).describe('Number of retry attempts'),
  started_at: z.string().datetime().or(z.date()).optional().describe('Step start time'),
  completed_at: z.string().datetime().or(z.date()).optional().describe('Step completion time'),
  duration_ms: z.number().int().min(0).optional().describe('Step execution duration in milliseconds'),
  metadata: z.record(z.any()).optional().describe('Additional step metadata'),
});
export type WorkflowStep = z.infer<typeof WorkflowStepSchema>;

/**
 * Multi-agent workflow model.
 */
export const WorkflowSchema = z.object({
  workflow_id: z.string().describe('Unique workflow identifier'),
  name: z.string().describe('Workflow name'),
  description: z.string().optional().describe('Workflow description'),
  status: WorkflowStatusSchema.default('pending').describe('Overall workflow status'),
  steps: z.array(WorkflowStepSchema).min(1).describe('Workflow steps in execution order'),
  context: z.record(z.any()).describe('Shared workflow context'),
  orchestrator_id: z.string().optional().describe('ID of orchestrator agent managing workflow'),
  created_by: z.string().optional().describe('User or system that created workflow'),
  created_at: z.string().datetime().or(z.date()).describe('Workflow creation time'),
  started_at: z.string().datetime().or(z.date()).optional().describe('Workflow start time'),
  completed_at: z.string().datetime().or(z.date()).optional().describe('Workflow completion time'),
  total_duration_ms: z.number().int().min(0).optional().describe('Total workflow duration in milliseconds'),
  metadata: z.record(z.any()).optional().describe('Additional workflow metadata'),
});
export type Workflow = z.infer<typeof WorkflowSchema>;

/**
 * Performance metrics for an agent.
 */
export const AgentPerformanceMetricsSchema = z.object({
  agent_id: z.string().describe('Agent identifier'),
  total_tasks: z.number().int().min(0).describe('Total tasks attempted'),
  completed_tasks: z.number().int().min(0).describe('Successfully completed tasks'),
  failed_tasks: z.number().int().min(0).describe('Failed tasks'),
  success_rate: z.number().min(0).max(1).describe('Task success rate (0-1)'),
  average_duration_ms: z.number().min(0).optional().describe('Average task duration in milliseconds'),
  total_tool_calls: z.number().int().min(0).describe('Total tool/function calls made'),
  average_tokens_used: z.number().min(0).optional().describe('Average tokens used per task'),
  period_start: z.string().datetime().or(z.date()).describe('Metrics period start'),
  period_end: z.string().datetime().or(z.date()).describe('Metrics period end'),
});
export type AgentPerformanceMetrics = z.infer<typeof AgentPerformanceMetricsSchema>;