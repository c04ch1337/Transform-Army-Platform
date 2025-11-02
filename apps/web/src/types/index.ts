/**
 * Frontend type definitions.
 * 
 * Imports types from the shared schema package to ensure
 * type safety between frontend and backend.
 */

// API Response types
export interface ApiResponse<T = any> {
  data?: T
  error?: ApiError
  meta?: {
    total?: number
    page?: number
    limit?: number
  }
}

export interface ApiError {
  code: string
  message: string
  details?: any
  correlation_id?: string
  timestamp?: string
}

// Tenant types
export interface Tenant {
  id: string
  name: string
  slug: string
  is_active: boolean
  provider_configs?: Record<string, any>
  created_at: string
  updated_at?: string
}

// Action Log types
export interface ActionLog {
  id: string
  tenant_id: string
  action_type: string
  provider_name: string
  status: 'SUCCESS' | 'FAILURE' | 'PENDING' | 'TIMEOUT' | 'RETRY'
  error_message?: string
  execution_time_ms: number
  created_at: string
}

export interface ActionLogDetail extends ActionLog {
  request_payload: Record<string, any>
  response_data?: Record<string, any>
  metadata?: Record<string, any>
  updated_at: string
}

// Audit Log types
export interface AuditLog {
  id: string
  tenant_id: string
  action: string
  resource_type: string
  resource_id: string
  user_id?: string
  changes?: Record<string, any>
  ip_address?: string
  created_at: string
}

// Provider types
export interface ProviderStatus {
  name: string
  type: 'CRM' | 'HELPDESK' | 'CALENDAR' | 'EMAIL' | 'KNOWLEDGE'
  enabled: boolean
  healthy: boolean
  last_check?: string
}

// Statistics types
export interface ActionStats {
  total_actions: number
  successful_actions: number
  failed_actions: number
  average_execution_time_ms: number
  actions_by_type: Record<string, number>
  actions_by_provider: Record<string, number>
}

// Workflow types (for React Flow)
export interface WorkflowNode {
  id: string
  type: 'agent' | 'decision' | 'action' | 'trigger'
  data: {
    label: string
    agent_type?: string
    config?: Record<string, any>
  }
  position: { x: number; y: number }
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  type?: 'default' | 'conditional'
  label?: string
}

// Agent types
export interface Agent {
  agent_id: string
  name: string
  type: string
  version: string
  status: 'active' | 'standby' | 'training' | 'offline'
  description: string
  role: {
    primary: string
    squad: string
    phase: string
  }
  model: {
    primary: string
    fallback: string
    temperature: number
    max_tokens: number
  }
  tools: string[]
  permissions: Record<string, string[]>
  thresholds: Record<string, any>
  sla?: Record<string, any>
  cost_budget?: {
    per_operation?: number
    per_ticket?: number
    per_research?: number
    per_check?: number
    per_article?: number
    per_evaluation?: number
    daily_max: number
  }
  monitoring?: {
    check_frequency_minutes: number
    alert_channels: string[]
  }
}

export interface AgentStats {
  agent_id: string
  missions_completed: number
  success_rate: number
  avg_response_time_ms: number
  last_active: string
}

export interface Squad {
  squad_id: string
  name: string
  description: string
  agents: string[]
  lead_agent: string
  workflows: string[]
}

// Agent Configuration Types
export interface AgentConfig {
  name: string
  model: {
    provider: string
    model: string
    temperature: number
    maxTokens: number
  }
  voice: {
    provider: string
    voiceId: string
  }
  systemPrompt: string
  firstMessage: string
  endCallMessage?: string
  functions: AgentFunction[]
  serverUrl: string
  serverUrlSecret?: string
}

export interface AgentFunction {
  name: string
  description: string
  parameters: Record<string, any>
  enabled?: boolean
}

export interface ConfigVersion {
  version: number
  timestamp: string
  changes: string
  config: AgentConfig
}