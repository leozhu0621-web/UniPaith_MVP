/** Spec 31 — canonical institution admissions intake routes. */

export type AdmissionsTab = 'pipeline' | 'integrity' | 'interviews' | 'inquiries' | 'cohort'
export type PipelineView = 'board' | 'list' | 'review' | 'priority'

export function admissionsUrl(tab: AdmissionsTab = 'pipeline', view?: PipelineView): string {
  const params = new URLSearchParams({ tab })
  if (view) params.set('view', view)
  return `/i/admissions?${params.toString()}`
}

export function applicantUrl(applicationId: string, detailTab?: string): string {
  const base = `/i/admissions/applicant/${applicationId}`
  return detailTab ? `${base}?tab=${detailTab}` : base
}

export const INQUIRIES_URL = '/i/inquiries'
