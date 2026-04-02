import apiClient from './client'
import { toArrayData } from './normalize'

export const getMatches = (forceRefresh = false) =>
  apiClient.get('/students/me/matches', { params: { force_refresh: forceRefresh } }).then(r => toArrayData<any>(r.data))

export const getMatchDetail = (programId: string) =>
  apiClient.get(`/students/me/matches/${programId}`).then(r => r.data)

export const logEngagement = (programId: string, signalType: string, signalValue: number) =>
  apiClient.post('/students/me/engagement', { program_id: programId, signal_type: signalType, signal_value: signalValue }).then(r => r.data)

export const chatStudentAssistant = (message: string, contextProgramId?: string) =>
  apiClient
    .post('/students/me/assistant/chat', {
      message,
      context_program_id: contextProgramId,
    })
    .then(r => r.data)
