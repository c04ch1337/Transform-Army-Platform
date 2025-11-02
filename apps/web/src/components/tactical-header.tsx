'use client'

import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'

interface TacticalHeaderProps {
  title: string
  subtitle?: string
  badge?: string
  isOnline?: boolean
}

export function TacticalHeader({ 
  title, 
  subtitle, 
  badge,
  isOnline = true 
}: TacticalHeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>('')

  // Update clock every second
  useEffect(() => {
    const updateClock = () => {
      setCurrentTime(
        new Date().toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
        })
      )
    }
    updateClock()
    const interval = setInterval(updateClock, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="border-b border-tactical-green/20 bg-tactical-black-light">
      <div className="container flex h-16 items-center gap-4">
        <h1 className="text-2xl font-tactical font-bold text-tactical-gold uppercase tracking-wider">
          {title}
        </h1>
        
        {badge && (
          <Badge variant="outline" className="hexagon border-tactical-green text-tactical-green">
            {badge}
          </Badge>
        )}
        
        {subtitle && (
          <span className="hidden md:inline font-mono text-xs text-tactical-green-light uppercase tracking-widest">
            {subtitle}
          </span>
        )}
        
        {/* Connection Status Badge */}
        <Badge
          variant={isOnline ? 'default' : 'destructive'}
          className={`ml-2 ${isOnline ? 'bg-terminal-green text-black' : ''}`}
        >
          {isOnline ? '● CONNECTED' : '● OFFLINE MODE'}
        </Badge>

        <div className="ml-auto flex items-center gap-2">
          <span className="military-time text-tactical-green">
            {currentTime} ZULU
          </span>
        </div>
      </div>
    </header>
  )
}