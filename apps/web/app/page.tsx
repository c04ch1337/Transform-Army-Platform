'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TacticalHeader } from "@/components/tactical-header"
import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import type { ActionStats } from "@/types"

interface HealthData {
  status: string
  timestamp: string
  version: string
}

interface ProviderRegistry {
  status: string
  total_providers: number
  by_type: Record<string, { count: number; providers: string[]; classes: string[] }>
}

interface ProviderInfo {
  name: string
  type: string
  signal: number
}

export default function CommandCenter() {
  const [isOnline, setIsOnline] = useState<boolean>(true)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [healthData, setHealthData] = useState<HealthData | null>(null)
  const [statsData, setStatsData] = useState<ActionStats | null>(null)
  const [providerData, setProviderData] = useState<ProviderRegistry | null>(null)

  // Format provider data for display
  const getProviderList = (): ProviderInfo[] => {
    if (!providerData) return []

    const providers: ProviderInfo[] = []
    Object.entries(providerData.by_type).forEach(([type, info]) => {
      info.providers.forEach((providerName) => {
        providers.push({
          name: providerName,
          type: type.toUpperCase(),
          signal: 3 // Full signal when connected
        })
      })
    })
    return providers
  }

  // Fetch all data from backend
  const fetchData = async () => {
    try {
      // Fetch in parallel for better performance
      const [health, stats, providers] = await Promise.all([
        apiClient.getHealth(),
        apiClient.getActionStats(),
        apiClient.getProviderRegistry()
      ])

      setHealthData(health)
      setStatsData(stats)
      setProviderData(providers)
      setIsOnline(true)
    } catch (error) {
      console.error('Failed to fetch data from backend:', error)
      setIsOnline(false)
      
      // Fallback to mock data in offline mode
      if (!healthData) {
        setHealthData({
          status: 'offline',
          timestamp: new Date().toISOString(),
          version: 'v1.0.0'
        })
      }
      if (!statsData) {
        setStatsData({
          total_actions: 0,
          successful_actions: 0,
          failed_actions: 0,
          average_execution_time_ms: 0,
          actions_by_type: {},
          actions_by_provider: {}
        })
      }
      if (!providerData) {
        setProviderData({
          status: 'offline',
          total_providers: 3,
          by_type: {
            crm: { count: 1, providers: ['HubSpot'], classes: ['HubSpotProvider'] },
            helpdesk: { count: 1, providers: ['Zendesk'], classes: ['ZendeskProvider'] },
            calendar: { count: 1, providers: ['Google Calendar'], classes: ['GoogleCalendarProvider'] }
          }
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchData()
  }, [])

  // Periodic refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData()
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  // Calculate success rate
  const getSuccessRate = (): string => {
    if (!statsData || statsData.total_actions === 0) return '--'
    const rate = (statsData.successful_actions / statsData.total_actions) * 100
    return rate.toFixed(1)
  }

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <div className="animate-pulse space-y-3">
      <div className="h-4 bg-tactical-green/20 rounded w-3/4"></div>
      <div className="h-4 bg-tactical-green/20 rounded w-1/2"></div>
      <div className="h-4 bg-tactical-green/20 rounded w-2/3"></div>
    </div>
  )

  return (
    <div className="flex min-h-screen flex-col bg-tactical-black text-foreground">
      <TacticalHeader
        title="Transform Army AI"
        badge="Command Center"
        isOnline={isOnline}
      />

      {/* Command Center Grid */}
      <main className="flex-1 container py-6 tactical-grid">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          
          {/* System Status - Intel Card */}
          <Card className="intel-card">
            <CardHeader>
              <CardTitle className="heading-tactical text-base">System Status</CardTitle>
              <CardDescription className="label-ops">Adapter Service</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <LoadingSkeleton />
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Operational Status</span>
                    <Badge className={isOnline ? "status-operational" : "bg-amber-500"}>
                      {isOnline ? 'OPERATIONAL' : 'OFFLINE'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Version</span>
                    <span className="font-mono text-sm text-tactical-gold">
                      {healthData?.version || 'v1.0.0'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last Check</span>
                    <span className="font-mono text-sm text-terminal-green">
                      {healthData?.timestamp 
                        ? new Date(healthData.timestamp).toLocaleTimeString('en-US', { hour12: false })
                        : '--:--:--'}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Provider Assets */}
          <Card className="command-panel">
            <CardHeader>
              <CardTitle className="heading-tactical text-base">Intel Sources</CardTitle>
              <CardDescription className="label-ops">Active Providers</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <LoadingSkeleton />
              ) : (
                <div className="space-y-2">
                  {getProviderList().length > 0 ? (
                    getProviderList().map((provider, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="text-sm">{provider.name}</span>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="font-mono text-xs">
                            {provider.type}
                          </Badge>
                          <div className="signal-strength">
                            <div className={`signal-bar h-3 ${isOnline ? '' : 'opacity-30'}`} />
                            <div className={`signal-bar h-4 ${isOnline ? '' : 'opacity-30'}`} />
                            <div className={`signal-bar h-5 ${isOnline ? '' : 'opacity-30'}`} />
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-muted-foreground">No providers configured</div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Mission Activity */}
          <Card className="command-panel">
            <CardHeader>
              <CardTitle className="heading-tactical text-base">Mission Activity</CardTitle>
              <CardDescription className="label-ops">Last 24 Hours</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <LoadingSkeleton />
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total Missions</span>
                    <span className="text-2xl font-tactical font-bold text-tactical-gold">
                      {statsData?.total_actions || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Success Rate</span>
                    <span className="font-mono text-terminal-green">
                      {getSuccessRate()}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Avg Response</span>
                    <span className="font-mono text-sm">
                      {statsData?.average_execution_time_ms 
                        ? `${Math.round(statsData.average_execution_time_ms)} ms`
                        : '-- ms'}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Operations Briefing */}
        <Card className="mt-6 intel-card">
          <CardHeader>
            <CardTitle className="heading-tactical">Operations Briefing</CardTitle>
            <CardDescription className="label-ops">Transform Army AI Command Center</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm prose-invert max-w-none">
              <p className="text-foreground">
                Welcome to the Transform Army AI tactical operations center. This command interface provides 
                real-time visibility and control over your multi-agent AI force.
              </p>
              {!isOnline && (
                <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded">
                  <p className="text-amber-400 text-sm mb-0">
                    ⚠️ <strong>OFFLINE MODE:</strong> Backend adapter service is not reachable. 
                    Displaying cached data. System will automatically reconnect when service is available.
                  </p>
                </div>
              )}
              <h4 className="heading-tactical text-sm mt-4 mb-2">Mission Objectives:</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>🎯 Configure unit API credentials and access tokens</li>
                <li>🔧 Establish provider integration channels (HubSpot, Zendesk, Google)</li>
                <li>📊 Monitor agent deployment status and mission performance</li>
                <li>📝 Review after-action reports (AARs) and intelligence logs</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}