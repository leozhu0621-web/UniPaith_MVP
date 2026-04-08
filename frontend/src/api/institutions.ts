import apiClient from './client'
import type { AnalyticsData, Campaign, CampaignMetrics, DashboardSummary, DatasetPreview, Institution, InstitutionDataset, Program, Segment } from '../types'

export async function getInstitution(): Promise<Institution> {
  const { data } = await apiClient.get('/institutions/me')
  return data
}

export async function getPublicInstitution(institutionId: string): Promise<Institution> {
  const { data } = await apiClient.get(`/institutions/${institutionId}`)
  return data
}

export async function createInstitution(payload: {
  name: string; type: string; country: string; region?: string; city?: string;
  website_url?: string; description_text?: string; logo_url?: string
}): Promise<Institution> {
  const { data } = await apiClient.post('/institutions/me', payload)
  return data
}

export async function updateInstitution(payload: Partial<{
  name: string; type: string; country: string; region: string; city: string;
  website_url: string; description_text: string; logo_url: string
}>): Promise<Institution> {
  const { data } = await apiClient.put('/institutions/me', payload)
  return data
}

export async function getInstitutionPrograms(): Promise<Program[]> {
  const { data } = await apiClient.get('/institutions/me/programs')
  return data
}

export async function getInstitutionProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.get(`/institutions/me/programs/${programId}`)
  return data
}

export async function createProgram(payload: {
  program_name: string; degree_type: string; department?: string;
  duration_months?: number; tuition?: number; acceptance_rate?: number;
  delivery_format?: string; campus_setting?: string;
  requirements?: Record<string, any>; application_requirements?: Record<string, any>[];
  description_text?: string; who_its_for?: string;
  application_deadline?: string; program_start_date?: string;
  tracks?: string[]; outcomes_data?: Record<string, any>;
  intake_rounds?: Record<string, any>[]; media_urls?: string[];
  highlights?: string[]; faculty_contacts?: { name: string; email?: string; role?: string }[]
}): Promise<Program> {
  const { data } = await apiClient.post('/institutions/me/programs', payload)
  return data
}

export async function updateProgram(programId: string, payload: Partial<{
  program_name: string; degree_type: string; department: string;
  duration_months: number; tuition: number; acceptance_rate: number;
  delivery_format: string; campus_setting: string;
  requirements: Record<string, any>; application_requirements: Record<string, any>[];
  description_text: string; who_its_for: string;
  application_deadline: string; program_start_date: string;
  tracks: string[]; outcomes_data: Record<string, any>;
  intake_rounds: Record<string, any>[]; media_urls: string[];
  highlights: string[]; faculty_contacts: { name: string; email?: string; role?: string }[]
}>): Promise<Program> {
  const { data } = await apiClient.put(`/institutions/me/programs/${programId}`, payload)
  return data
}

export async function publishProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/publish`)
  return data
}

export async function unpublishProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/unpublish`)
  return data
}

export async function deleteProgram(programId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/programs/${programId}`)
}

export async function getSegments(): Promise<Segment[]> {
  const { data } = await apiClient.get('/institutions/me/segments')
  return data
}

export async function createSegment(payload: {
  segment_name: string; program_id?: string | null;
  criteria: Record<string, any>; is_active?: boolean
}): Promise<Segment> {
  const { data } = await apiClient.post('/institutions/me/segments', payload)
  return data
}

export async function updateSegment(segmentId: string, payload: Partial<{
  segment_name: string; program_id: string | null;
  criteria: Record<string, any>; is_active: boolean
}>): Promise<Segment> {
  const { data } = await apiClient.put(`/institutions/me/segments/${segmentId}`, payload)
  return data
}

export async function deleteSegment(segmentId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/segments/${segmentId}`)
}

// --- Dashboard & Analytics ---

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get('/institutions/me/dashboard')
  return data
}

export async function getAnalytics(): Promise<AnalyticsData> {
  const { data } = await apiClient.get('/institutions/me/analytics')
  return data
}

// --- Campaigns ---

export async function getCampaigns(status?: string): Promise<Campaign[]> {
  const params = status ? { status } : undefined
  const { data } = await apiClient.get('/institutions/me/campaigns', { params })
  return data
}

export async function createCampaign(payload: {
  campaign_name: string; campaign_type?: string; program_id?: string | null;
  segment_id?: string | null; message_subject?: string; message_body?: string;
  scheduled_send_at?: string | null
}): Promise<Campaign> {
  const { data } = await apiClient.post('/institutions/me/campaigns', payload)
  return data
}

export async function updateCampaign(campaignId: string, payload: Partial<{
  campaign_name: string; campaign_type: string; program_id: string | null;
  segment_id: string | null; message_subject: string; message_body: string;
  status: string; scheduled_send_at: string | null
}>): Promise<Campaign> {
  const { data } = await apiClient.put(`/institutions/me/campaigns/${campaignId}`, payload)
  return data
}

export async function deleteCampaign(campaignId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/campaigns/${campaignId}`)
}

export async function sendCampaign(campaignId: string): Promise<Campaign> {
  const { data } = await apiClient.post(`/institutions/me/campaigns/${campaignId}/send`)
  return data
}

export async function getCampaignMetrics(campaignId: string): Promise<CampaignMetrics> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}/metrics`)
  return data
}

export async function previewCampaignAudience(campaignId: string): Promise<{ campaign_id: string; audience_count: number }> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}/audience`)
  return data
}

export async function previewSegmentAudience(segmentId: string): Promise<{ segment_id: string; audience_count: number }> {
  const { data } = await apiClient.get(`/institutions/me/segments/${segmentId}/preview`)
  return data
}

export async function chatInstitutionAssistant(message: string, contextProgramId?: string): Promise<{ reply: string; model: string; provider: string }> {
  const { data } = await apiClient.post('/institutions/me/assistant/chat', {
    message,
    context_program_id: contextProgramId,
  })
  return data
}

// --- Datasets ---

export async function requestDatasetUpload(payload: {
  dataset_name: string; dataset_type: string; file_name: string;
  content_type?: string; file_size_bytes?: number;
  description?: string; usage_scope?: string;
}): Promise<{ dataset_id: string; upload_url: string }> {
  const { data } = await apiClient.post('/institutions/me/datasets/upload', payload)
  return data
}

export async function confirmDatasetUpload(datasetId: string): Promise<InstitutionDataset> {
  const { data } = await apiClient.post(`/institutions/me/datasets/${datasetId}/confirm`)
  return data
}

export async function getDatasets(): Promise<InstitutionDataset[]> {
  const { data } = await apiClient.get('/institutions/me/datasets')
  return data
}

export async function getDataset(datasetId: string): Promise<InstitutionDataset> {
  const { data } = await apiClient.get(`/institutions/me/datasets/${datasetId}`)
  return data
}

export async function getDatasetPreview(datasetId: string): Promise<DatasetPreview> {
  const { data } = await apiClient.get(`/institutions/me/datasets/${datasetId}/preview`)
  return data
}

export async function updateDataset(datasetId: string, payload: Partial<{
  dataset_name: string; description: string; column_mapping: Record<string, string>;
  usage_scope: string; status: string;
}>): Promise<InstitutionDataset> {
  const { data } = await apiClient.put(`/institutions/me/datasets/${datasetId}`, payload)
  return data
}

export async function deleteDataset(datasetId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/datasets/${datasetId}`)
}
