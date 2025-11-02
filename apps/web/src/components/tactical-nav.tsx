'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Badge } from '@/components/ui/badge'

interface NavItem {
  href: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { href: '/', label: 'Command Center', icon: '⌘' },
  { href: '/agents', label: 'Agent Roster', icon: '⚡' },
  { href: '/logs', label: 'Mission Logs', icon: '📋' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
]

interface TacticalNavProps {
  isOnline?: boolean
}

export function TacticalNav({ isOnline = true }: TacticalNavProps) {
  const pathname = usePathname()

  return (
    <nav className="border-b border-tactical-green/20 bg-tactical-black-light/80 backdrop-blur-sm">
      <div className="container flex items-center gap-1 h-12 overflow-x-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-2 px-4 py-2 font-tactical text-sm uppercase tracking-wider
                transition-all duration-200 whitespace-nowrap
                border-b-2 hover:border-tactical-green/50
                ${
                  isActive
                    ? 'border-tactical-green text-tactical-green terminal-glow'
                    : 'border-transparent text-gray-400 hover:text-tactical-green'
                }
              `}
            >
              <span className="text-base" aria-hidden="true">
                {item.icon}
              </span>
              <span className="hidden md:inline">{item.label}</span>
            </Link>
          )
        })}
        
        {/* Connection Status Indicator */}
        <div className="ml-auto flex items-center gap-2 px-2">
          <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-terminal-green' : 'bg-terminal-red'} animate-pulse`} />
          <span className={`font-mono text-xs uppercase ${isOnline ? 'text-terminal-green' : 'text-terminal-red'}`}>
            {isOnline ? 'LINK' : 'LOST'}
          </span>
        </div>
      </div>
    </nav>
  )
}