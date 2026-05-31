import apiClient from './client'
import { toArrayData } from './normalize'
import type { ComparisonResponse, SavedProgram, SavedPriority } from '../types'

export const listSaved = () =>
  apiClient.get('/students/me/saved').then(r => toArrayData<SavedProgram>(r.data))

export const listSavedTagSuggestions = () =>
  apiClient.get('/students/me/saved/tags').then(r => toArrayData<string>(r.data))

export const saveProgram = (programId: string, notes?: string) =>
  apiClient.post('/students/me/saved', { program_id: programId, notes }).then(r => r.data as SavedProgram)

export const unsaveProgram = (programId: string): Promise<void> =>
  apiClient.delete(`/students/me/saved/${programId}`).then(() => {})

export const updateSavedNotes = (programId: string, notes: string) =>
  apiClient.put(`/students/me/saved/${programId}/notes`, { notes }).then(r => r.data as SavedProgram)

export const patchSavedProgram = (
  programId: string,
  body: { priority?: SavedPriority; notes?: string; tags?: string[] },
) =>
  apiClient.patch(`/students/me/saved/${programId}`, body).then(r => r.data as SavedProgram)

export const startApplicationFromSaved = (programId: string) =>
  apiClient
    .post(`/students/me/saved/${programId}/start-application`)
    .then(r => r.data as { app_id: string })

export const comparePrograms = (programIds: string[]) =>
  apiClient
    .post('/students/me/saved/compare', { program_ids: programIds })
    .then(r => r.data as ComparisonResponse)
