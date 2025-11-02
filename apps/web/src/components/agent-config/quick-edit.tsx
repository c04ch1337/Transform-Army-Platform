'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { AgentConfig, AgentFunction } from '@/types'
import { Save, RotateCcw, Settings } from 'lucide-react'

interface QuickEditProps {
  config: AgentConfig | null
  onSave: (config: AgentConfig) => void
  onCancel: () => void
  isLoading?: boolean
}

export function QuickEdit({ config, onSave, onCancel, isLoading = false }: QuickEditProps) {
  const [formData, setFormData] = useState<AgentConfig>({
    name: '',
    model: {
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 2000
    },
    voice: {
      provider: '11labs',
      voiceId: ''
    },
    systemPrompt: '',
    firstMessage: '',
    endCallMessage: '',
    functions: [],
    serverUrl: '',
    serverUrlSecret: ''
  })

  useEffect(() => {
    if (config) {
      setFormData(config)
    }
  }, [config])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
  }

  const handleReset = () => {
    if (config) {
      setFormData(config)
    }
  }

  const toggleFunction = (functionName: string) => {
    setFormData(prev => ({
      ...prev,
      functions: prev.functions.map(fn =>
        fn.name === functionName ? { ...fn, enabled: !fn.enabled } : fn
      )
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Agent Identity */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider">
            Agent Identity
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
                Agent Name
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="bg-tactical-black border-tactical-green/30 text-white font-mono"
                placeholder="Enter agent name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="callSign" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
                Call Sign
              </Label>
              <Input
                id="callSign"
                value={formData.voice.voiceId}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  voice: { ...prev.voice, voiceId: e.target.value } 
                }))}
                className="bg-tactical-black border-tactical-green/30 text-white font-mono"
                placeholder="ALPHA-01"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Model Configuration */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider">
            AI Model Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="model" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
                Model
              </Label>
              <Select
                value={formData.model.model}
                onValueChange={(value: string) => setFormData(prev => ({
                  ...prev,
                  model: { ...prev.model, model: value }
                }))}
              >
                <SelectTrigger className="bg-tactical-black border-tactical-green/30 text-white font-mono">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-tactical-black border-tactical-green/30">
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                  <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxTokens" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
                Max Tokens
              </Label>
              <Input
                id="maxTokens"
                type="number"
                value={formData.model.maxTokens}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  model: { ...prev.model, maxTokens: parseInt(e.target.value) || 0 } 
                }))}
                className="bg-tactical-black border-tactical-green/30 text-white font-mono"
                min="100"
                max="8000"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label htmlFor="temperature" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
                Temperature
              </Label>
              <Badge variant="outline" className="bg-tactical-black border-tactical-green/30 text-tactical-green font-mono">
                {formData.model.temperature.toFixed(1)}
              </Badge>
            </div>
            <Slider
              id="temperature"
              value={[formData.model.temperature]}
              onValueChange={(value: number[]) => setFormData(prev => ({
                ...prev,
                model: { ...prev.model, temperature: value[0] }
              }))}
              min={0}
              max={2}
              step={0.1}
              className="[&_[role=slider]]:bg-tactical-green [&_[role=slider]]:border-tactical-green-dark"
            />
          </div>
        </CardContent>
      </Card>

      {/* Voice Configuration */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider">
            Voice Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="voiceProvider" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
              Voice Provider
            </Label>
            <Select
              value={formData.voice.provider}
              onValueChange={(value: string) => setFormData(prev => ({
                ...prev,
                voice: { ...prev.voice, provider: value }
              }))}
            >
              <SelectTrigger className="bg-tactical-black border-tactical-green/30 text-white font-mono">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-tactical-black border-tactical-green/30">
                <SelectItem value="11labs">ElevenLabs</SelectItem>
                <SelectItem value="openai">OpenAI TTS</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Prompts */}
      <Card className="bg-tactical-black/50 border-tactical-green/30">
        <CardHeader>
          <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider">
            System Prompts
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="systemPrompt" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
              System Prompt
            </Label>
            <textarea
              id="systemPrompt"
              value={formData.systemPrompt}
              onChange={(e) => setFormData(prev => ({ ...prev, systemPrompt: e.target.value }))}
              className="w-full min-h-[200px] bg-tactical-black border border-tactical-green/30 text-white font-mono text-sm p-3 rounded-md resize-y"
              placeholder="Enter system prompt..."
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="firstMessage" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
              First Message
            </Label>
            <textarea
              id="firstMessage"
              value={formData.firstMessage}
              onChange={(e) => setFormData(prev => ({ ...prev, firstMessage: e.target.value }))}
              className="w-full min-h-[80px] bg-tactical-black border border-tactical-green/30 text-white font-mono text-sm p-3 rounded-md resize-y"
              placeholder="Enter first message..."
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="endCallMessage" className="text-tactical-green-light font-mono text-xs uppercase tracking-widest">
              End Call Message
            </Label>
            <textarea
              id="endCallMessage"
              value={formData.endCallMessage || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, endCallMessage: e.target.value }))}
              className="w-full min-h-[80px] bg-tactical-black border border-tactical-green/30 text-white font-mono text-sm p-3 rounded-md resize-y"
              placeholder="Enter end call message..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Functions */}
      {formData.functions.length > 0 && (
        <Card className="bg-tactical-black/50 border-tactical-green/30">
          <CardHeader>
            <CardTitle className="text-tactical-gold font-tactical uppercase tracking-wider">
              Available Functions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {formData.functions.map((func) => (
                <div
                  key={func.name}
                  className="flex items-center justify-between p-3 bg-tactical-black/30 border border-tactical-green/20 rounded"
                >
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      id={func.name}
                      checked={func.enabled !== false}
                      onCheckedChange={() => toggleFunction(func.name)}
                      className="border-tactical-green data-[state=checked]:bg-tactical-green"
                    />
                    <div>
                      <Label
                        htmlFor={func.name}
                        className="text-white font-mono text-sm cursor-pointer"
                      >
                        {func.name}
                      </Label>
                      <p className="text-xs text-gray-400 font-mono">{func.description}</p>
                    </div>
                  </div>
                  <Badge
                    variant={func.enabled !== false ? "default" : "outline"}
                    className={func.enabled !== false ? "bg-tactical-green text-white" : "border-tactical-green/30 text-tactical-green"}
                  >
                    {func.enabled !== false ? "Enabled" : "Disabled"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-4 pt-4 border-t border-tactical-green/20">
        <Button
          type="button"
          variant="outline"
          onClick={handleReset}
          className="border-tactical-green/30 text-tactical-green hover:bg-tactical-green/10 font-mono"
          disabled={isLoading}
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          className="border-tactical-green/30 text-white hover:bg-tactical-black-light font-mono"
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          className="bg-tactical-green hover:bg-tactical-green-light text-white font-tactical font-semibold"
          disabled={isLoading}
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </form>
  )
}