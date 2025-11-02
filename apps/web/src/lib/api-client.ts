/**
 * API client for Transform Army AI Adapter.
 * 
 * Handles authentication, error handling, and type-safe requests.
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  ApiResponse,
  Tenant,
  ActionLog,
  ActionLogDetail,
  AuditLog,
  ActionStats,
  ProviderStatus,
  Agent,
  AgentStats
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class AdapterClient {
  private client: AxiosInstance
  private apiKey: string | null = null

  constructor(apiKey?: string) {
    this.apiKey = apiKey || null

    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add API key
    this.client.interceptors.request.use((config) => {
      if (this.apiKey) {
        config.headers['X-API-Key'] = this.apiKey
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiResponse>) => {
        // Transform error into standard format
        const apiError = error.response?.data?.error || {
          code: 'UNKNOWN_ERROR',
          message: error.message,
        }
        return Promise.reject(apiError)
      }
    )
  }

  setApiKey(apiKey: string) {
    this.apiKey = apiKey
  }

  // Tenant Management
  async getCurrentTenant(): Promise<Tenant> {
    const response = await this.client.get<Tenant>('/api/v1/admin/tenants/me')
    return response.data
  }

  async createTenant(data: {
    name: string
    slug: string
    provider_configs?: Record<string, any>
  }): Promise<Tenant & { api_key: string }> {
    const response = await this.client.post<Tenant & { api_key: string }>(
      '/api/v1/admin/tenants',
      data
    )
    return response.data
  }

  async rotateApiKey(tenantId: string): Promise<{ tenant_id: string; new_api_key: string }> {
    const response = await this.client.post(
      `/api/v1/admin/tenants/${tenantId}/rotate-api-key`
    )
    return response.data
  }

  // Action Logs
  async getActionLogs(params?: {
    action_type?: string
    status?: string
    provider_name?: string
    skip?: number
    limit?: number
  }): Promise<ActionLog[]> {
    const response = await this.client.get<ActionLog[]>('/api/v1/logs/actions', { params })
    return response.data
  }

  async getRecentLogs(limit: number = 50): Promise<ActionLog[]> {
    const response = await this.client.get<ActionLog[]>('/api/v1/logs/actions', {
      params: { limit, skip: 0 }
    })
    return response.data
  }

  async getActionLogDetail(actionId: string): Promise<ActionLogDetail> {
    const response = await this.client.get<ActionLogDetail>(`/api/v1/logs/actions/${actionId}`)
    return response.data
  }

  async getRecentFailedActions(minutes: number = 60, limit: number = 50): Promise<ActionLog[]> {
    const response = await this.client.get<ActionLog[]>('/api/v1/logs/actions/failed/recent', {
      params: { minutes, limit }
    })
    return response.data
  }

  async getActionStats(): Promise<ActionStats> {
    const response = await this.client.get<ActionStats>('/api/v1/logs/stats')
    return response.data
  }

  // Audit Logs
  async getAuditLogs(params?: {
    action?: string
    resource_type?: string
    skip?: number
    limit?: number
  }): Promise<AuditLog[]> {
    const response = await this.client.get<AuditLog[]>('/api/v1/logs/audits', { params })
    return response.data
  }

  async getResourceAuditLogs(
    resourceType: string,
    resourceId: string
  ): Promise<AuditLog[]> {
    const response = await this.client.get<AuditLog[]>(
      `/api/v1/logs/audits/resource/${resourceType}/${resourceId}`
    )
    return response.data
  }

  // Health & Status
  async getHealth(): Promise<{ status: string; timestamp: string; version: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  async getProviderRegistry(): Promise<{
    status: string
    total_providers: number
    by_type: Record<string, { count: number; providers: string[]; classes: string[] }>
  }> {
    const response = await this.client.get('/health/providers')
    return response.data
  }

  async getReadiness(): Promise<{
    status: string
    providers: Record<string, string>
  }> {
    const response = await this.client.get('/health/ready')
    return response.data
  }

  // CRM Operations (examples)
  async createContact(data: {
    email: string
    first_name?: string
    last_name?: string
    company?: string
    phone?: string
  }): Promise<any> {
    const response = await this.client.post('/api/v1/crm/contacts', data)
    return response.data
  }

  async searchContacts(query: string, limit: number = 10): Promise<any> {
    const response = await this.client.post('/api/v1/crm/contacts/search', {
      query,
      limit
    })
    return response.data
  }

  // Helpdesk Operations (examples)
  async createTicket(data: {
    subject: string
    description: string
    priority?: string
    requester_email?: string
  }): Promise<any> {
    const response = await this.client.post('/api/v1/helpdesk/tickets', data)
    return response.data
  }

  async searchTickets(query: string, filters?: Record<string, any>): Promise<any> {
    const response = await this.client.post('/api/v1/helpdesk/tickets/search', {
      query,
      ...filters
    })
    return response.data
  }

  // Agent Operations
  async getAgents(): Promise<Agent[]> {
    const response = await this.client.get<{ total: number; agents: Agent[] }>('/api/v1/agents')
    return response.data.agents
  }

  async getAgent(agentId: string): Promise<Agent> {
    const response = await this.client.get<Agent>(`/api/v1/agents/${agentId}`)
    return response.data
  }

  async getAgentStats(agentId: string): Promise<AgentStats> {
    const response = await this.client.get<AgentStats>(`/api/v1/agents/${agentId}/stats`)
    return response.data
  }

  // Agent Configuration Management
  async getAgentConfig(agentId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/agents/${agentId}/config`)
    return response.data
  }

  async updateAgentConfig(agentId: string, config: any): Promise<any> {
    const response = await this.client.put(`/api/v1/agents/${agentId}/config`, config)
    return response.data
  }

  async validateAgentConfig(agentId: string, config: any): Promise<{is_valid: boolean, errors: string[]}> {
    const response = await this.client.post(`/api/v1/agents/${agentId}/config/validate`, config)
    return response.data
  }

  async getConfigHistory(agentId: string): Promise<any[]> {
    const response = await this.client.get(`/api/v1/agents/${agentId}/config/history`)
    return response.data
  }

  async restoreConfigVersion(agentId: string, version: number): Promise<any> {
    const response = await this.client.post(`/api/v1/agents/${agentId}/config/restore/${version}`)
    return response.data
  }

  async resetAgentConfig(agentId: string): Promise<any> {
    const response = await this.client.post(`/api/v1/agents/${agentId}/config/reset`)
    return response.data
  }
}

// Export singleton instance
export const apiClient = new AdapterClient()

// Export class for custom instances
export default AdapterClient