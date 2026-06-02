/**
 * Spec 42 §3.19–§3.20 / §4.17 — Prompt Library + Story Bank API client.
 *
 * The student-facing behavioral practice surface: the canonical prompt catalog,
 * per-prompt responses (with system-derived STAR/impact flags), a reusable story
 * bank, and the §4.17 inference summary. Mirrors
 * unipaith-backend/src/unipaith/api/prompt_library.py.
 */
import apiClient from './client'
import type {
  BehavioralPrompt,
  BehavioralResponse,
  BehavioralResponseUpsert,
  PromptLibrarySummary,
  Story,
  StoryInput,
} from '../types/promptLibrary'

const BASE = '/students/me/prompt-library'

export const listPrompts = (params?: {
  intent?: string
  channel?: string
}): Promise<BehavioralPrompt[]> =>
  apiClient.get(`${BASE}/prompts`, { params }).then(r => r.data)

export const listResponses = (): Promise<BehavioralResponse[]> =>
  apiClient.get(`${BASE}/responses`).then(r => r.data)

export const upsertResponse = (
  promptKey: string,
  body: BehavioralResponseUpsert,
): Promise<BehavioralResponse> =>
  apiClient.put(`${BASE}/responses/${promptKey}`, body).then(r => r.data)

export const listStories = (): Promise<Story[]> =>
  apiClient.get(`${BASE}/stories`).then(r => r.data)

export const createStory = (body: StoryInput): Promise<Story> =>
  apiClient.post(`${BASE}/stories`, body).then(r => r.data)

export const updateStory = (storyId: string, body: StoryInput): Promise<Story> =>
  apiClient.put(`${BASE}/stories/${storyId}`, body).then(r => r.data)

export const deleteStory = (storyId: string): Promise<void> =>
  apiClient.delete(`${BASE}/stories/${storyId}`).then(() => undefined)

export const getSummary = (): Promise<PromptLibrarySummary> =>
  apiClient.get(`${BASE}/summary`).then(r => r.data)
