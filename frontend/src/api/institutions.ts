import apiClient from './client'
import type { AnalyticsData, AuditLogList, Campaign, CommunicationTemplate, IntakeRound, ProgramChecklistItem, CampaignAttributionDetail, CampaignLink, CampaignMetrics, DashboardSummary, DatasetPreview, Inquiry, Institution, InstitutionDataset, InstitutionPost, Program, Promotion, Segment, UnclaimedInstitution } from '../types'

export async function getInstitution(): Promise<Institution> {
  const { data } = await apiClient.get('/institutions/me')
  return data
}

export async function searchInstitutions(params?: {
  q?: string; country?: string; type?: string; page?: number; page_size?: number
}) {
  const { data } = await apiClient.get('/institutions/search', { params })
  return data
}

export async function getPublicInstitution(institutionId: string): Promise<Institution> {
  const { data } = await apiClient.get(`/institutions/${institutionId}`)
  return data
}

export async function getInstitutionSchools(institutionId: string) {
  const { data } = await apiClient.get(`/institutions/${institutionId}/schools`)
  return data
}

export async function getSchoolPrograms(institutionId: string, schoolId: string) {
  const { data } = await apiClient.get(`/institutions/${institutionId}/schools/${schoolId}/programs`)
  return data
}

// --- Institution Search & Claim ---

export async function searchUnclaimedInstitutions(query: string): Promise<UnclaimedInstitution[]> {
  const { data } = await apiClient.get('/institutions/search-unclaimed', { params: { q: query } })
  return data
}

export async function claimInstitution(extractedIds: string[]): Promise<Institution> {
  const { data } = await apiClient.post('/institutions/me/claim', { extracted_ids: extractedIds })
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
  website_url: string; description_text: string; logo_url: string;
  campus_description: string; campus_setting: 'urban' | 'suburban' | 'rural';
  student_body_size: number; contact_email: string;
  media_gallery: string[];
  // JSONB dicts — see UpdateInstitutionRequest in the backend schema.
  social_links: Record<string, any>;
  inquiry_routing: Record<string, any>;
  support_services: Record<string, any>;
  policies: Record<string, any>;
  international_info: Record<string, any>;
  school_outcomes: Record<string, any>;
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

type ProgramWritablePayload = {
  program_name: string; degree_type: string; department: string;
  duration_months: number; tuition: number; acceptance_rate: number;
  delivery_format: string; campus_setting: string;
  requirements: Record<string, any>; application_requirements: Record<string, any>[];
  description_text: string; who_its_for: string;
  application_deadline: string; program_start_date: string;
  // tracks + intake_rounds are JSONB dicts in the DB (e.g., tracks has
  // {concentrations, note}; intake_rounds has {fall_YYYY: {...}, source}).
  tracks: Record<string, any>; outcomes_data: Record<string, any>;
  intake_rounds: Record<string, any>; media_urls: string[];
  highlights: string[]; faculty_contacts: { name: string; email?: string; role?: string }[];
  cost_data: Record<string, any>;
}

export async function createProgram(payload: Partial<ProgramWritablePayload> & {
  program_name: string; degree_type: string;
}): Promise<Program> {
  const { data } = await apiClient.post('/institutions/me/programs', payload)
  return data
}

export async function updateProgram(programId: string, payload: Partial<ProgramWritablePayload>): Promise<Program> {
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

// --- Campaign Links & Attribution ---

export async function getCampaignLinks(campaignId: string): Promise<CampaignLink[]> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}/links`)
  return data
}

export async function createCampaignLink(campaignId: string, payload: {
  destination_type: string
  destination_id?: string
  custom_url?: string
  label?: string
}): Promise<CampaignLink> {
  const { data } = await apiClient.post(`/institutions/me/campaigns/${campaignId}/links`, payload)
  return data
}

export async function deleteCampaignLink(campaignId: string, linkId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/campaigns/${campaignId}/links/${linkId}`)
}

export async function getCampaignAttribution(campaignId: string): Promise<CampaignAttributionDetail> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}/attribution`)
  return data
}

export async function recordCampaignAction(payload: {
  campaign_id: string
  action_type: string
  target_id?: string
}): Promise<void> {
  await apiClient.post('/institutions/track/action', payload)
}

export async function previewSegmentAudience(segmentId: string): Promise<{ segment_id: string; audience_count: number }> {
  const { data } = await apiClient.get(`/institutions/me/segments/${segmentId}/preview`)
  return data
}

// --- Inquiries ---

export async function submitInquiry(payload: {
  institution_id: string
  program_id?: string
  subject: string
  message: string
  inquiry_type?: string
  campaign_id?: string
}): Promise<Inquiry> {
  const { data } = await apiClient.post('/institutions/inquiries', payload)
  return data
}

export async function getInquiries(status?: string): Promise<Inquiry[]> {
  const params = status ? { status } : undefined
  const { data } = await apiClient.get('/institutions/me/inquiries', { params })
  return data
}

export async function updateInquiry(inquiryId: string, payload: {
  status?: string
  assigned_to?: string
  response_text?: string
}): Promise<Inquiry> {
  const { data } = await apiClient.put(`/institutions/me/inquiries/${inquiryId}`, payload)
  return data
}

// --- Program Checklist ---

export async function getProgramChecklist(programId: string): Promise<ProgramChecklistItem[]> {
  const { data } = await apiClient.get(`/institutions/me/programs/${programId}/checklist`)
  return data
}

export async function createChecklistItem(programId: string, payload: {
  item_name: string; category?: string; requirement_level?: string;
  description?: string; instructions?: string; sort_order?: number
}): Promise<ProgramChecklistItem> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/checklist`, payload)
  return data
}

export async function updateChecklistItem(programId: string, itemId: string, payload: Partial<{
  item_name: string; category: string; requirement_level: string;
  description: string; instructions: string; sort_order: number; is_active: boolean
}>): Promise<ProgramChecklistItem> {
  const { data } = await apiClient.put(`/institutions/me/programs/${programId}/checklist/${itemId}`, payload)
  return data
}

export async function deleteChecklistItem(programId: string, itemId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/programs/${programId}/checklist/${itemId}`)
}

// --- Intake Rounds ---

export async function getIntakeRounds(programId: string): Promise<IntakeRound[]> {
  const { data } = await apiClient.get(`/institutions/me/programs/${programId}/intakes`)
  return data
}

export async function createIntakeRound(programId: string, payload: {
  round_name: string; intake_term?: string; application_open?: string;
  application_deadline?: string; decision_date?: string; program_start?: string;
  capacity?: number; requirements?: Record<string, unknown>; sort_order?: number
}): Promise<IntakeRound> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/intakes`, payload)
  return data
}

export async function updateIntakeRound(programId: string, intakeId: string, payload: Partial<{
  round_name: string; intake_term: string; application_open: string;
  application_deadline: string; decision_date: string; program_start: string;
  capacity: number; requirements: Record<string, unknown>; status: string;
  is_active: boolean; sort_order: number
}>): Promise<IntakeRound> {
  const { data } = await apiClient.put(`/institutions/me/programs/${programId}/intakes/${intakeId}`, payload)
  return data
}

export async function deleteIntakeRound(programId: string, intakeId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/programs/${programId}/intakes/${intakeId}`)
}

export async function getPublicIntakeRounds(institutionId: string, programId: string): Promise<IntakeRound[]> {
  const { data } = await apiClient.get(`/institutions/${institutionId}/programs/${programId}/intakes`)
  return data
}

// --- Communication Templates ---

export async function getTemplates(templateType?: string, programId?: string): Promise<CommunicationTemplate[]> {
  const params: Record<string, string> = {}
  if (templateType) params.template_type = templateType
  if (programId) params.program_id = programId
  const { data } = await apiClient.get('/institutions/me/templates', { params })
  return data
}

export async function createTemplate(payload: {
  template_type: string; name: string; subject: string; body: string;
  program_id?: string; variables?: string[]; is_default?: boolean
}): Promise<CommunicationTemplate> {
  const { data } = await apiClient.post('/institutions/me/templates', payload)
  return data
}

export async function updateTemplate(templateId: string, payload: Partial<{
  template_type: string; name: string; subject: string; body: string;
  program_id: string; variables: string[]; is_default: boolean; is_active: boolean
}>): Promise<CommunicationTemplate> {
  const { data } = await apiClient.put(`/institutions/me/templates/${templateId}`, payload)
  return data
}

export async function deleteTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/templates/${templateId}`)
}

export async function sendFromTemplate(templateId: string, applicationIds: string[], overrides?: Record<string, string>): Promise<{ success_count: number; failed_ids: string[] }> {
  const { data } = await apiClient.post(`/institutions/me/templates/${templateId}/send`, { application_ids: applicationIds, variable_overrides: overrides })
  return data
}

export async function previewTemplate(templateId: string, applicationId?: string): Promise<{ rendered_subject: string; rendered_body: string; variables_used: string[] }> {
  const params = applicationId ? { application_id: applicationId } : undefined
  const { data } = await apiClient.post(`/institutions/me/templates/${templateId}/preview`, null, { params })
  return data
}

// --- AI Communication Drafts ---

export async function generateAIDraft(applicationId: string, messageType: string, contextNotes?: string): Promise<{
  subject: string; body: string; message_type: string; editable: boolean
}> {
  const params: Record<string, string> = { application_id: applicationId, message_type: messageType }
  if (contextNotes) params.context_notes = contextNotes
  const { data } = await apiClient.post('/institutions/me/templates/ai-draft', null, { params })
  return data
}

// --- Audit Log ---

export async function getAuditLog(params?: {
  application_id?: string; action?: string; entity_type?: string; limit?: number; offset?: number
}): Promise<AuditLogList> {
  const { data } = await apiClient.get('/institutions/me/audit-log', { params })
  return data
}

// --- Promotions ---

export async function getPromotions(): Promise<Promotion[]> {
  const { data } = await apiClient.get('/institutions/me/promotions')
  return data
}

export async function createPromotion(payload: {
  program_id?: string
  promotion_type?: string
  title: string
  description?: string
  targeting?: { regions?: string[]; countries?: string[]; degree_types?: string[]; interests?: string[] }
  starts_at?: string
  ends_at?: string
}): Promise<Promotion> {
  const { data } = await apiClient.post('/institutions/me/promotions', payload)
  return data
}

export async function updatePromotion(promotionId: string, payload: Partial<{
  program_id: string
  promotion_type: string
  title: string
  description: string
  targeting: { regions?: string[]; countries?: string[]; degree_types?: string[]; interests?: string[] }
  status: string
  starts_at: string
  ends_at: string
}>): Promise<Promotion> {
  const { data } = await apiClient.put(`/institutions/me/promotions/${promotionId}`, payload)
  return data
}

export async function deletePromotion(promotionId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/promotions/${promotionId}`)
}

export async function getFeaturedPromotions(params?: {
  region?: string; country?: string; degree_type?: string
}): Promise<Promotion[]> {
  const { data } = await apiClient.get('/institutions/promotions/featured', { params })
  return data
}

// --- AI Intelligence ---

export async function getIntelligenceDigest(): Promise<{
  institution_id: string; institution_name: string; digest: string
  stats: Record<string, number>; generated_at: string
}> {
  const { data } = await apiClient.get('/institutions/me/intelligence/digest', { timeout: 60_000 })
  return data
}

export async function getDemandForecast(): Promise<{
  institution_id: string; institution_name: string
  programs: { program_id: string; program_name: string; degree_type: string; active_matches: number; recent_predictions: number; demand_signal: string }[]
  forecast_period: string; generated_at: string
}> {
  const { data } = await apiClient.get('/institutions/me/intelligence/demand')
  return data
}

export async function getYieldRiskAlerts(): Promise<{
  institution_id: string
  alerts: { application_id: string; student_id: string; program_id: string; risk_level: string; competing_programs: number; reason: string }[]
  generated_at: string
}> {
  const { data } = await apiClient.get('/institutions/me/intelligence/yield-risks')
  return data
}

export async function getApplicantContext(studentId: string): Promise<{
  institution_id: string; student_id: string; student_name: string; context: string
  match_data: { program_id: string; score: number | null; tier: number }[]
  generated_at: string
}> {
  const { data } = await apiClient.get(`/institutions/me/intelligence/applicant/${studentId}`, { timeout: 60_000 })
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

// --- Posts ---

export async function getPosts(): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get('/institutions/me/posts')
  return data
}

export async function createPost(payload: {
  title: string; body: string; media_urls?: { url: string; type: string; caption?: string }[];
  tagged_program_ids?: string[]; tagged_intake?: string;
  status?: string; scheduled_for?: string;
  is_template?: boolean; template_name?: string;
}): Promise<InstitutionPost> {
  const { data } = await apiClient.post('/institutions/me/posts', payload)
  return data
}

export async function updatePost(postId: string, payload: Partial<{
  title: string; body: string; media_urls: { url: string; type: string; caption?: string }[];
  tagged_program_ids: string[]; tagged_intake: string;
  status: string; scheduled_for: string;
  is_template: boolean; template_name: string;
}>): Promise<InstitutionPost> {
  const { data } = await apiClient.put(`/institutions/me/posts/${postId}`, payload)
  return data
}

export async function deletePost(postId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/posts/${postId}`)
}

export async function publishPost(postId: string): Promise<InstitutionPost> {
  const { data } = await apiClient.post(`/institutions/me/posts/${postId}/publish`)
  return data
}

export async function pinPost(postId: string): Promise<InstitutionPost> {
  const { data } = await apiClient.post(`/institutions/me/posts/${postId}/pin`)
  return data
}

export async function requestPostMediaUpload(contentType: string): Promise<{ upload_url: string; media_key: string }> {
  const { data } = await apiClient.post('/institutions/me/posts/media/upload', { content_type: contentType })
  return data
}

export async function getPostTemplates(): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get('/institutions/me/posts/templates')
  return data
}

export async function getPublicPosts(institutionId: string): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get(`/institutions/${institutionId}/posts`)
  return data
}

export async function getPublicPostsFeed(limit = 20): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get('/institutions/posts/feed', { params: { limit } })
  return data
}
