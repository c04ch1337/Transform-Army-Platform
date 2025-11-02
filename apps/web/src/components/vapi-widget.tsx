'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Mic, X, Phone, Shield } from 'lucide-react'
import Vapi from '@vapi-ai/web'
import { Agent } from '@/types'

/**
 * VapiWidget Component
 * 
 * Global floating voice assistant widget that provides quick access
 * to call any AI agent. Appears as a fixed bottom-right button that
 * opens a modal selector for all available agents.
 * 
 * @component
 * @example
 * ```tsx
 * <VapiWidget agents={agentsList} />
 * ```
 */

export interface VapiWidgetProps {
  /** List of available agents to call */
  agents: Agent[]
  /** Optional position override (default: bottom-right) */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}

interface AgentCallData {
  agent_id: string
  call_sign: string
  name: string
  vapi_assistant_id: string
  status: string
}

type CallState = 'idle' | 'connecting' | 'active' | 'ended'

export function VapiWidget({ 
  agents, 
  position = 'bottom-right' 
}: VapiWidgetProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [callState, setCallState] = useState<CallState>('idle')
  const [activeAgent, setActiveAgent] = useState<AgentCallData | null>(null)
  const [callDuration, setCallDuration] = useState(0)
  const vapiRef = useRef<Vapi | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const callStartTimeRef = useRef<number | null>(null)

  // Mock agent metadata with call signs and Vapi IDs
  const AGENT_METADATA: Record<string, { callSign: string; vapiId: string }> = {
    'bdr-concierge': { callSign: 'ALPHA-1', vapiId: process.env.NEXT_PUBLIC_VAPI_BDR_ASSISTANT_ID || 'demo-bdr' },
    'support-concierge': { callSign: 'ALPHA-2', vapiId: process.env.NEXT_PUBLIC_VAPI_SUPPORT_ASSISTANT_ID || 'demo-support' },
    'research-recon': { callSign: 'BRAVO-1', vapiId: process.env.NEXT_PUBLIC_VAPI_RESEARCH_ASSISTANT_ID || 'demo-research' },
    'ops-sapper': { callSign: 'BRAVO-2', vapiId: process.env.NEXT_PUBLIC_VAPI_OPS_ASSISTANT_ID || 'demo-ops' },
    'knowledge-librarian': { callSign: 'CHARLIE-1', vapiId: process.env.NEXT_PUBLIC_VAPI_KNOWLEDGE_ASSISTANT_ID || 'demo-knowledge' },
    'qa-auditor': { callSign: 'CHARLIE-2', vapiId: process.env.NEXT_PUBLIC_VAPI_QA_ASSISTANT_ID || 'demo-qa' }
  }

  // Initialize Vapi client
  useEffect(() => {
    const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY
    
    if (!publicKey) {
      console.warn('VAPI_PUBLIC_KEY not configured')
      return
    }

    try {
      vapiRef.current = new Vapi(publicKey)
      
      // Set up event listeners
      vapiRef.current.on('call-start', handleCallStart)
      vapiRef.current.on('call-end', handleCallEnd)
      vapiRef.current.on('error', handleError)
    } catch (error) {
      console.error('Failed to initialize Vapi:', error)
    }

    // Cleanup on unmount
    return () => {
      if (vapiRef.current) {
        vapiRef.current.stop()
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  // Handle call start
  const handleCallStart = () => {
    setCallState('active')
    callStartTimeRef.current = Date.now()
    
    // Start duration timer
    timerRef.current = setInterval(() => {
      if (callStartTimeRef.current) {
        const duration = Math.floor((Date.now() - callStartTimeRef.current) / 1000)
        setCallDuration(duration)
      }
    }, 1000)
  }

  // Handle call end
  const handleCallEnd = () => {
    setCallState('ended')
    callStartTimeRef.current = null
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    
    // Reset to idle after 2 seconds
    setTimeout(() => {
      setCallState('idle')
      setCallDuration(0)
      setActiveAgent(null)
    }, 2000)
  }

  // Handle error
  const handleError = (error: any) => {
    console.error('Vapi error:', error)
    setCallState('idle')
    setActiveAgent(null)
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  // Start call with selected agent
  const initiateCall = async (agent: Agent) => {
    if (!vapiRef.current) {
      console.error('Vapi not initialized')
      return
    }

    const metadata = AGENT_METADATA[agent.agent_id]
    if (!metadata) {
      console.error('Agent metadata not found')
      return
    }

    setActiveAgent({
      agent_id: agent.agent_id,
      call_sign: metadata.callSign,
      name: agent.name,
      vapi_assistant_id: metadata.vapiId,
      status: agent.status
    })

    setCallState('connecting')
    setIsModalOpen(false)

    try {
      await vapiRef.current.start(metadata.vapiId)
    } catch (error: any) {
      console.error('Failed to start call:', error)
      handleError(error)
    }
  }

  // End active call
  const endCall = () => {
    if (vapiRef.current) {
      vapiRef.current.stop()
    }
  }

  // Format duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Get position classes
  const getPositionClasses = () => {
    switch (position) {
      case 'bottom-left':
        return 'bottom-6 left-6'
      case 'top-right':
        return 'top-6 right-6'
      case 'top-left':
        return 'top-6 left-6'
      default: // bottom-right
        return 'bottom-6 right-6'
    }
  }

  // Get squad color
  const getSquadColor = (squad: string) => {
    if (squad.includes('sales')) return 'border-l-tactical-green'
    if (squad.includes('support')) return 'border-l-tactical-gold'
    return 'border-l-tactical-blue'
  }

  return (
    <>
      {/* Floating Action Button */}
      <div className={`fixed ${getPositionClasses()} z-50`}>
        {callState === 'active' && activeAgent ? (
          <div className="flex flex-col items-end gap-2">
            <Card className="bg-tactical-black border-terminal-green shadow-2xl">
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <Badge className="bg-terminal-green/20 text-terminal-green border-terminal-green/30 animate-pulse">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-terminal-green rounded-full animate-pulse" />
                      <span className="font-mono text-xs">ACTIVE</span>
                    </div>
                  </Badge>
                  <div>
                    <p className="font-tactical text-sm text-tactical-gold uppercase">
                      {activeAgent.call_sign}
                    </p>
                    <p className="font-mono text-xs text-gray-400">{formatDuration(callDuration)}</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={endCall}
                    className="bg-terminal-red hover:bg-terminal-red/80 text-white"
                  >
                    END
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Button
            onClick={() => setIsModalOpen(true)}
            size="lg"
            className="h-14 w-14 rounded-full bg-tactical-green hover:bg-tactical-green-light text-white shadow-2xl transition-all hover:scale-110"
            aria-label="Talk to Command"
          >
            <Mic className="w-6 h-6" />
          </Button>
        )}
      </div>

      {/* Agent Selector Modal */}
      {isModalOpen && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setIsModalOpen(false)}
        >
          <Card 
            className="bg-tactical-black border-tactical-green/50 max-w-2xl w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="border-b border-tactical-green/30">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="font-tactical text-2xl text-tactical-green uppercase">
                    Select Agent to Call
                  </CardTitle>
                  <p className="font-mono text-sm text-gray-400 mt-1">
                    Choose an AI agent to initiate voice communication
                  </p>
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setIsModalOpen(false)}
                  className="text-gray-400 hover:text-terminal-red"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="p-4 max-h-[60vh] overflow-y-auto">
              <div className="space-y-2">
                {agents.map((agent) => {
                  const metadata = AGENT_METADATA[agent.agent_id]
                  if (!metadata) return null

                  const isActive = agent.status === 'active'
                  const isAvailable = isActive && callState === 'idle'

                  return (
                    <button
                      key={agent.agent_id}
                      onClick={() => isAvailable && initiateCall(agent)}
                      disabled={!isAvailable}
                      className={`w-full text-left transition-all ${
                        isAvailable
                          ? 'hover:bg-tactical-green/10 cursor-pointer'
                          : 'opacity-50 cursor-not-allowed'
                      }`}
                    >
                      <Card className={`bg-tactical-black-light border-l-4 ${getSquadColor(agent.role.squad)}`}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 flex-1">
                              <Shield className="w-5 h-5 text-tactical-gold" />
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-tactical text-lg text-tactical-gold uppercase">
                                    {metadata.callSign}
                                  </span>
                                  <Badge 
                                    variant="outline"
                                    className={`text-xs font-mono uppercase ${
                                      isActive 
                                        ? 'border-terminal-green text-terminal-green' 
                                        : 'border-gray-600 text-gray-600'
                                    }`}
                                  >
                                    {agent.status}
                                  </Badge>
                                </div>
                                <p className="font-mono text-sm text-tactical-green">
                                  {agent.name}
                                </p>
                                <p className="font-mono text-xs text-gray-500 mt-1">
                                  {agent.description}
                                </p>
                              </div>
                            </div>
                            {isAvailable && (
                              <Button
                                size="sm"
                                className="bg-tactical-green hover:bg-tactical-green-light text-white font-mono uppercase"
                              >
                                <Phone className="w-4 h-4 mr-2" />
                                CALL
                              </Button>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </button>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}