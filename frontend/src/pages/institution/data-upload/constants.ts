// Spec 24 — shared client constants for the Data Upload workspace.
// The backend (services/dataset_service.py) is the source of truth for these
// field contracts; kept in sync here to drive the mapping UI.

import type { DatasetType } from '../../../types'

export const DATASET_TYPES: { value: DatasetType; label: string; blurb: string }[] = [
  {
    value: 'admissions_history',
    label: 'Admissions history',
    blurb: 'Historical applicants & decisions — trains matching (consent-gated).',
  },
  {
    value: 'prospect_list',
    label: 'Prospect list',
    blurb: 'Contacts for outreach campaigns.',
  },
  {
    value: 'outcomes_summary',
    label: 'Outcomes summary',
    blurb: 'Placement / salary aggregates for the program Outcomes tab.',
  },
]

export const USAGE_SCOPES = [
  { value: 'all', label: 'All uses' },
  { value: 'marketing', label: 'Marketing only' },
  { value: 'admissions', label: 'Admissions ops only' },
  { value: 'analytics', label: 'Analytics only' },
]

// Platform target fields per dataset type (mirror of dataset_service.PLATFORM_FIELDS).
export const PLATFORM_FIELDS: Record<DatasetType, string[]> = {
  prospect_list: [
    'email', 'first_name', 'last_name', 'phone', 'nationality',
    'country', 'degree_interest', 'program_interest', 'source', 'notes',
  ],
  admissions_history: [
    'student_email', 'program_name', 'application_date', 'decision',
    'gpa', 'test_score', 'enrollment_status',
  ],
  outcomes_summary: [
    'program_name', 'graduation_year', 'employment_status', 'employer',
    'salary_range', 'time_to_employment',
  ],
}

export const REQUIRED_FIELDS: Record<DatasetType, string[]> = {
  prospect_list: ['email'],
  admissions_history: ['student_email', 'program_name', 'application_date', 'decision'],
  outcomes_summary: ['program_name', 'graduation_year'],
}

// The dataset types that carry a program identifier needing normalization.
export const PROGRAM_FIELD: Record<DatasetType, string | null> = {
  prospect_list: null,
  admissions_history: 'program_name',
  outcomes_summary: 'program_name',
}

// Semantic status → Badge variant (Spec 24 §11 — no gold here).
export const STATUS_BADGE: Record<string, 'success' | 'info' | 'warning' | 'error' | 'neutral'> = {
  uploaded: 'info',
  validated: 'success',
  processed: 'neutral',
  failed: 'error',
}

export const SCOPE_LABEL: Record<string, string> = {
  all: 'All uses',
  marketing: 'Marketing',
  admissions: 'Admissions',
  analytics: 'Analytics',
}

export const USED_BY: Record<DatasetType, string> = {
  admissions_history: 'Matching',
  prospect_list: 'Campaigns',
  outcomes_summary: 'Outcomes tab',
}

/** Best-effort auto-mapping: match an uploaded column to a platform field by
 * normalized name (lowercase, strip non-alphanumerics). */
export function autoMap(columns: string[], fields: string[]): Record<string, string> {
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')
  const fieldByNorm = new Map(fields.map((f) => [norm(f), f]))
  const out: Record<string, string> = {}
  for (const col of columns) {
    const exact = fieldByNorm.get(norm(col))
    if (exact) out[col] = exact
  }
  return out
}
