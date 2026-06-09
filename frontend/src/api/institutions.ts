import apiClient from './client'
import type { AnalyticsData, AnalyticsFilters, AttributionReport, AuditEventDetail, AuditLogList, Campaign, CommunicationTemplate, FunnelReport, IntakeRound, OverviewReport, ProgramChecklistItem, CampaignAttributionDetail, CampaignLink, CampaignMetrics, CampaignObjective, CampaignDestinationType, CampaignCtaType, CampaignChannel, AudiencePreview, DraftCampaignCopy, UploadedList, CampaignSuppression, DashboardSummary, DatasetMappingTemplate, DatasetPreview, DatasetVersion, Inquiry, Institution, InstitutionDataset, InstitutionPost, InstitutionSetupState, NLBridgeResult, PostCTA, PostVisibility, Program, Promotion, Segment, SegmentPreview, SegmentRuleTree, SetupStepPatch, SignalDictionary, ValidationReport } from '../types'

export async function getInstitution(): Promise<Institution> {
  const { data } = await apiClient.get('/institutions/me')
  return data
}

// --- First-run setup wizard (Spec 30) ---

export async function getSetupState(): Promise<InstitutionSetupState> {
  const { data } = await apiClient.get('/institutions/me/setup')
  return data
}

export async function patchSetupStep(payload: SetupStepPatch): Promise<InstitutionSetupState> {
  const { data } = await apiClient.patch('/institutions/me/setup/step', payload)
  return data
}

export async function completeSetup(): Promise<InstitutionSetupState> {
  const { data } = await apiClient.post('/institutions/me/setup/complete')
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
  student_body_size: number; founded_year: number; contact_email: string; contact_phone: string;
  media_gallery: string[];
  // JSONB dicts — see UpdateInstitutionRequest in the backend schema.
  social_links: Record<string, any>;
  inquiry_routing: Record<string, any>;
  support_services: Record<string, any>;
  policies: Record<string, any>;
  international_info: Record<string, any>;
  school_outcomes: Record<string, any>;
  require_campaign_approval: boolean;
  accreditation?: string;
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
  program_name: string; degree_type: string; school_id: string | null; department: string;
  duration_months: number; tuition: number; acceptance_rate: number;
  delivery_format: string; campus_setting: string;
  requirements: Record<string, any>; application_requirements: Record<string, any> | Record<string, any>[];
  description_text: string; who_its_for: string;
  application_deadline: string; program_start_date: string;
  // tracks + intake_rounds are JSONB dicts in the DB (e.g., tracks has
  // {concentrations, note}; intake_rounds has {fall_YYYY: {...}, source}).
  // Spec 23 §3 — the guided editor now also writes a structured intake_rounds[]
  // and the typed cost_data / outcomes_data / application_requirements blobs.
  tracks: Record<string, any>; outcomes_data: Record<string, any>;
  intake_rounds: Record<string, any> | Record<string, any>[]; media_urls: string[];
  highlights: string[]; faculty_contacts: { name: string; email?: string; role?: string }[];
  cost_data: Record<string, any>; promotion_categories: string[];
}

// Spec 23 §6 — structured publish-validation error. The publish endpoint returns
// 422 with this under `detail` so the editor can list each missing field and
// scroll to the section that owns it.
export type PublishValidationDetail = {
  message: string
  missing_fields: { field: string; section: string; message: string }[]
}

export async function createProgram(payload: Partial<ProgramWritablePayload> & {
  program_name: string; degree_type: string;
}): Promise<Program> {
  const { data } = await apiClient.post('/institutions/me/programs', payload)
  return data
}

// `expectedVersion` (Spec 23 §6) lets the server reject a save that raced another
// edit (409). Omit it for first-load saves where no baseline version is known.
export async function updateProgram(
  programId: string,
  payload: Partial<ProgramWritablePayload>,
  expectedVersion?: number,
): Promise<Program> {
  const body = expectedVersion != null ? { ...payload, expected_version: expectedVersion } : payload
  const { data } = await apiClient.put(`/institutions/me/programs/${programId}`, body)
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

type SegmentWritePayload = Partial<{
  segment_name: string
  description: string | null
  program_id: string | null
  rules: SegmentRuleTree | null
  criteria: Record<string, any> | null
  uploaded_list_ids: string[]
  frequency_cap_per_week: number | null
  is_active: boolean
}>

export async function createSegment(payload: SegmentWritePayload): Promise<Segment> {
  const { data } = await apiClient.post('/institutions/me/segments', payload)
  return data
}

export async function updateSegment(segmentId: string, payload: SegmentWritePayload): Promise<Segment> {
  const { data } = await apiClient.put(`/institutions/me/segments/${segmentId}`, payload)
  return data
}

export async function deleteSegment(segmentId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/segments/${segmentId}`)
}

// --- Spec 26 §2/§3/§6 — signal dictionary, preview, NL bridge ---

export async function getSegmentSignalDictionary(): Promise<SignalDictionary> {
  const { data } = await apiClient.get('/institutions/me/segments/signal-dictionary')
  return data
}

export async function previewSegmentRules(payload: {
  rules: SegmentRuleTree | null
  program_id?: string | null
  uploaded_list_ids?: string[]
}): Promise<SegmentPreview> {
  const { data } = await apiClient.post('/institutions/me/segments/preview', payload)
  return data
}

export async function previewSavedSegment(segmentId: string): Promise<SegmentPreview> {
  const { data } = await apiClient.post(`/institutions/me/segments/${segmentId}/preview`)
  return data
}

export async function segmentNlBridge(text: string): Promise<NLBridgeResult> {
  const { data } = await apiClient.post('/institutions/me/segments/nl-bridge', { text })
  return data
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

// --- Attribution & Funnel Analytics (Spec 28) ---

function analyticsParams(f: AnalyticsFilters): Record<string, string> {
  const p: Record<string, string> = {}
  for (const [k, v] of Object.entries(f)) {
    if (v) p[k] = v as string
  }
  return p
}

export async function getAnalyticsOverview(f: AnalyticsFilters): Promise<OverviewReport> {
  const { data } = await apiClient.get('/institutions/me/analytics/overview', {
    params: analyticsParams(f),
  })
  return data
}

export async function getAnalyticsFunnel(f: AnalyticsFilters): Promise<FunnelReport> {
  const { data } = await apiClient.get('/institutions/me/analytics/funnel', {
    params: analyticsParams(f),
  })
  return data
}

export async function getAnalyticsAttribution(f: AnalyticsFilters): Promise<AttributionReport> {
  const { data } = await apiClient.get('/institutions/me/analytics/attribution', {
    params: analyticsParams(f),
  })
  return data
}

export async function exportAnalyticsCsv(kind: string, f: AnalyticsFilters): Promise<void> {
  const { data } = await apiClient.get('/institutions/me/analytics/export', {
    params: { ...analyticsParams(f), kind, format: 'csv' },
    responseType: 'blob',
  })
  const url = URL.createObjectURL(data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analytics-${kind}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// --- Campaigns (Spec 25) ---

export interface CampaignPayload {
  name: string
  objective?: CampaignObjective | null
  owner_id?: string | null
  associate_program_ids?: string[]
  associate_intake_round_id?: string | null
  destination_type?: CampaignDestinationType | null
  destination_id?: string | null
  destination_url?: string | null
  cta_type?: CampaignCtaType | null
  channels?: CampaignChannel[]
  audience_segment_ids?: string[]
  audience_uploaded_list_ids?: string[]
  subject?: string | null
  body?: string | null
  scheduled_at?: string | null
}

export async function getCampaigns(status?: string): Promise<Campaign[]> {
  const params = status ? { status } : undefined
  const { data } = await apiClient.get('/institutions/me/campaigns', { params })
  return data
}

export async function getCampaign(campaignId: string): Promise<Campaign> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}`)
  return data
}

export async function createCampaign(payload: CampaignPayload): Promise<Campaign> {
  const { data } = await apiClient.post('/institutions/me/campaigns', payload)
  return data
}

export async function updateCampaign(campaignId: string, payload: Partial<CampaignPayload>): Promise<Campaign> {
  const { data } = await apiClient.put(`/institutions/me/campaigns/${campaignId}`, payload)
  return data
}

export async function deleteCampaign(campaignId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/campaigns/${campaignId}`)
}

async function campaignAction(campaignId: string, action: string): Promise<Campaign> {
  const { data } = await apiClient.post(`/institutions/me/campaigns/${campaignId}/${action}`)
  return data
}
export const sendCampaign = (id: string) => campaignAction(id, 'send')
export const scheduleCampaign = (id: string) => campaignAction(id, 'schedule')
export const pauseCampaign = (id: string) => campaignAction(id, 'pause')
export const resumeCampaign = (id: string) => campaignAction(id, 'resume')
export const completeCampaign = (id: string) => campaignAction(id, 'complete')
export const submitCampaignForApproval = (id: string) => campaignAction(id, 'submit-approval')
export const approveCampaign = (id: string) => campaignAction(id, 'approve')

export async function rejectCampaign(campaignId: string, comment: string): Promise<Campaign> {
  const { data } = await apiClient.post(`/institutions/me/campaigns/${campaignId}/reject`, { comment })
  return data
}

export async function getCampaignMetrics(campaignId: string): Promise<CampaignMetrics> {
  const { data } = await apiClient.get(`/institutions/me/campaigns/${campaignId}/metrics`)
  return data
}

export async function previewCampaignAudience(campaignId: string): Promise<AudiencePreview> {
  const { data } = await apiClient.post(`/institutions/me/campaigns/${campaignId}/preview-audience`)
  return data
}

export async function draftCampaignCopy(payload: {
  objective?: string | null
  cta_type?: string | null
  audience_summary?: string | null
  audience_segment_ids?: string[]
  tone?: string | null
  additional_context?: string | null
}): Promise<DraftCampaignCopy> {
  const { data } = await apiClient.post('/institutions/me/campaigns/draft-copy', payload)
  return data
}

// --- Uploaded contact lists (Spec 24/26) ---

export async function getUploadedLists(): Promise<UploadedList[]> {
  const { data } = await apiClient.get('/institutions/me/uploaded-lists')
  return data
}

export async function createUploadedList(payload: {
  name: string; description?: string | null; source?: string;
  source_consent_confirmed?: boolean; contacts: Record<string, any>[]
}): Promise<UploadedList> {
  const { data } = await apiClient.post('/institutions/me/uploaded-lists', payload)
  return data
}

export async function updateUploadedList(listId: string, payload: Partial<{
  name: string; description: string | null; source_consent_confirmed: boolean
}>): Promise<UploadedList> {
  const { data } = await apiClient.put(`/institutions/me/uploaded-lists/${listId}`, payload)
  return data
}

export async function deleteUploadedList(listId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/uploaded-lists/${listId}`)
}

// --- Suppression list (Spec 25 §4) ---

export async function getSuppressions(): Promise<CampaignSuppression[]> {
  const { data } = await apiClient.get('/institutions/me/suppressions')
  return data
}

export async function addSuppression(email: string, reason?: string): Promise<CampaignSuppression> {
  const { data } = await apiClient.post('/institutions/me/suppressions', { email, reason })
  return data
}

export async function deleteSuppression(suppressionId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/suppressions/${suppressionId}`)
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

// Spec 27 §5 — per-object engagement tracking (post/event/promotion).
export async function trackEngagement(payload: {
  object_type: 'post' | 'event' | 'promotion'
  object_id: string
  action: 'view' | 'impression' | 'click' | 'save' | 'request_info' | 'apply_started'
}): Promise<void> {
  try {
    await apiClient.post('/institutions/track/engagement', payload)
  } catch {
    // Engagement tracking is best-effort — never surface an error to the user.
  }
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

// Reorder checklist items — Spec/47 G-I3. Persists the new order by
// PUT-ing the `sort_order` field for each item in the supplied order.
// Items keep their existing `sort_order` only if they remain at the same
// index — otherwise they get assigned (index * 10) so adding an item later
// doesn't immediately force a cascade.
export async function reorderChecklistItems(
  programId: string,
  orderedIds: string[],
  currentItems: ProgramChecklistItem[],
): Promise<void> {
  const idToCurrentSort = new Map(currentItems.map(it => [it.id, it.sort_order]))
  const updates = orderedIds
    .map((id, index) => ({ id, newSort: index * 10, oldSort: idToCurrentSort.get(id) }))
    .filter(u => u.oldSort !== u.newSort)
  await Promise.all(
    updates.map(u =>
      apiClient.put(`/institutions/me/programs/${programId}/checklist/${u.id}`, {
        sort_order: u.newSort,
      }),
    ),
  )
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
  // Spec 37 §3/§5 — capture token, AI-vs-rule-based source, and disabled flag.
  source?: 'ai' | 'rule_based'
  draft_token?: string
  disabled?: boolean
}> {
  const params: Record<string, string> = { application_id: applicationId, message_type: messageType }
  if (contextNotes) params.context_notes = contextNotes
  const { data } = await apiClient.post('/institutions/me/templates/ai-draft', null, { params })
  return data
}

// --- Audit Log (Spec 36) ---

export interface AuditLogParams {
  application_id?: string
  action?: string
  entity_type?: string
  category?: string
  actor_id?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export async function getAuditLog(params?: AuditLogParams): Promise<AuditLogList> {
  const { data } = await apiClient.get('/institutions/me/audit-log', { params })
  return data
}

export async function getAuditEvent(id: string): Promise<AuditEventDetail> {
  const { data } = await apiClient.get(`/institutions/me/audit-log/${id}`)
  return data
}

export async function exportAuditCsv(params?: AuditLogParams): Promise<Blob> {
  const { data } = await apiClient.get('/institutions/me/audit-log', {
    params: { ...params, format: 'csv' },
    responseType: 'blob',
  })
  return data as Blob
}

export async function overrideFairnessSignal(body: {
  signal_key: string
  action?: 'acknowledge' | 'override'
  reason: string
}): Promise<AuditEventDetail> {
  const { data } = await apiClient.post('/institutions/me/intelligence/fairness/override', body)
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
  target_kind?: 'program' | 'institution' | 'landing'
  target_url?: string
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
  target_kind: 'program' | 'institution' | 'landing'
  target_url: string
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

export async function recordPromotionClick(promotionId: string): Promise<void> {
  await apiClient.post(`/institutions/promotions/${promotionId}/click`)
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
  // Spec 34 §6 — admitted students with an unanswered offer near/past deadline.
  alerts: {
    application_id: string
    student_id: string
    student_name?: string | null
    offer_id?: string
    risk_level: 'high' | 'medium'
    reason: string
    days_remaining?: number | null
    response_deadline?: string | null
  }[]
  count: number
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
  coverage_start?: string; coverage_end?: string;
  update_mode?: 'replace' | 'append';
}): Promise<{ dataset_id: string; upload_url: string; staging_s3_key?: string }> {
  const { data } = await apiClient.post('/institutions/me/datasets/upload', payload)
  return data
}

export async function confirmDatasetUpload(
  datasetId: string,
  payload?: {
    column_mapping?: Record<string, string>;
    skip_invalid_rows?: boolean;
    save_template?: boolean;
    template_name?: string;
  },
): Promise<InstitutionDataset> {
  const { data } = await apiClient.post(`/institutions/me/datasets/${datasetId}/confirm`, payload ?? {})
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

export async function getDatasetPreview(datasetId: string, limit = 100): Promise<DatasetPreview> {
  const { data } = await apiClient.get(`/institutions/me/datasets/${datasetId}/preview`, { params: { limit } })
  return data
}

export async function updateDataset(datasetId: string, payload: Partial<{
  dataset_name: string; description: string; column_mapping: Record<string, string>;
  usage_scope: string; status: string;
  coverage_start: string; coverage_end: string;
}>): Promise<InstitutionDataset> {
  const { data } = await apiClient.put(`/institutions/me/datasets/${datasetId}`, payload)
  return data
}

export async function deleteDataset(datasetId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/datasets/${datasetId}`)
}

export async function requestDatasetReplaceUpload(
  datasetId: string,
  payload: { file_name: string; content_type?: string; file_size_bytes?: number },
): Promise<{ dataset_id: string; upload_url: string; staging_s3_key?: string }> {
  const { data } = await apiClient.post(`/institutions/me/datasets/${datasetId}/replace/upload`, payload)
  return data
}

export async function confirmDatasetReplace(
  datasetId: string,
  payload: {
    staging_s3_key: string; file_name: string; update_mode?: 'replace' | 'append';
    column_mapping?: Record<string, string>; skip_invalid_rows?: boolean;
  },
): Promise<InstitutionDataset> {
  const path = payload.update_mode === 'append'
    ? `/institutions/me/datasets/${datasetId}/append`
    : `/institutions/me/datasets/${datasetId}/replace`
  const { data } = await apiClient.post(path, payload)
  return data
}

export async function getDatasetVersions(datasetId: string): Promise<DatasetVersion[]> {
  const { data } = await apiClient.get(`/institutions/me/datasets/${datasetId}/versions`)
  return data
}

export async function rollbackDatasetVersion(datasetId: string, versionId: string): Promise<InstitutionDataset> {
  const { data } = await apiClient.post(`/institutions/me/datasets/${datasetId}/versions/${versionId}/rollback`)
  return data
}

export async function getDatasetMappingTemplates(datasetType?: string): Promise<DatasetMappingTemplate[]> {
  const { data } = await apiClient.get('/institutions/me/datasets/mapping-templates', {
    params: datasetType ? { dataset_type: datasetType } : undefined,
  })
  return data
}

export async function saveDatasetMappingTemplate(payload: {
  template_name: string;
  dataset_type: string;
  column_mapping: Record<string, string>;
}): Promise<DatasetMappingTemplate> {
  const { data } = await apiClient.post('/institutions/me/datasets/mapping-templates', payload)
  return data
}

export function parseValidationReport(err: unknown): ValidationReport | null {
  const detail = (err as { response?: { data?: { detail?: { validation_report?: ValidationReport } } } })
    ?.response?.data?.detail
  if (detail && typeof detail === 'object' && 'validation_report' in detail) {
    return detail.validation_report as ValidationReport
  }
  return null
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
  ctas?: PostCTA[]; visibility?: PostVisibility;
}): Promise<InstitutionPost> {
  const { data } = await apiClient.post('/institutions/me/posts', payload)
  return data
}

export async function updatePost(postId: string, payload: Partial<{
  title: string; body: string; media_urls: { url: string; type: string; caption?: string }[];
  tagged_program_ids: string[]; tagged_intake: string;
  status: string; scheduled_for: string;
  is_template: boolean; template_name: string;
  ctas: PostCTA[]; visibility: PostVisibility;
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

export async function getPublicPosts(
  institutionId: string,
  params?: { school_id?: string; program_id?: string; institution_scope?: boolean },
): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get(`/institutions/${institutionId}/posts`, { params })
  return data
}

export async function getPublicPostsFeed(limit = 20): Promise<InstitutionPost[]> {
  const { data } = await apiClient.get('/institutions/posts/feed', { params: { limit } })
  return data
}
