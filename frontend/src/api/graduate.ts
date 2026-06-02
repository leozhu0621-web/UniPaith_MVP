import apiClient from './client'

// Spec 41 · Graduate & PhD Admissions — /institutions/me/graduate

const BASE = '/institutions/me/graduate'

// ── types ───────────────────────────────────────────────────────────────────

export type RecommendedDecision =
  | 'admitted'
  | 'conditional_admission'
  | 'waitlisted'
  | 'rejected'
  | 'deferred'

export type CentralStatus = 'pending' | 'confirmed' | 'overridden' | null
export type FundingPoolKind = 'department' | 'grant' | 'fellowship' | 'other'
export type FundingComponentKind = 'TA' | 'RA' | 'fellowship' | 'tuition_waiver' | 'stipend'
export type FundingPackageStatus = 'draft' | 'proposed' | 'finalized' | 'rescinded'

export interface DepartmentSummary {
  id: string
  name: string
  code: string | null
  description: string | null
  notes: string | null
  program_count: number
  faculty_count: number
  funding_budget: number
  funding_committed: number
  created_at: string | null
}

export interface Department {
  id: string
  name: string
  code: string | null
  description: string | null
  notes: string | null
}

export interface GraduateSummary {
  departments: DepartmentSummary[]
  department_count: number
  faculty_count: number
  graduate_application_count: number
  pending_recommendations: number
  funding: { total_budget: number; total_committed: number; total_remaining: number }
}

export interface Faculty {
  id: string
  department_id: string | null
  user_id: string | null
  name: string
  email: string | null
  title: string | null
  research_areas: string[]
  accepting_students: boolean
  openings: number
  funding_available: boolean
  bio: string | null
  homepage_url: string | null
}

export interface AdvisorMatch {
  faculty_id: string
  faculty_name: string
  title: string | null
  research_areas: string[]
  accepting_students: boolean
  openings: number
  funding_available: boolean
  alignment_score: number
  shared_interests: string[]
  applicant_named_advisor: boolean
  advisor_flagged_interest: boolean
  mutual: boolean
  rationale: string | null
}

export interface GraduateIntent {
  application_id: string
  research_interests: string[]
  target_advisor_ids: string[]
  target_advisor_names: string[]
  statement_of_purpose: string | null
  funding_required: boolean
  extracted_interests: string[]
  alignment_summary: string | null
}

export interface AdvisorMatchesResponse {
  application_id: string
  applicant_interests: string[]
  intent: GraduateIntent | null
  matches: AdvisorMatch[]
  ai_enabled: boolean
}

export interface FundingPool {
  id: string
  department_id: string | null
  name: string
  kind: FundingPoolKind
  total_budget: number
  currency: string
  notes: string | null
}

export interface FundingPoolBudget {
  id: string
  department_id: string | null
  name: string
  kind: FundingPoolKind
  currency: string
  budget: number
  committed: number
  remaining: number
  over: boolean
}

export interface FundingBudget {
  pools: FundingPoolBudget[]
  total_budget: number
  total_committed: number
  total_remaining: number
}

export interface FundingComponent {
  id?: string
  kind: FundingComponentKind
  amount: number
  source_pool_id: string | null
  years: number[]
  label: string | null
}

export interface FundingAnalysis {
  per_pool: Array<{
    pool_id: string
    name: string
    budget: number
    committed: number
    this_package: number
    remaining: number
    over: boolean
  }>
  over_commit: boolean
  warnings: string[]
  suggestions: string[]
}

export interface FundingPackage {
  application_id: string
  department_id: string | null
  status: FundingPackageStatus
  total_value: number
  currency: string
  multi_year: boolean
  notes: string | null
  finalized_at: string | null
  components: FundingComponent[]
  analysis: FundingAnalysis | null
}

export interface DepartmentReviewRecord {
  application_id: string
  department_id: string | null
  recommended_decision: RecommendedDecision | null
  recommended_by: string | null
  recommended_at: string | null
  committee_notes: string | null
  funding_package_id: string | null
  central_status: CentralStatus
  central_decision: string | null
  central_at: string | null
}

export interface ReviewApplicant {
  application_id: string
  program_id: string
  program_name: string
  degree_type: string
  status: string | null
  decision: string | null
  student_decision: string | null
  recommended_decision: RecommendedDecision | null
  central_status: CentralStatus
  mutual_interest_count: number
}

export interface DepartmentReviewList {
  department: { id: string; name: string; code: string | null }
  applicants: ReviewApplicant[]
}

export interface DepartmentDashboard {
  department: DepartmentSummary
  applicant_count: number
  recommended_count: number
  admitted_count: number
  yield: { admitted: number; accepted: number }
  funding: FundingBudget
  faculty: Faculty[]
}

// ── summary + departments ─────────────────────────────────────────────────────

export const getGraduateSummary = () =>
  apiClient.get(`${BASE}/summary`).then(r => r.data as GraduateSummary)

export const listDepartments = () =>
  apiClient.get(`${BASE}/departments`).then(r => r.data as DepartmentSummary[])

export const createDepartment = (payload: Partial<Department>) =>
  apiClient.post(`${BASE}/departments`, payload).then(r => r.data as Department)

export const getDepartment = (id: string) =>
  apiClient.get(`${BASE}/departments/${id}`).then(r => r.data as Department)

export const updateDepartment = (id: string, payload: Partial<Department>) =>
  apiClient.patch(`${BASE}/departments/${id}`, payload).then(r => r.data as Department)

export const getDepartmentDashboard = (id: string) =>
  apiClient.get(`${BASE}/departments/${id}/dashboard`).then(r => r.data as DepartmentDashboard)

export const getDepartmentReview = (id: string) =>
  apiClient.get(`${BASE}/departments/${id}/review`).then(r => r.data as DepartmentReviewList)

export const getDepartmentFundingBudget = (id: string) =>
  apiClient.get(`${BASE}/departments/${id}/funding-budget`).then(r => r.data as FundingBudget)

// ── faculty ───────────────────────────────────────────────────────────────────

export const listFaculty = (departmentId?: string) =>
  apiClient
    .get(`${BASE}/faculty`, { params: departmentId ? { department_id: departmentId } : {} })
    .then(r => r.data as Faculty[])

export const createFaculty = (payload: Partial<Faculty>) =>
  apiClient.post(`${BASE}/faculty`, payload).then(r => r.data as Faculty)

export const updateFaculty = (id: string, payload: Partial<Faculty>) =>
  apiClient.patch(`${BASE}/faculty/${id}`, payload).then(r => r.data as Faculty)

// ── advisor matching + intent ─────────────────────────────────────────────────

export const getAdvisorMatches = (applicationId: string) =>
  apiClient
    .get(`${BASE}/applications/${applicationId}/advisor-matches`)
    .then(r => r.data as AdvisorMatchesResponse)

export const flagAdvisorInterest = (applicationId: string, facultyId: string, flagged: boolean) =>
  apiClient
    .post(`${BASE}/applications/${applicationId}/advisor-matches/${facultyId}/flag-interest`, {
      flagged,
    })
    .then(r => r.data as { faculty_id: string; mutual: boolean; advisor_flagged_interest: boolean })

export const getIntent = (applicationId: string) =>
  apiClient
    .get(`${BASE}/applications/${applicationId}/intent`)
    .then(r => r.data as GraduateIntent | null)

export const upsertIntent = (applicationId: string, payload: Partial<GraduateIntent>) =>
  apiClient
    .put(`${BASE}/applications/${applicationId}/intent`, payload)
    .then(r => r.data as GraduateIntent)

// ── funding pools + budget + package ──────────────────────────────────────────

export const listFundingPools = (departmentId?: string) =>
  apiClient
    .get(`${BASE}/funding/pools`, { params: departmentId ? { department_id: departmentId } : {} })
    .then(r => r.data as FundingPool[])

export const createFundingPool = (payload: Partial<FundingPool>) =>
  apiClient.post(`${BASE}/funding/pools`, payload).then(r => r.data as FundingPool)

export const updateFundingPool = (id: string, payload: Partial<FundingPool>) =>
  apiClient.patch(`${BASE}/funding/pools/${id}`, payload).then(r => r.data as FundingPool)

export const getFundingBudget = (departmentId?: string) =>
  apiClient
    .get(`${BASE}/funding/budget`, { params: departmentId ? { department_id: departmentId } : {} })
    .then(r => r.data as FundingBudget)

export const getFundingPackage = (applicationId: string) =>
  apiClient
    .get(`${BASE}/applications/${applicationId}/funding-package`)
    .then(r => r.data as FundingPackage | null)

export interface BuildFundingPackagePayload {
  status?: FundingPackageStatus
  currency?: string
  notes?: string | null
  components: Array<{
    kind: FundingComponentKind
    amount: number
    source_pool_id?: string | null
    years?: number[]
    label?: string | null
  }>
}

export const buildFundingPackage = (applicationId: string, payload: BuildFundingPackagePayload) =>
  apiClient
    .put(`${BASE}/applications/${applicationId}/funding-package`, payload)
    .then(r => r.data as FundingPackage)

// ── two-stage department review ───────────────────────────────────────────────

export const getApplicationReview = (applicationId: string) =>
  apiClient
    .get(`${BASE}/applications/${applicationId}/review`)
    .then(r => r.data as DepartmentReviewRecord | null)

export const recommendApplication = (
  applicationId: string,
  payload: { decision: RecommendedDecision; committee_notes?: string | null },
) =>
  apiClient
    .post(`${BASE}/applications/${applicationId}/recommend`, payload)
    .then(r => r.data as DepartmentReviewRecord)

export const confirmRecommendation = (
  applicationId: string,
  payload: { override_decision?: RecommendedDecision; offer_terms?: Record<string, unknown> } = {},
) =>
  apiClient
    .post(`${BASE}/applications/${applicationId}/confirm`, payload)
    .then(r => r.data as { department_review: DepartmentReviewRecord; decision: string; offer_id: string | null })

// ── student-facing grad intent (§3 flow) ──────────────────────────────────────

export const getStudentGraduateIntent = (applicationId: string) =>
  apiClient
    .get(`/students/me/applications/${applicationId}/graduate-intent`)
    .then(r => r.data as { is_graduate: boolean; intent: GraduateIntent | null })

export const putStudentGraduateIntent = (
  applicationId: string,
  payload: Partial<GraduateIntent>,
) =>
  apiClient
    .put(`/students/me/applications/${applicationId}/graduate-intent`, payload)
    .then(r => r.data as GraduateIntent)
