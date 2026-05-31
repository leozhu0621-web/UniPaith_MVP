import apiClient from './client'
import { toArrayData } from './normalize'
import type {
  ComparisonResponse,
  SavedPriority,
  SavedProgram,
  StartApplicationResponse,
} from '../types'

export const listSaved = () =>
  apiClient.get('/students/me/saved').then(r => toArrayData<SavedProgram>(r.data))

export const saveProgram = (programId: string, notes?: string) =>
  apiClient
    .post('/students/me/saved', { program_id: programId, notes })
    .then(r => r.data as SavedProgram)

export const unsaveProgram = (programId: string) =>
  apiClient.delete(`/students/me/saved/${programId}`)

export interface SavedPatch {
  priority?: SavedPriority
  notes?: string
  tags?: string[]
}

// Spec 13 §4.2 (priority — closes G-S5) / §4.3 (tags & notes). Partial update.
export const updateSaved = (programId: string, patch: SavedPatch) =>
  apiClient.patch(`/students/me/saved/${programId}`, patch).then(r => r.data as SavedProgram)

// Legacy notes-only update — kept for back-compat (prefer updateSaved).
export const updateSavedNotes = (programId: string, notes: string) =>
  apiClient
    .put(`/students/me/saved/${programId}/notes`, { notes })
    .then(r => r.data as SavedProgram)

// Spec 13 §6 — one-click conversion of a saved program to an application.
export const startApplication = (programId: string) =>
  apiClient
    .post(`/students/me/saved/${programId}/start-application`)
    .then(r => r.data as StartApplicationResponse)

export const comparePrograms = (programIds: string[]) =>
  apiClient
    .post('/students/me/saved/compare', { program_ids: programIds })
    .then(r => r.data as ComparisonResponse)
