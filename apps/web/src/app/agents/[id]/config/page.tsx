'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TacticalHeader } from '@/components/tactical-header'
import { QuickEdit } from '@/components/agent-config/quick-edit'
import { JsonEditor } from '@/components/agent-config/json-editor'
import { VersionHistory } from '@/components/agent-config/version-history'
import { apiClient } from '@/lib/api-client'
import { AgentConfig, ConfigVersion, Agent } from '@/types'
import { Settings, Save, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function AgentConfigPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [versions, setVersions] = useState<ConfigVersion[]>([])
  const [activeTab, setActiveTab] = useState('quick-edit')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Load agent and config data
  useEffect(() => {
    loadAgentData()
  }, [agentId])

  const loadAgentData = async () => {
    setIsLoading(true)
    try {
      // Load agent details
      const agentData = await apiClient.getAgent(agentId)
      setAgent(agentData)

      // Load current config
      const configData = await apiClient.getAgentConfig(agentId)
      setConfig(configData)

      // Load version history
      const historyData = await apiClient.getConfigHistory(agentId)
      setVersions(historyData)
    } catch (error: any) {
      toast({
        title: 'Failed to load agent configuration',
        description: error.message || 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async (newConfig: AgentConfig) => {
    setIsSaving(true)
    try {
      // Validate config first
      const validation = await apiClient.validateAgentConfig(agentId, newConfig)
      
      if (!validation.is_valid) {
        toast({
          title: 'Configuration validation failed',
          description: validation.errors.join(', '),
          variant: 'destructive',
        })
        setIsSaving(false)
        return
      }

      // Save config
      const savedConfig = await apiClient.updateAgentConfig(agentId, newConfig)
      setConfig(savedConfig)
      setHasUnsavedChanges(false)

      // Reload version history
      const historyData = await apiClient.getConfigHistory(agentId)
      setVersions(historyData)

      toast({
        title: 'Configuration saved successfully',
        description: 'Agent configuration has been updated',
      })
    } catch (error: any) {
      toast({
        title: 'Failed to save configuration',
        description: error.message || 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        router.push('/settings')
      }
    } else {
      router.push('/settings')
    }
  }

  const handleReset = async () => {
    if (confirm('This will reset the configuration to default values. Are you sure?')) {
      setIsSaving(true)
      try {
        const defaultConfig = await apiClient.resetAgentConfig(agentId)
        setConfig(defaultConfig)
        setHasUnsavedChanges(false)

        // Reload version history
        const historyData = await apiClient.getConfigHistory(agentId)
        setVersions(historyData)

        toast({
          title: 'Configuration reset successfully',
          description: 'Agent configuration has been reset to defaults',
        })
      } catch (error: any) {
        toast({
          title: 'Failed to reset configuration',
          description: error.message || 'An error occurred',
          variant: 'destructive',
        })
      } finally {
        setIsSaving(false)
      }
    }
  }

  const handleRestoreVersion = async (version: number) => {
    setIsSaving(true)
    try {
      const restoredConfig = await apiClient.restoreConfigVersion(agentId, version)
      setConfig(restoredConfig)
      setHasUnsavedChanges(false)

      // Reload version history
      const historyData = await apiClient.getConfigHistory(agentId)
      setVersions(historyData)

      toast({
        title: 'Version restored successfully',
        description: `Configuration restored to version ${version}`,
      })
    } catch (error: any) {
      toast({
        title: 'Failed to restore version',
        description: error.message || 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleValidate = async (configToValidate: any) => {
    try {
      return await apiClient.validateAgentConfig(agentId, configToValidate)
    } catch (error: any) {
      return { is_valid: false, errors: [error.message || 'Validation failed'] }
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col bg-tactical-black text-foreground">
        <TacticalHeader
          title="Transform Army AI"
          badge="Configuration"
          subtitle="Loading..."
          isOnline={true}
        />
        <main className="flex-1 container py-6">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <Settings className="w-16 h-16 mx-auto mb-4 text-tactical-green animate-spin" />
              <p className="text-tactical-green font-mono">Loading agent configuration...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!agent || !config) {
    return (
      <div className="flex min-h-screen flex-col bg-tactical-black text-foreground">
        <TacticalHeader
          title="Transform Army AI"
          badge="Configuration"
          subtitle="Error"
          isOnline={true}
        />
        <main className="flex-1 container py-6">
          <Card className="bg-terminal-red/10 border-terminal-red/30">
            <CardContent className="p-8 text-center">
              <AlertCircle className="w-16 h-16 mx-auto mb-4 text-terminal-red" />
              <h2 className="font-tactical text-2xl text-terminal-red uppercase mb-2">
                Agent Not Found
              </h2>
              <p className="text-gray-400 font-mono mb-4">
                Could not load agent configuration
              </p>
              <Button
                onClick={() => router.push('/settings')}
                className="bg-tactical-green hover:bg-tactical-green-light text-white font-tactical"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Settings
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-tactical-black text-foreground">
      <TacticalHeader
        title="Transform Army AI"
        badge="Configuration Editor"
        subtitle={`Agent: ${agent.name}`}
        isOnline={true}
      />

      <main className="flex-1 container py-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header with Agent Info */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => router.push('/settings')}
                className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="font-tactical text-2xl text-tactical-gold uppercase">
                  {agent.name}
                </h1>
                <p className="text-sm text-gray-400 font-mono">
                  Agent ID: {agent.agent_id}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge
                variant={agent.status === 'active' ? 'default' : 'outline'}
                className={
                  agent.status === 'active'
                    ? 'bg-terminal-green text-white'
                    : 'border-terminal-amber text-terminal-amber'
                }
              >
                {agent.status}
              </Badge>
              {hasUnsavedChanges && (
                <Badge variant="outline" className="border-terminal-amber text-terminal-amber">
                  Unsaved Changes
                </Badge>
              )}
            </div>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-tactical-black border border-tactical-green/30 p-1">
              <TabsTrigger
                value="quick-edit"
                className="data-[state=active]:bg-tactical-green data-[state=active]:text-white font-mono"
              >
                Quick Edit
              </TabsTrigger>
              <TabsTrigger
                value="advanced-json"
                className="data-[state=active]:bg-tactical-green data-[state=active]:text-white font-mono"
              >
                Advanced JSON
              </TabsTrigger>
              <TabsTrigger
                value="version-history"
                className="data-[state=active]:bg-tactical-green data-[state=active]:text-white font-mono"
              >
                Version History
              </TabsTrigger>
            </TabsList>

            <TabsContent value="quick-edit" className="space-y-6">
              <QuickEdit
                config={config}
                onSave={handleSave}
                onCancel={handleCancel}
                isLoading={isSaving}
              />
            </TabsContent>

            <TabsContent value="advanced-json" className="space-y-6">
              <JsonEditor
                config={config}
                onSave={handleSave}
                onCancel={handleCancel}
                onValidate={handleValidate}
                isLoading={isSaving}
              />
            </TabsContent>

            <TabsContent value="version-history" className="space-y-6">
              <VersionHistory
                versions={versions}
                currentVersion={versions[0]?.version}
                onRestore={handleRestoreVersion}
                isLoading={isSaving}
              />
            </TabsContent>
          </Tabs>

          {/* Quick Actions */}
          {activeTab !== 'version-history' && (
            <Card className="bg-tactical-black/30 border-tactical-green/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-400 font-mono">
                    Need help? Check the documentation or contact support.
                  </p>
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    className="border-terminal-red/30 text-terminal-red hover:bg-terminal-red/10 font-mono"
                    disabled={isSaving}
                  >
                    Reset to Default
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}