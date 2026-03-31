import apiClient from './client'

export const listSaved = () =>
  apiClient.get('/students/me/saved').then(r => r.data)

export const saveProgram = (programId: string, notes?: string) =>
  apiClient.post('/students/me/saved', { program_id: programId, notes }).then(r => r.data)

export const unsaveProgram = (programId: string) =>
  apiClient.delete(`/students/me/saved/${programId}`)

export const updateSavedNotes = (programId: string, notes: string) =>
  apiClient.put(`/students/me/saved/${programId}/notes`, { notes }).then(r => r.data)

export const comparePrograms = (programIds: string[]) =>
  apiClient.post('/students/me/saved/compare', { program_ids: programIds }).then(r => r.data)
