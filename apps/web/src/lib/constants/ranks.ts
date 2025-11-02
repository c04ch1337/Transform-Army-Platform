/**
 * Military rank structure for Transform Army AI agents
 */

export enum MilitaryRank {
  // Enlisted ranks
  SPECIALIST = 'SPC',
  SERGEANT = 'SGT',
  STAFF_SERGEANT = 'SSG',
  SERGEANT_FIRST_CLASS = 'SFC',
  MASTER_SERGEANT = 'MSG',
  
  // Officer ranks (for future expansion)
  LIEUTENANT = 'LT',
  CAPTAIN = 'CPT',
  MAJOR = 'MAJ',
  COLONEL = 'COL'
}

export interface RankInfo {
  abbreviation: string
  fullName: string
  payGrade: string
  stripes: number
  color: string
}

export const RANK_DATA: Record<MilitaryRank, RankInfo> = {
  [MilitaryRank.SPECIALIST]: {
    abbreviation: 'SPC',
    fullName: 'Specialist',
    payGrade: 'E-4',
    stripes: 2,
    color: '#FFB800'
  },
  [MilitaryRank.SERGEANT]: {
    abbreviation: 'SGT',
    fullName: 'Sergeant',
    payGrade: 'E-5',
    stripes: 3,
    color: '#FFB800'
  },
  [MilitaryRank.STAFF_SERGEANT]: {
    abbreviation: 'SSG',
    fullName: 'Staff Sergeant',
    payGrade: 'E-6',
    stripes: 3,
    color:  '#FFB800'
  },
  [MilitaryRank.SERGEANT_FIRST_CLASS]: {
    abbreviation: 'SFC',
    fullName: 'Sergeant First Class',
    payGrade: 'E-7',
    stripes: 3,
    color: '#FFB800'
  },
  [MilitaryRank.MASTER_SERGEANT]: {
    abbreviation: 'MSG',
    fullName: 'Master Sergeant',
    payGrade: 'E-8',
    stripes: 3,
    color: '#FFB800'
  },
  [MilitaryRank.LIEUTENANT]: {
    abbreviation: 'LT',
    fullName: 'Lieutenant',
    payGrade: 'O-2',
    stripes: 1,
    color: '#00D9FF'
  },
  [MilitaryRank.CAPTAIN]: {
    abbreviation: 'CPT',
    fullName: 'Captain',
    payGrade: 'O-3',
    stripes: 2,
    color: '#00D9FF'
  },
  [MilitaryRank.MAJOR]: {
    abbreviation: 'MAJ',
    fullName: 'Major',
    payGrade: 'O-4',
    stripes: 1,
    color: '#4A7C59'
  },
  [MilitaryRank.COLONEL]: {
    abbreviation: 'COL',
    fullName: 'Colonel',
    payGrade: 'O-6',
    stripes: 1,
    color: '#4A7C59'
  }
}