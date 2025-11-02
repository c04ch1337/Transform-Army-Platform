'use client'

import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Mic, MicOff, PhoneOff } from 'lucide-react'

/**
 * CallStatus Component
 * 
 * Compact status indicator showing live call state, duration, and controls
 * for mute/unmute and hang up functionality.
 * 
 * @component
 * @example
 * ```tsx
 * <CallStatus
 *   isActive={true}
 *   duration={125}
 *   isMuted={false}
 *   onMuteToggle={() => {}}
 *   onHangup={() => {}}
 * />
 * ```
 */

export interface CallStatusProps {
  /** Whether a call is currently active */
  isActive: boolean
  /** Call duration in seconds */
  duration?: number
  /** Whether the microphone is muted */
  isMuted?: boolean
  /** Callback to toggle mute state */
  onMuteToggle?: () => void
  /** Callback to hang up the call */
  onHangup?: () => void
  /** Optional agent call sign for display */
  callSign?: string
}

export function CallStatus({
  isActive,
  duration = 0,
  isMuted = false,
  onMuteToggle,
  onHangup,
  callSign
}: CallStatusProps) {
  // Format duration as MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (!isActive) {
    return (
      <div className="flex items-center gap-2">
        <Badge 
          variant="outline" 
          className="bg-tactical-black/50 border-gray-600 text-gray-500 font-mono text-xs uppercase"
        >
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-gray-500 rounded-full" />
            <span>IDLE</span>
          </div>
        </Badge>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant="outline"
        className="bg-terminal-green/10 border-terminal-green text-terminal-green font-mono text-xs uppercase animate-pulse"
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-terminal-green rounded-full animate-pulse" />
          <span>ACTIVE</span>
        </div>
      </Badge>

      <Badge 
        variant="outline"
        className="bg-tactical-black/50 border-terminal-green/30 text-terminal-green font-mono text-xs"
      >
        {formatDuration(duration)}
      </Badge>

      {callSign && (
        <Badge 
          variant="outline"
          className="bg-tactical-black/50 border-tactical-gold/30 text-tactical-gold font-mono text-xs uppercase"
        >
          {callSign}
        </Badge>
      )}

      {onMuteToggle && (
        <Button
          size="icon"
          variant="outline"
          onClick={onMuteToggle}
          className={`h-7 w-7 ${
            isMuted 
              ? 'border-terminal-red text-terminal-red hover:bg-terminal-red/20' 
              : 'border-tactical-blue text-tactical-blue hover:bg-tactical-blue/20'
          }`}
          aria-label={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? (
            <MicOff className="w-4 h-4" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </Button>
      )}

      {onHangup && (
        <Button
          size="icon"
          variant="outline"
          onClick={onHangup}
          className="h-7 w-7 border-terminal-red text-terminal-red hover:bg-terminal-red/20"
          aria-label="Hang up"
        >
          <PhoneOff className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}

/**
 * CallStatusIndicator Component
 * 
 * Minimal status badge showing only call state without controls.
 * Useful for compact displays or read-only views.
 * 
 * @component
 */
export interface CallStatusIndicatorProps {
  /** Whether a call is currently active */
  isActive: boolean
  /** Optional label override */
  label?: string
}

export function CallStatusIndicator({ 
  isActive, 
  label 
}: CallStatusIndicatorProps) {
  if (!isActive) {
    return (
      <Badge 
        variant="outline" 
        className="bg-tactical-black/50 border-gray-600 text-gray-500 font-mono text-xs uppercase"
      >
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 bg-gray-500 rounded-full" />
          <span>{label || 'IDLE'}</span>
        </div>
      </Badge>
    )
  }

  return (
    <Badge 
      variant="outline"
      className="bg-terminal-green/10 border-terminal-green text-terminal-green font-mono text-xs uppercase"
    >
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 bg-terminal-green rounded-full animate-pulse" />
        <span>{label || 'LIVE'}</span>
      </div>
    </Badge>
  )
}