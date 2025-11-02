'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TacticalHeader } from '@/components/tactical-header'
import { VoiceCallButton } from '@/components/voice-call-button'
import { VapiWidget } from '@/components/vapi-widget'
import { apiClient } from '@/lib/api-client'
import { Agent, AgentStats } from '@/types'
import { MilitaryRank, RANK_DATA } from '@/lib/constants/ranks'
import {
  Activity,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Filter,
  RefreshCw,
  Search,
  Shield,
  Signal,
  Star,
  Target,
  TrendingUp,
  Users,
  Wifi,
  WifiOff
} from 'lucide-react'

// Mock data for agents with military callsigns and stats
const MOCK_AGENT_DATA = [
  {
    agent_id: 'bdr-concierge',
    callSign: 'ALPHA-1',
    nickname: 'Hunter',
    rank: MilitaryRank.STAFF_SERGEANT,
    mos: '11B',
    missions: 247,
    successRate: 94.8,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_BDR_ASSISTANT_ID || 'demo-bdr',
  },
  {
    agent_id: 'support-concierge',
    callSign: 'ALPHA-2',
    nickname: 'Medic',
    rank: MilitaryRank.SERGEANT,
    mos: '68W',
    missions: 892,
    successRate: 96.2,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_SUPPORT_ASSISTANT_ID || 'demo-support',
  },
  {
    agent_id: 'research-recon',
    callSign: 'BRAVO-1',
    nickname: 'Scout',
    rank: MilitaryRank.SERGEANT_FIRST_CLASS,
    mos: '19D',
    missions: 156,
    successRate: 91.7,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_RESEARCH_ASSISTANT_ID || 'demo-research',
  },
  {
    agent_id: 'ops-sapper',
    callSign: 'BRAVO-2',
    nickname: 'Sapper',
    rank: MilitaryRank.SERGEANT,
    mos: '12B',
    missions: 432,
    successRate: 98.1,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_OPS_ASSISTANT_ID || 'demo-ops',
  },
  {
    agent_id: 'knowledge-librarian',
    callSign: 'CHARLIE-1',
    nickname: 'Intel',
    rank: MilitaryRank.SERGEANT_FIRST_CLASS,
    mos: '35F',
    missions: 623,
    successRate: 95.4,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_KNOWLEDGE_ASSISTANT_ID || 'demo-knowledge',
  },
  {
    agent_id: 'qa-auditor',
    callSign: 'CHARLIE-2',
    nickname: 'Guardian',
    rank: MilitaryRank.MASTER_SERGEANT,
    mos: '35M',
    missions: 1053,
    successRate: 99.1,
    lastActive: new Date().toISOString(),
    vapiAssistantId: process.env.NEXT_PUBLIC_VAPI_QA_ASSISTANT_ID || 'demo-qa',
  },
]

type SortField = 'callSign' | 'missions' | 'successRate' | 'status'
type FilterSquad = 'all' | 'sales-squad' | 'support-squad' | 'ops-squad'

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isOnline, setIsOnline] = useState(true)
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortField>('callSign')
  const [filterSquad, setFilterSquad] = useState<FilterSquad>('all')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch agents data
  const fetchAgents = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getAgents()
      setAgents(data)
      setIsOnline(true)
      setError(null)
    } catch (err: any) {
      console.error('Failed to fetch agents:', err)
      setError(err.message || 'Failed to fetch agents')
      setIsOnline(false)
      // Use mock data in offline mode
      if (agents.length === 0) {
        // Load mock agents from agent-configs structure
        const mockAgents: Agent[] = [
          {
            agent_id: 'bdr-concierge',
            name: 'BDR Concierge',
            type: 'bdr-concierge',
            version: '1.0.0',
            status: 'active',
            description: 'Inbound lead qualification and meeting coordination',
            role: { primary: 'sales', squad: 'sales-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-4', fallback: 'gpt-3.5-turbo', temperature: 0.3, max_tokens: 2000 },
            tools: ['crm.contacts.search', 'crm.contacts.create', 'calendar.events.create', 'email.send'],
            permissions: { crm: ['read', 'write'], calendar: ['read', 'write'], email: ['send'] },
            thresholds: { qualification_score: 70, confidence_min: 0.7 },
            cost_budget: { per_operation: 0.50, daily_max: 50.00 }
          },
          {
            agent_id: 'support-concierge',
            name: 'Support Concierge',
            type: 'support-concierge',
            version: '1.0.0',
            status: 'active',
            description: 'Tier-0/1 support triage and deflection',
            role: { primary: 'support', squad: 'support-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-4', fallback: 'gpt-3.5-turbo', temperature: 0.2, max_tokens: 1500 },
            tools: ['helpdesk.tickets.read', 'helpdesk.tickets.update', 'knowledge.search', 'crm.contacts.search'],
            permissions: { helpdesk: ['read', 'write'], knowledge: ['read'], crm: ['read'] },
            thresholds: { kb_confidence_min: 0.80, deflection_confidence: 0.75 },
            cost_budget: { per_ticket: 0.30, daily_max: 40.00 }
          },
          {
            agent_id: 'research-recon',
            name: 'Research Recon',
            type: 'research-recon',
            version: '1.0.0',
            status: 'active',
            description: 'Competitive intelligence and market research',
            role: { primary: 'research', squad: 'sales-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-4', fallback: 'gpt-3.5-turbo', temperature: 0.3, max_tokens: 4000 },
            tools: ['web.search', 'web.scrape', 'data.company.lookup', 'crm.companies.search'],
            permissions: { web: ['search', 'scrape'], crm: ['read', 'write'], data: ['lookup'] },
            thresholds: { confidence_min: 0.75 },
            cost_budget: { per_research: 5.00, daily_max: 30.00 }
          },
          {
            agent_id: 'ops-sapper',
            name: 'Ops Sapper',
            type: 'ops-sapper',
            version: '1.0.0',
            status: 'active',
            description: 'Operational monitoring and SLA tracking',
            role: { primary: 'operations', squad: 'ops-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-3.5-turbo', fallback: 'gpt-3.5-turbo', temperature: 0.1, max_tokens: 1000 },
            tools: ['analytics.query', 'helpdesk.tickets.search', 'crm.deals.search', 'slack.notify'],
            permissions: { analytics: ['read'], helpdesk: ['read'], crm: ['read'], slack: ['send'] },
            thresholds: { sla_alert_minutes_before: 15, data_quality_min: 0.90 },
            monitoring: { check_frequency_minutes: 60, alert_channels: ['slack', 'email'] },
            cost_budget: { per_check: 0.10, daily_max: 10.00 }
          },
          {
            agent_id: 'knowledge-librarian',
            name: 'Knowledge Librarian',
            type: 'knowledge-librarian',
            version: '1.0.0',
            status: 'active',
            description: 'Knowledge base management and maintenance',
            role: { primary: 'knowledge', squad: 'support-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-4', fallback: 'gpt-3.5-turbo', temperature: 0.3, max_tokens: 4000 },
            tools: ['knowledge.articles.create', 'knowledge.articles.update', 'document.parse', 'helpdesk.tickets.search'],
            permissions: { knowledge: ['read', 'write'], documents: ['parse'], helpdesk: ['read'] },
            thresholds: { freshness_days_max: 90, quality_score_min: 0.90 },
            cost_budget: { per_article: 2.00, daily_max: 20.00 }
          },
          {
            agent_id: 'qa-auditor',
            name: 'QA Auditor',
            type: 'qa-auditor',
            version: '1.0.0',
            status: 'active',
            description: 'Quality assurance and validation',
            role: { primary: 'quality', squad: 'ops-squad', phase: 'ground-forces' },
            model: { primary: 'gpt-4', fallback: 'gpt-3.5-turbo', temperature: 0.1, max_tokens: 1000 },
            tools: ['analytics.query', 'slack.notify'],
            permissions: { analytics: ['read'], all_agent_outputs: ['read'], slack: ['send'] },
            thresholds: { quality_score_min: 7.0, block_threshold: 6.0 },
            cost_budget: { per_evaluation: 0.05, daily_max: 15.00 }
          }
        ]
        setAgents(mockAgents)
      }
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchAgents()
  }, [])

  // Auto-refresh every 20 seconds
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      fetchAgents()
    }, 20000)
    return () => clearInterval(interval)
  }, [autoRefresh])

  // Get agent metadata
  const getAgentMetadata = (agentId: string) => {
    return MOCK_AGENT_DATA.find(m => m.agent_id === agentId) || {
      agent_id: agentId,
      callSign: 'UNKNOWN',
      nickname: 'Unknown',
      rank: MilitaryRank.SERGEANT,
      mos: '00X',
      missions: 0,
      successRate: 0,
      lastActive: new Date().toISOString(),
      vapiAssistantId: 'demo-unknown',
    }
  }

  // Get squad color
  const getSquadColor = (squad: string) => {
    if (squad.includes('sales')) return 'text-tactical-green border-tactical-green'
    if (squad.includes('support')) return 'text-tactical-gold border-tactical-gold'
    return 'text-tactical-blue border-tactical-blue'
  }

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-terminal-green/20 text-terminal-green border-terminal-green/30'
      case 'standby': return 'bg-tactical-gold/20 text-tactical-gold border-tactical-gold/30'
      case 'training': return 'bg-tactical-blue/20 text-tactical-blue border-tactical-blue/30'
      default: return 'bg-gray-500/20 text-gray-500 border-gray-500/30'
    }
  }

  // Filter and sort agents
  const filteredAndSortedAgents = useMemo(() => {
    if (!Array.isArray(agents) || agents.length === 0) {
      return []
    }
    
    let filtered = agents.filter(agent => {
      const metadata = getAgentMetadata(agent.agent_id)
      const matchesSearch = 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        metadata.callSign.toLowerCase().includes(searchQuery.toLowerCase()) ||
        metadata.nickname.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.role.primary.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesSquad = filterSquad === 'all' || agent.role.squad === filterSquad
      
      return matchesSearch && matchesSquad
    })

    filtered.sort((a, b) => {
      const metaA = getAgentMetadata(a.agent_id)
      const metaB = getAgentMetadata(b.agent_id)
      
      switch (sortBy) {
        case 'callSign':
          return metaA.callSign.localeCompare(metaB.callSign)
        case 'missions':
          return metaB.missions - metaA.missions
        case 'successRate':
          return metaB.successRate - metaA.successRate
        case 'status':
          return a.status.localeCompare(b.status)
        default:
          return 0
      }
    })

    return filtered
  }, [agents, searchQuery, sortBy, filterSquad])

  // Calculate overview stats
  const overviewStats = useMemo(() => {
    if (!Array.isArray(agents)) {
      return { totalAgents: 0, activeAgents: 0, totalMissions: 0, avgSuccessRate: 0 }
    }
    
    const totalAgents = agents.length
    const activeAgents = agents.filter(a => a.status === 'active').length
    const totalMissions = MOCK_AGENT_DATA.reduce((sum, m) => sum + m.missions, 0)
    const avgSuccessRate = MOCK_AGENT_DATA.length > 0
      ? MOCK_AGENT_DATA.reduce((sum, m) => sum + m.successRate, 0) / MOCK_AGENT_DATA.length
      : 0

    return { totalAgents, activeAgents, totalMissions, avgSuccessRate }
  }, [agents])

  // Render rank badge
  const renderRankBadge = (rank: MilitaryRank) => {
    const rankInfo = RANK_DATA[rank]
    return (
      <div className="flex items-center gap-1 px-2 py-1 bg-tactical-black border border-tactical-gold/30 rounded font-mono text-xs uppercase tracking-wider">
        <Shield className="w-3 h-3 text-tactical-gold" />
        <span className="text-tactical-gold">{rankInfo.abbreviation}</span>
      </div>
    )
  }

  // Render signal strength
  const renderSignalStrength = (status: string) => {
    const isActive = status === 'active'
    return (
      <div className="flex gap-0.5 items-end">
        {[1, 2, 3, 4].map(bar => (
          <div
            key={bar}
            className={`w-1 transition-all duration-300 ${
              isActive && bar <= 4
                ? 'bg-terminal-green'
                : 'bg-gray-600'
            }`}
            style={{ height: `${bar * 3}px` }}
          />
        ))}
      </div>
    )
  }

  if (loading && agents.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-tactical-black via-tactical-black-light to-tactical-black p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-tactical-green">
            <RefreshCw className="w-12 h-12 mx-auto mb-4 animate-spin" />
            <p className="font-mono text-lg">LOADING AGENT ROSTER...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-tactical-black via-tactical-black-light to-tactical-black">
      <TacticalHeader
        title="Transform Army AI"
        badge="Agent Roster"
        subtitle="Tactical AI Squadron"
        isOnline={isOnline}
      />
      
      <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">

        {/* Error Banner */}
        {error && !isOnline && (
          <Card className="border-terminal-red bg-terminal-red/10">
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-terminal-red" />
                <div>
                  <p className="font-mono text-sm text-terminal-red font-semibold">CONNECTION LOST</p>
                  <p className="font-mono text-xs text-gray-400">Operating in offline mode with cached data</p>
                </div>
              </div>
              <Button
                onClick={fetchAgents}
                variant="outline"
                size="sm"
                className="border-terminal-red text-terminal-red hover:bg-terminal-red/20"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                RETRY
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-tactical-black/50 border-tactical-green/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-gray-400 uppercase">Total Agents</p>
                  <p className="font-tactical text-3xl text-tactical-green font-bold">
                    {overviewStats.totalAgents}
                  </p>
                </div>
                <Users className="w-8 h-8 text-tactical-green/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-tactical-black/50 border-terminal-green/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-gray-400 uppercase">Active Missions</p>
                  <p className="font-tactical text-3xl text-terminal-green font-bold">
                    {overviewStats.totalMissions}
                  </p>
                </div>
                <Target className="w-8 h-8 text-terminal-green/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-tactical-black/50 border-tactical-gold/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-gray-400 uppercase">Avg Success Rate</p>
                  <p className="font-tactical text-3xl text-tactical-gold font-bold">
                    {overviewStats.avgSuccessRate.toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-tactical-gold/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-tactical-black/50 border-tactical-blue/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-gray-400 uppercase">Operational</p>
                  <p className="font-tactical text-3xl text-tactical-blue font-bold">
                    {overviewStats.activeAgents}/{overviewStats.totalAgents}
                  </p>
                </div>
                <Activity className="w-8 h-8 text-tactical-blue/50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filter Controls */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tactical-green" />
            <Input
              type="text"
              placeholder="SEARCH AGENTS BY NAME, CALLSIGN, OR ROLE..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-tactical-black border-tactical-green/30 text-terminal-green placeholder:text-gray-600 font-mono uppercase"
            />
          </div>
          
          <div className="flex gap-2">
            <select
              value={filterSquad}
              onChange={(e) => setFilterSquad(e.target.value as FilterSquad)}
              className="px-4 py-2 bg-tactical-black border border-tactical-green/30 text-tactical-green font-mono text-sm uppercase rounded-md"
            >
              <option value="all">ALL SQUADS</option>
              <option value="sales-squad">ALPHA SQUAD</option>
              <option value="support-squad">BRAVO SQUAD</option>
              <option value="ops-squad">CHARLIE SQUAD</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortField)}
              className="px-4 py-2 bg-tactical-black border border-tactical-green/30 text-tactical-green font-mono text-sm uppercase rounded-md"
            >
              <option value="callSign">SORT: CALLSIGN</option>
              <option value="missions">SORT: MISSIONS</option>
              <option value="successRate">SORT: SUCCESS RATE</option>
              <option value="status">SORT: STATUS</option>
            </select>

            <Button
              onClick={fetchAgents}
              variant="outline"
              size="sm"
              className="border-tactical-green text-tactical-green hover:bg-tactical-green/20"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredAndSortedAgents.map((agent) => {
            const metadata = getAgentMetadata(agent.agent_id)
            const isExpanded = expandedAgent === agent.agent_id
            
            return (
              <Card
                key={agent.agent_id}
                className={`bg-gradient-to-br from-tactical-black to-tactical-black-light border-l-4 ${getSquadColor(
                  agent.role.squad
                )} hover:shadow-lg transition-all cursor-pointer`}
                onClick={() => setExpandedAgent(isExpanded ? null : agent.agent_id)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="font-tactical text-3xl font-bold text-tactical-gold uppercase">
                          {metadata.callSign}
                        </div>
                        {renderRankBadge(metadata.rank)}
                      </div>
                      <div className="font-mono text-lg text-tactical-green">
                        "{metadata.nickname}" - {agent.name}
                      </div>
                      <div className="font-mono text-xs text-gray-500 uppercase mt-1">
                        MOS: {metadata.mos} • {agent.role.primary}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {renderSignalStrength(agent.status)}
                      <Badge className={`${getStatusColor(agent.status)} uppercase font-mono text-xs`}>
                        {agent.status}
                      </Badge>
                    </div>
                  </div>

                  <p className="text-gray-400 text-sm">{agent.description}</p>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Stats Row */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="font-mono text-xs text-gray-500 uppercase">Missions</p>
                      <p className="font-tactical text-2xl text-terminal-green">{metadata.missions}</p>
                    </div>
                    <div className="text-center">
                      <p className="font-mono text-xs text-gray-500 uppercase">Success Rate</p>
                      <p className="font-tactical text-2xl text-tactical-gold">{metadata.successRate}%</p>
                    </div>
                    <div className="text-center">
                      <p className="font-mono text-xs text-gray-500 uppercase">Squad</p>
                      <p className="font-mono text-sm text-tactical-blue uppercase">
                        {agent.role.squad.replace('-squad', '')}
                      </p>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="space-y-3 pt-4 border-t border-tactical-green/20">
                      <div>
                        <p className="font-mono text-xs text-gray-500 uppercase mb-2">Authorized Tools</p>
                        <div className="flex flex-wrap gap-1">
                          {agent.tools.slice(0, 4).map((tool, i) => (
                            <Badge key={i} variant="outline" className="text-xs font-mono border-tactical-green/30 text-tactical-green">
                              {tool.split('.').pop()}
                            </Badge>
                          ))}
                          {agent.tools.length > 4 && (
                            <Badge variant="outline" className="text-xs font-mono border-tactical-green/30 text-tactical-green">
                              +{agent.tools.length - 4} more
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div>
                        <p className="font-mono text-xs text-gray-500 uppercase mb-2">Model Configuration</p>
                        <p className="font-mono text-xs text-gray-400">
                          Primary: {agent.model.primary} • Temperature: {agent.model.temperature}
                        </p>
                      </div>

                      <div>
                        <p className="font-mono text-xs text-gray-500 uppercase mb-2">Cost Budget</p>
                        <p className="font-mono text-xs text-gray-400">
                          Daily Max: ${agent.cost_budget?.daily_max.toFixed(2) || 'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="font-mono text-xs text-gray-500 uppercase mb-2">Last Active</p>
                        <p className="font-mono text-xs text-terminal-green">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {new Date(metadata.lastActive).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-col gap-2 pt-2">
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-tactical-green text-tactical-green hover:bg-tactical-green/20 font-mono uppercase text-xs"
                        onClick={(e) => {
                          e.stopPropagation()
                          // View details action
                        }}
                      >
                        VIEW DETAILS
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-tactical-gold text-tactical-gold hover:bg-tactical-gold/20 font-mono uppercase text-xs"
                        onClick={(e) => {
                          e.stopPropagation()
                          // Configure action
                        }}
                      >
                        CONFIGURE
                      </Button>
                    </div>
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="w-full"
                    >
                      <VoiceCallButton
                        agent_id={agent.agent_id}
                        agent_name={agent.name}
                        call_sign={metadata.callSign}
                        vapi_assistant_id={metadata.vapiAssistantId}
                      />
                    </div>
                  </div>

                  {/* Expand/Collapse Indicator */}
                  <div className="flex justify-center pt-2">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-tactical-green" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-tactical-green animate-pulse" />
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* No Results */}
        {filteredAndSortedAgents.length === 0 && (
          <Card className="bg-tactical-black/50 border-tactical-gold/30">
            <CardContent className="text-center py-12">
              <Search className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="font-mono text-lg text-gray-400 uppercase">NO AGENTS FOUND</p>
              <p className="font-mono text-sm text-gray-600 mt-2">
                Try adjusting your search or filter criteria
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Global Vapi Widget */}
      <VapiWidget agents={agents} />
    </div>
  )
}