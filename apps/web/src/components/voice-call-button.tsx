'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Phone, PhoneOff, Loader2 } from 'lucide-react'
import Vapi from '@vapi-ai/web'

/**
 * VoiceCallButton Component
 * 
 * Production-grade voice UI component for initiating and managing
 * voice calls with AI agents via Vapi.ai integration.
 * 
 * @component
 * @example
 * ```tsx
 * <VoiceCallButton
 *   agent_id="bdr-concierge"
 *   agent_name="BDR Concierge"
 *   call_sign="ALPHA-1"
 *   vapi_assistant_id="your-vapi-assistant-id"
 * />
 * ```
 */

export interface VoiceCallButtonProps {
  /** Unique identifier for the agent */
  agent_id: string
  /** Display name of the agent */
  agent_name: string
  /** Military call sign (e.g., "ALPHA-1") */
  call_sign: string
  /** Vapi assistant ID for voice connection */
  vapi_assistant_id: string
  /** Optional callback when call starts */
  onCallStart?: () => void
  /** Optional callback when call ends */
  onCallEnd?: () => void
  /** Optional callback for errors */
  onError?: (error: Error) => void
}

type CallState = 'idle' | 'connecting' | 'active' | 'ended' | 'error'

export function VoiceCallButton({
  agent_id,
  agent_name,
  call_sign,
  vapi_assistant_id,
  onCallStart,
  onCallEnd,
  onError
}: VoiceCallButtonProps) {
  const [callState, setCallState] = useState<CallState>('idle')
  const [callDuration, setCallDuration] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const vapiRef = useRef<Vapi | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const callStartTimeRef = useRef<number | null>(null)

  // Initialize Vapi client
  useEffect(() => {
    const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY
    
    if (!publicKey) {
      console.error('VAPI_PUBLIC_KEY not configured')
      setErrorMessage('Voice service not configured')
      return
    }

    try {
      vapiRef.current = new Vapi(publicKey)
      
      // Set up event listeners
      vapiRef.current.on('call-start', handleCallStart)
      vapiRef.current.on('call-end', handleCallEnd)
      vapiRef.current.on('error', handleError)
      vapiRef.current.on('message', handleMessage)
    } catch (error) {
      console.error('Failed to initialize Vapi:', error)
      setErrorMessage('Voice service initialization failed')
      if (onError && error instanceof Error) {
        onError(error)
      }
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

  // Handle call start event
  const handleCallStart = () => {
    setCallState('active')
    setErrorMessage(null)
    callStartTimeRef.current = Date.now()
    
    // Start duration timer
    timerRef.current = setInterval(() => {
      if (callStartTimeRef.current) {
        const duration = Math.floor((Date.now() - callStartTimeRef.current) / 1000)
        setCallDuration(duration)
      }
    }, 1000)
    
    if (onCallStart) {
      onCallStart()
    }
  }

  // Handle call end event
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
    }, 2000)
    
    if (onCallEnd) {
      onCallEnd()
    }
  }

  // Handle error event
  const handleError = (error: any) => {
    console.error('Vapi error:', error)
    setCallState('error')
    setErrorMessage(error?.message || 'Call failed')
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    
    // Reset to idle after 3 seconds
    setTimeout(() => {
      setCallState('idle')
      setErrorMessage(null)
      setCallDuration(0)
    }, 3000)
    
    if (onError && error instanceof Error) {
      onError(error)
    }
  }

  // Handle message event (for debugging/logging)
  const handleMessage = (message: any) => {
    console.log('Vapi message:', message)
  }

  // Start call handler
  const startCall = async () => {
    if (!vapiRef.current || !vapi_assistant_id) {
      setErrorMessage('Voice service not ready')
      return
    }

    setCallState('connecting')
    setErrorMessage(null)

    try {
      await vapiRef.current.start(vapi_assistant_id)
    } catch (error: any) {
      console.error('Failed to start call:', error)
      handleError(error)
    }
  }

  // End call handler
  const endCall = () => {
    if (vapiRef.current) {
      vapiRef.current.stop()
    }
  }

  // Format call duration as MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Render based on call state
  const renderButton = () => {
    switch (callState) {
      case 'connecting':
        return (
          <Button
            size="sm"
            disabled
            className="flex-1 bg-tactical-gold/50 hover:bg-tactical-gold/50 text-white font-mono uppercase text-xs"
          >
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            CONNECTING...
          </Button>
        )

      case 'active':
        return (
          <div className="flex-1 flex items-center gap-2">
            <Button
              size="sm"
              onClick={endCall}
              className="flex-1 bg-terminal-red hover:bg-terminal-red/80 text-white font-mono uppercase text-xs"
            >
              <PhoneOff className="w-4 h-4 mr-2" />
              HANG UP
            </Button>
            <Badge className="bg-terminal-green/20 text-terminal-green border-terminal-green/30 animate-pulse">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-terminal-green rounded-full animate-pulse" />
                <span className="font-mono text-xs">{formatDuration(callDuration)}</span>
              </div>
            </Badge>
          </div>
        )

      case 'ended':
        return (
          <Button
            size="sm"
            disabled
            className="flex-1 bg-tactical-blue/50 hover:bg-tactical-blue/50 text-white font-mono uppercase text-xs"
          >
            CALL ENDED
          </Button>
        )

      case 'error':
        return (
          <Button
            size="sm"
            disabled
            className="flex-1 bg-terminal-red/50 hover:bg-terminal-red/50 text-white font-mono uppercase text-xs"
          >
            {errorMessage || 'CALL FAILED'}
          </Button>
        )

      default: // idle
        return (
          <Button
            size="sm"
            onClick={startCall}
            className="flex-1 bg-tactical-green hover:bg-tactical-green-light text-white font-mono uppercase text-xs"
            aria-label={`Call ${call_sign}`}
          >
            <Phone className="w-4 h-4 mr-2" />
            📞 CALL {call_sign}
          </Button>
        )
    }
  }

  return <div className="flex w-full">{renderButton()}</div>
}