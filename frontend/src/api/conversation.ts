import apiClient from './client'
import type {
  ConfidenceReport,
  ConversationRequirement,
  ConversationSession,
  ConversationTurnRequest,
  ConversationTurnResponse,
  ResolveConversationConflictRequest,
  ResolveConversationConflictResponse,
  ResumeCheckpoint,
  ShortlistUnlockReport,
  UpdateConversationRequirementRequest,
} from '../types'

export async function sendConversationTurn(payload: ConversationTurnRequest): Promise<ConversationTurnResponse> {
  const { data } = await apiClient.post<ConversationTurnResponse>('/students/me/conversation/turn', payload)
  return data
}

export async function getConversationSession(): Promise<ConversationSession> {
  const { data } = await apiClient.get<ConversationSession>('/students/me/conversation/session')
  return data
}

export async function getConversationResumeCheckpoint(): Promise<ResumeCheckpoint> {
  const { data } = await apiClient.get<ResumeCheckpoint>('/students/me/conversation/session')
  return data
}

export async function listConversationRequirements(): Promise<ConversationRequirement[]> {
  const { data } = await apiClient.get<{ requirements: ConversationRequirement[] }>(
    '/students/me/conversation/requirements',
  )
  return data.requirements
}

export async function updateConversationRequirement(
  requirementId: string,
  payload: UpdateConversationRequirementRequest,
): Promise<ConversationRequirement> {
  const { data } = await apiClient.patch<ConversationRequirement>(
    `/students/me/conversation/requirements/${requirementId}`,
    payload,
  )
  return data
}

export async function getConversationConfidenceReport(): Promise<ConfidenceReport> {
  const { data } = await apiClient.get<ConfidenceReport>('/students/me/conversation/confidence')
  return data
}

export async function getShortlistUnlockReport(): Promise<ShortlistUnlockReport> {
  const { data } = await apiClient.get<ShortlistUnlockReport>('/students/me/conversation/shortlist-unlock')
  return data
}

export async function resolveConversationConflict(
  conflictId: string,
  payload: ResolveConversationConflictRequest,
): Promise<ResolveConversationConflictResponse> {
  const { data } = await apiClient.post<ResolveConversationConflictResponse>(
    `/students/me/conversation/conflicts/${conflictId}/resolve`,
    payload,
  )
  return data
}
