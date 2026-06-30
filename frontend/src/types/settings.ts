// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
import type { EmailFrequency, NotificationTypePref } from './messaging';

// === SETTINGS (Spec 21) ===
export type ThemePref = 'light' | 'dark' | 'system'
export type FontSizePref = 'sm' | 'md' | 'lg' | 'xl'

export interface AccessibilityPrefs {
  dyslexia_mode: boolean
  font_size: FontSizePref
  reduced_motion: boolean
}

export interface SettingsPreferences {
  locale: string | null
  timezone: string | null
  theme: ThemePref
  accessibility: AccessibilityPrefs
}

export interface DeletionInfo {
  scheduled_at: string
  purge_at: string
}

export interface UserSettings {
  account: {
    email: string
    role: string
    member_since: string | null
    display_name: string | null
    photo_url: string | null
    pending_email: string | null
  }
  security: { mfa_enabled: boolean; mfa_method: string | null }
  preferences: SettingsPreferences
  notifications: NotificationTypePref[]
  email_enabled: boolean
  email_frequency: EmailFrequency
  deletion: DeletionInfo | null
}

export interface MfaEnrollResponse {
  secret: string
  otpauth_uri: string
  recovery_codes: string[]
}

export interface SessionInfo {
  id: string
  device: string
  current: boolean
  last_active: string | null
  location: string | null
}

export interface LoginEvent {
  at: string
  device: string | null
  location: string | null
  risk: string | null
}

export interface TeamMember {
  id: string
  email: string
  role: string
  status: string
  invited_at: string | null
}

export interface ReviewConfig {
  blind_review_default: boolean
  calibration_enabled: boolean
  reviewer_assignment_mode: 'round_robin' | 'load_balanced' | 'manual'
}

// Spec 37 §5 — per-institution AI controls (per-surface on/off + confidence
// thresholds) plus the 46 §9 no-training tier override.
export interface AISurfaceConfig {
  enabled: boolean
  min_confidence: number
}

export interface AIConfig {
  surfaces: Record<string, AISurfaceConfig>
  no_training: boolean
}

export interface InstitutionSettings {
  account: {
    institution_id: string | null
    name: string | null
    contact_email: string | null
    website_url: string | null
    primary_domain: string | null
    member_since: string | null
  }
  security: { mfa_enabled: boolean; mfa_method: string | null }
  preferences: SettingsPreferences
  notifications: NotificationTypePref[]
  email_enabled: boolean
  email_frequency: EmailFrequency
  team: TeamMember[]
  deletion: DeletionInfo | null
  review_config: ReviewConfig
  ai_config: AIConfig
}


// === RECOMMENDATIONS ===
export interface RecommendationRequest {
  id: string
  student_id: string
  recommender_name: string
  recommender_email: string | null
  recommender_title: string | null
  recommender_institution: string | null
  relationship: string | null
  status: 'draft' | 'requested' | 'submitted' | 'received'
  requested_at: string | null
  due_date: string | null
  notes: string | null
  target_program_id: string | null
  created_at: string
  updated_at: string
}
