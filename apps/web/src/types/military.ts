/**
 * Type definitions for military/hacker theme
 */

import { MilitaryRank } from '@/lib/constants/ranks'
import { AgentSpecialty } from '@/lib/constants/specialties'

export interface MilitaryProfile {
  callSign: string
  rank: MilitaryRank
  mos: AgentSpecialty
  unit: string
  clearanceLevel: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET'
}

export interface AgentProfile {
  id: string
  name: string
  military: MilitaryProfile
  status: 'ACTIVE' | 'STANDBY' | 'OFFLINE'
  lastMission?: string
  missionsCompleted: number
  successRate: number
}

export interface Squad {
  name: string
  designation: 'ALPHA' | 'BRAVO' | 'CHARLIE'
  agents: AgentProfile[]
  commander?: AgentProfile
  status: 'OPERATIONAL' | 'STANDBY' | 'DEGRADED'
}

export interface Mission {
  id: string
  codename: string
  type: string
  status: 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILURE'
  assignedAgent: string
  startTime: string
  endTime?: string
  objective: string
}