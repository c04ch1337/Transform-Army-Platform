'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TacticalHeader } from '@/components/tactical-header'
import { apiClient } from '@/lib/api-client'
import { Agent } from '@/types'
import { 
  Settings, 
  Database, 
  Key, 
  Bell, 
  Shield, 
  Users, 
  Zap,
  Edit,
  Activity,
  Clock
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function SettingsPage() {
  const router = useRouter()
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    setIsLoading(true)
    try {
      const agentData = await apiClient.getAgents()
      setAgents(agentData)
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEditConfig = (agentId: string) => {
    router.push(`/agents/${agentId}/config`)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-terminal-green text-white'
      case 'standby':
        return 'bg-terminal-amber text-white'
      case 'offline':
        return 'bg-terminal-red text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-tactical-black text-foreground">
      <TacticalHeader 
        title="Transform Army AI"
        badge="Settings"
        subtitle="System Configuration"
        isOnline={true}
      />

      <main className="flex-1 container py-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Agent Configuration Section */}
          <Card className="bg-gradient-to-br from-tactical-black to-tactical-black-light border-tactical-gold">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="font-tactical text-3xl text-tactical-gold uppercase flex items-center gap-3">
                    <Settings className="w-8 h-8" />
                    Agent Configuration
                  </CardTitle>
                  <CardDescription className="text-tactical-green font-mono mt-2">
                    Manage and configure your AI agents
                  </CardDescription>
                </div>
                <Badge className="bg-tactical-green text-white font-mono">
                  {agents.length} Agents
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <Card key={i} className="bg-tactical-black/50 border-tactical-green/30 animate-pulse">
                      <CardContent className="p-6">
                        <div className="h-4 bg-tactical-green/20 rounded mb-3"></div>
                        <div className="h-3 bg-tactical-green/10 rounded mb-2"></div>
                        <div className="h-3 bg-tactical-green/10 rounded"></div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : agents.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {agents.slice(0, 6).map((agent) => (
                    <Card 
                      key={agent.agent_id}
                      className="bg-tactical-black/50 border-tactical-green/30 hover:border-tactical-green/60 transition-all hover:shadow-lg hover:shadow-tactical-green/20"
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h3 className="font-tactical text-lg text-tactical-gold uppercase mb-1">
                              {agent.name}
                            </h3>
                            <p className="text-xs text-gray-400 font-mono">
                              {agent.type}
                            </p>
                          </div>
                          <Badge className={getStatusColor(agent.status)}>
                            {agent.status}
                          </Badge>
                        </div>

                        <div className="space-y-2 mb-4">
                          <div className="flex items-center gap-2 text-sm">
                            <Activity className="w-4 h-4 text-tactical-green" />
                            <span className="text-gray-400 font-mono">
                              {agent.role.primary}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <Clock className="w-4 h-4 text-tactical-blue" />
                            <span className="text-gray-400 font-mono text-xs">
                              v{agent.version}
                            </span>
                          </div>
                        </div>

                        <Button
                          onClick={() => handleEditConfig(agent.agent_id)}
                          className="w-full bg-tactical-green hover:bg-tactical-green-light text-white font-tactical font-semibold"
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          Edit Configuration
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="bg-tactical-black/30 border-tactical-green/20">
                  <CardContent className="p-12 text-center">
                    <Users className="w-16 h-16 mx-auto mb-4 text-tactical-green/50" />
                    <p className="text-gray-400 font-mono">No agents configured</p>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>

          {/* Recently Modified Section */}
          {agents.length > 0 && (
            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Recently Modified
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {agents.slice(0, 5).map((agent) => (
                    <div
                      key={agent.agent_id}
                      className="flex items-center justify-between p-3 bg-tactical-black/30 border border-tactical-green/20 rounded hover:border-tactical-green/40 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          agent.status === 'active' ? 'bg-terminal-green' : 'bg-terminal-amber'
                        }`} />
                        <div>
                          <p className="text-white font-mono text-sm">{agent.name}</p>
                          <p className="text-xs text-gray-400 font-mono">{agent.type}</p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEditConfig(agent.agent_id)}
                        className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10 font-mono"
                      >
                        <Edit className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Other Settings Sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Database className="w-5 h-5" />
                  Provider Configuration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Configure API credentials and connection settings for CRM, helpdesk, and calendar integrations.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Key className="w-5 h-5" />
                  Authentication
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Manage API keys, access tokens, and authentication credentials for external services.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Bell className="w-5 h-5" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Configure alert channels, notification preferences, and escalation protocols.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Shield className="w-5 h-5" />
                  Security
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Manage security policies, permissions, and access control for agents and users.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Users className="w-5 h-5" />
                  Team Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Add team members, manage roles, and configure collaboration settings.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-tactical-black/50 border-tactical-green/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-tactical-green">
                  <Zap className="w-5 h-5" />
                  Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  Optimize system performance, configure caching, and manage resource allocation.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}