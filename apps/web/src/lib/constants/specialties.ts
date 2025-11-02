/**
 * Military Occupational Specialties (MOS) for Transform Army AI agents
 */

export enum AgentSpecialty {
  COMBAT_ENGINEER = '12B',
  INTELLIGENCE_ANALYST = '35F',
  IT_SPECIALIST = '25B',
  SUPPLY_SPECIALIST = '92Y',
  HR_SPECIALIST = '42A',
  PSYOPS = '37F'
}

export interface SpecialtyInfo {
  code: string
  name: string
  branch: string
  category: 'combat' | 'intelligence' | 'support' | 'technical'
  color: string
  icon: string  // Lucide icon name
}

export const SPECIALTY_DATA: Record<AgentSpecialty, SpecialtyInfo> = {
  [AgentSpecialty.COMBAT_ENGINEER]: {
    code: '12B',
    name: 'Combat Engineer',
    branch: 'Combat Arms',
    category: 'combat',
    color: '#FF3B3B',
    icon: 'wrench'
  },
  [AgentSpecialty.INTELLIGENCE_ANALYST]: {
    code: '35F',
    name: 'Intelligence Analyst',
    branch: 'Military Intelligence',
    category: 'intelligence',
    color: '#00D9FF',
    icon: 'radar'
  },
  [AgentSpecialty.IT_SPECIALIST]: {
    code: '25B',
    name: 'Information Technology Specialist',
    branch: 'Signal Corps',
    category: 'technical',
    color: '#9333EA',
    icon: 'database'
  },
  [AgentSpecialty.SUPPLY_SPECIALIST]: {
    code: '92Y',
    name: 'Unit Supply Specialist',
    branch: 'Quartermaster Corps',
    category: 'support',
    color: '#10B981',
    icon: 'package'
  },
  [AgentSpecialty.HR_SPECIALIST]: {
    code: '42A',
    name: 'Human Resources Specialist',
    branch: 'Adjutant General Corps',
    category: 'support',
    color: '#3B82F6',
    icon: 'users'
  },
  [AgentSpecialty.PSYOPS]: {
    code: '37F',
    name: 'Psychological Operations Specialist',
    branch: 'Civil Affairs & Psychological Operations',
    category: 'intelligence',
    color: '#8B5CF6',
    icon: 'brain'
  }
}