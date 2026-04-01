import apiClient from './client'

// ─── Dashboard ───
export const getSystemStats = () =>
  apiClient.get('/admin/dashboard/stats').then(r => r.data)

// ─── Internal: Users ───
export const getUsers = (params?: {
  role?: string
  q?: string
  is_active?: boolean
  page?: number
  page_size?: number
}) =>
  apiClient.get('/internal/users', { params }).then(r => r.data)

export const deactivateUser = (userId: string, reason?: string) =>
  apiClient.patch(`/internal/users/${userId}/deactivate`, { reason }).then(r => r.data)

export const activateUser = (userId: string, reason?: string) =>
  apiClient.patch(`/internal/users/${userId}/activate`, { reason }).then(r => r.data)

export const bulkSetUsersActive = (data: { user_ids: string[]; active: boolean; reason?: string }) =>
  apiClient.post('/internal/users/bulk-active', data).then(r => r.data)

// ─── Internal: Institutions ───
export const verifyInstitution = (institutionId: string, reason?: string) =>
  apiClient.patch(`/internal/institutions/${institutionId}/verify`, { reason }).then(r => r.data)

export const bulkVerifyInstitutions = (data: { institution_ids: string[]; reason?: string }) =>
  apiClient.post('/internal/institutions/bulk-verify', data).then(r => r.data)

export const getAdminActionAudit = (params?: { limit?: number; entity_type?: string }) =>
  apiClient.get('/internal/audit/admin-actions', { params }).then(r => r.data)

// ─── Internal: AI Admin ───
export const bootstrapPrograms = () =>
  apiClient.post('/internal/ai/bootstrap-programs').then(r => r.data)

export const refreshStudent = (studentId: string) =>
  apiClient.post(`/internal/ai/refresh-student/${studentId}`).then(r => r.data)

export const refreshProgram = (programId: string) =>
  apiClient.post(`/internal/ai/refresh-program/${programId}`).then(r => r.data)

// ─── Internal: Stats ───
export const getPlatformStats = () =>
  apiClient.get('/internal/stats').then(r => r.data)

export const getEngineHealth = () =>
  apiClient.get('/internal/health').then(r => r.data)

// ─── Internal: AI Control Plane ───
export const getAIControlStatus = () =>
  apiClient.get('/internal/ai/control/status').then(r => r.data)

export const patchAIControlPolicy = (data: {
  autonomy_enabled?: boolean
  auto_fix_enabled?: boolean
  emergency_stop?: boolean
}) =>
  apiClient.patch('/internal/ai/control/policy', data).then(r => r.data)

export const runAIControlLoop = () =>
  apiClient.post('/internal/ai/control/run-loop').then(r => r.data)

export const getAIControlAudit = (params?: { limit?: number }) =>
  apiClient.get('/internal/ai/control/audit', { params }).then(r => r.data)

export const getAIControlSLO = () =>
  apiClient.get('/internal/ai/control/slo').then(r => r.data)

export const getAIOpsSnapshot = () =>
  apiClient.get('/internal/ai/ops/snapshot').then(r => r.data)

export const runAIEngineGraph = () =>
  apiClient.post('/internal/ai/engine/run').then(r => r.data)

export const getAIEngineState = () =>
  apiClient.get('/internal/ai/engine/state').then(r => r.data)

// ─── Crawler: Dashboard ───
export const getCrawlerDashboard = () =>
  apiClient.get('/admin/crawler/dashboard').then(r => r.data)

// ─── Crawler: Sources ───
export const getCrawlerSources = (params?: { active_only?: boolean; limit?: number }) =>
  apiClient.get('/admin/crawler/sources', { params }).then(r => r.data)

export const getCrawlerSource = (sourceId: string) =>
  apiClient.get(`/admin/crawler/sources/${sourceId}`).then(r => r.data)

export const createCrawlerSource = (data: {
  name: string; base_url: string; source_type?: string; schedule_cron?: string
}) =>
  apiClient.post('/admin/crawler/sources', data).then(r => r.data)

export const deleteCrawlerSource = (sourceId: string) =>
  apiClient.delete(`/admin/crawler/sources/${sourceId}`).then(r => r.data)

export const seedDefaultSources = () =>
  apiClient.post('/admin/crawler/sources/seed-defaults').then(r => r.data)

// ─── Crawler: Crawl Triggers ───
export const triggerCrawl = (sourceId: string) =>
  apiClient.post(`/admin/crawler/crawl/${sourceId}`).then(r => r.data)

export const triggerCrawlAll = () =>
  apiClient.post('/admin/crawler/crawl-all').then(r => r.data)

export const crawlUrl = (data: { url: string; source_id?: string }) =>
  apiClient.post('/admin/crawler/crawl-url', data).then(r => r.data)

// ─── Crawler: Jobs ───
export const getCrawlerJobs = (params?: { source_id?: string; skip?: number; limit?: number }) =>
  apiClient.get('/admin/crawler/jobs', { params }).then(r => r.data)

export const getCrawlerJob = (jobId: string) =>
  apiClient.get(`/admin/crawler/jobs/${jobId}`).then(r => r.data)

// ─── Crawler: Review ───
export const getReviewQueue = (params?: { skip?: number; limit?: number }) =>
  apiClient.get('/admin/crawler/review', { params }).then(r => r.data)

export const getReviewStats = () =>
  apiClient.get('/admin/crawler/review/stats').then(r => r.data)

export const getReviewItem = (extractedId: string) =>
  apiClient.get(`/admin/crawler/review/${extractedId}`).then(r => r.data)

export const approveReviewItem = (extractedId: string, data?: { edits?: Record<string, any>; notes?: string }) =>
  apiClient.post(`/admin/crawler/review/${extractedId}/approve`, data ?? {}).then(r => r.data)

export const rejectReviewItem = (extractedId: string, data: { reason: string }) =>
  apiClient.post(`/admin/crawler/review/${extractedId}/reject`, data).then(r => r.data)

// ─── Crawler: Enrichment ───
export const applyAllEnrichments = () =>
  apiClient.post('/admin/crawler/enrichment/apply-all').then(r => r.data)

// ─── ML: Cycle ───
export const runMLCycle = () =>
  apiClient.post('/admin/ml/cycle/run').then(r => r.data)

export const runMLEvaluate = () =>
  apiClient.post('/admin/ml/cycle/evaluate').then(r => r.data)

export const runDriftCheck = () =>
  apiClient.post('/admin/ml/cycle/drift-check').then(r => r.data)

export const backfillOutcomes = () =>
  apiClient.post('/admin/ml/cycle/backfill-outcomes').then(r => r.data)

// ─── ML: Evaluations ───
export const getMLEvaluations = (params?: { limit?: number }) =>
  apiClient.get('/admin/ml/evaluations', { params }).then(r => r.data)

export const getMLEvaluation = (evalId: string) =>
  apiClient.get(`/admin/ml/evaluations/${evalId}`).then(r => r.data)

// ─── ML: Training ───
export const getMLTrainingRuns = (params?: { limit?: number }) =>
  apiClient.get('/admin/ml/training', { params }).then(r => r.data)

export const triggerTraining = () =>
  apiClient.post('/admin/ml/training/trigger').then(r => r.data)

// ─── ML: Model Registry ───
export const getMLModels = () =>
  apiClient.get('/admin/ml/models').then(r => r.data)

export const promoteModel = (data: { model_version: string }) =>
  apiClient.post('/admin/ml/models/promote', data).then(r => r.data)

export const rollbackModel = () =>
  apiClient.post('/admin/ml/models/rollback').then(r => r.data)

// ─── ML: A/B Tests ───
export const createABTest = (data: { experiment_name: string; control_version: string; treatment_version: string; traffic_split?: number }) =>
  apiClient.post('/admin/ml/ab-tests', data).then(r => r.data)

export const getABTestResults = (experimentName: string) =>
  apiClient.get(`/admin/ml/ab-tests/${experimentName}`).then(r => r.data)

// ─── ML: Drift ───
export const getDriftSnapshots = (params?: { limit?: number }) =>
  apiClient.get('/admin/ml/drift', { params }).then(r => r.data)

// ─── ML: Fairness ───
export const getFairnessReports = (modelVersion: string) =>
  apiClient.get(`/admin/ml/fairness/${modelVersion}`).then(r => r.data)

export const updateFairnessDial = (data: { setting: string }) =>
  apiClient.put('/admin/ml/fairness/dial', data).then(r => r.data)

// ─── ML: Outcomes ───
export const getOutcomeStats = () =>
  apiClient.get('/admin/ml/outcomes/stats').then(r => r.data)
