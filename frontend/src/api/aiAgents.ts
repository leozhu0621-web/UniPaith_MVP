// Spec 45 — public AI agent catalog client. No auth required; the endpoint
// exposes only the agent architecture, never user data.
import apiClient from './client'
import type { AiAgentCatalog } from '../types/aiAgents'

export async function getAiAgents(): Promise<AiAgentCatalog> {
  const { data } = await apiClient.get<AiAgentCatalog>('/ai/agents')
  return data
}
