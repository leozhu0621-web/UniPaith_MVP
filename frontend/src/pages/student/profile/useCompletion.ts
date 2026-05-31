/**
 * Shared completion model for the Universal Profile (Spec/08 §3–§4, §18).
 *
 * Fetches the slices needed to compute per-cluster completion and the overall
 * ring value. All queries are react-query cached, so tabs that also read these
 * keys never double-fetch. Discovery artifacts (identity/goals/needs/strategy)
 * use `retry: false` so a brand-new student with no artifacts yet doesn't
 * error-spam — a missing artifact simply reads as 0% complete.
 */
import { useQuery } from '@tanstack/react-query'

import { getIdentity } from '../../../api/identity'
import { listGoals } from '../../../api/goals'
import { listNeeds } from '../../../api/needs'
import { getActiveStrategy } from '../../../api/strategy'
import {
  getAccommodations,
  getProfile,
  getScheduling,
  listCompetitions,
  listWorkExperiences,
} from '../../../api/students'
import { listDocuments } from '../../../api/documents'
import { computeCategoryStats, overallPct, type CategoryStat } from './shared'

export interface CompletionResult {
  stats: CategoryStat[]
  overall: number
  lastUpdated: string | null
  isLoading: boolean
}

export function useCompletion(): CompletionResult {
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const documents = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const work = useQuery({ queryKey: ['work-experiences'], queryFn: listWorkExperiences })
  const competitions = useQuery({ queryKey: ['competitions'], queryFn: listCompetitions })
  const accommodations = useQuery({ queryKey: ['accommodations'], queryFn: getAccommodations, retry: false })
  const scheduling = useQuery({ queryKey: ['scheduling'], queryFn: getScheduling, retry: false })
  const identity = useQuery({ queryKey: ['identity'], queryFn: getIdentity, retry: false })
  const goals = useQuery({ queryKey: ['goals'], queryFn: () => listGoals() })
  const needs = useQuery({ queryKey: ['needs'], queryFn: () => listNeeds() })
  const strategy = useQuery({ queryKey: ['strategy', 'active'], queryFn: getActiveStrategy, retry: false })

  const p: any = profile.data ?? null

  const stats = computeCategoryStats({
    profile: p,
    documents: Array.isArray(documents.data) ? documents.data : [],
    workExperiences: Array.isArray(work.data) ? work.data : [],
    competitions: Array.isArray(competitions.data) ? competitions.data : [],
    accommodations: accommodations.data ?? null,
    scheduling: scheduling.data ?? null,
    preferences: p?.preferences ?? null,
    dataConsent: p?.data_consent ?? null,
    identity: identity.data ?? null,
    goals: Array.isArray(goals.data) ? goals.data : [],
    needs: Array.isArray(needs.data) ? needs.data : [],
    strategy: strategy.data ?? null,
  })

  return {
    stats,
    overall: overallPct(stats),
    lastUpdated: p?.updated_at ?? null,
    isLoading: profile.isLoading,
  }
}
