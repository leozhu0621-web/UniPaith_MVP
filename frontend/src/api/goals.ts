/**
 * Phase A — Student goals (SMART stack) API client.
 */
import apiClient from './client'
import type {
  GoalCategory,
  GoalSource,
  GoalStatus,
  StudentGoal,
} from '../types'

const BASE = '/students/me/goals'

export interface CreateGoalBody {
  category: GoalCategory
  specific: string
  measurable?: string | null
  achievable_notes?: string | null
  relevant_notes?: string | null
  time_bound?: string | null
  status?: GoalStatus
  source?: GoalSource
  source_session_id?: string | null
  confidence?: string | number | null
}

export interface UpdateGoalBody {
  category?: GoalCategory
  specific?: string
  measurable?: string | null
  achievable_notes?: string | null
  relevant_notes?: string | null
  time_bound?: string | null
  status?: GoalStatus
  confidence?: string | number | null
}

export const listGoals = (status?: GoalStatus): Promise<StudentGoal[]> =>
  apiClient.get(BASE, { params: status ? { status } : undefined }).then(r => r.data)

export const createGoal = (body: CreateGoalBody): Promise<StudentGoal> =>
  apiClient.post(BASE, body).then(r => r.data)

export const updateGoal = (id: string, body: UpdateGoalBody): Promise<StudentGoal> =>
  apiClient.put(`${BASE}/${id}`, body).then(r => r.data)

export const deleteGoal = (id: string): Promise<void> =>
  apiClient.delete(`${BASE}/${id}`).then(() => undefined)

export type { GoalCategory, GoalSource, GoalStatus, StudentGoal }
