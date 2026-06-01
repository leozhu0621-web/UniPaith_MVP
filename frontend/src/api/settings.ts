import apiClient from './client'
import type {
  DeletionInfo,
  InstitutionSettings,
  LoginEvent,
  MfaEnrollResponse,
  ReviewConfig,
  SessionInfo,
  TeamMember,
  UserSettings,
} from '../types'

// ── Student settings ────────────────────────────────────────────────────────

export interface UpdateSettingsPayload {
  display_name?: string
  photo_url?: string
  locale?: string
  timezone?: string
  theme?: 'light' | 'dark' | 'system'
  dyslexia_mode?: boolean
  font_size?: 'sm' | 'md' | 'lg' | 'xl'
  reduced_motion?: boolean
}

export const getSettings = (): Promise<UserSettings> =>
  apiClient.get('/students/me/settings').then(r => r.data)

export const updateSettings = (data: UpdateSettingsPayload): Promise<UserSettings> =>
  apiClient.patch('/students/me/settings', data).then(r => r.data)

// ── Account-level security + deletion (shared across roles) ─────────────────

export const changePassword = (current_password: string, new_password: string) =>
  apiClient.post('/account/change-password', { current_password, new_password }).then(r => r.data)

export const changeEmail = (new_email: string): Promise<{ pending_email: string }> =>
  apiClient.post('/account/change-email', { new_email }).then(r => r.data)

export const mfaEnroll = (): Promise<MfaEnrollResponse> =>
  apiClient.post('/account/mfa/enroll').then(r => r.data)

export const mfaConfirm = (code: string): Promise<{ mfa_enabled: boolean; mfa_method: string | null }> =>
  apiClient.post('/account/mfa/confirm', { code }).then(r => r.data)

export const mfaDisable = (code: string): Promise<{ mfa_enabled: boolean; mfa_method: string | null }> =>
  apiClient.post('/account/mfa/disable', { code }).then(r => r.data)

export const getSessions = (): Promise<SessionInfo[]> =>
  apiClient.get('/account/sessions').then(r => r.data)

export const revokeSessions = () =>
  apiClient.post('/account/sessions/revoke').then(r => r.data)

export const getLoginActivity = (): Promise<LoginEvent[]> =>
  apiClient.get('/account/login-activity').then(r => r.data)

export const deleteAccount = (confirm_text: string, password: string): Promise<DeletionInfo> =>
  apiClient.post('/account/delete', { confirm_text, password }).then(r => r.data)

export const cancelDeletion = () =>
  apiClient.post('/account/delete/cancel').then(r => r.data)

// ── Institution settings + team ─────────────────────────────────────────────

export interface UpdateInstitutionSettingsPayload {
  name?: string
  contact_email?: string
  website_url?: string
  review_config?: Partial<ReviewConfig>
  theme?: 'light' | 'dark' | 'system'
  locale?: string
  timezone?: string
  dyslexia_mode?: boolean
  font_size?: 'sm' | 'md' | 'lg' | 'xl'
  reduced_motion?: boolean
}

export const getInstitutionSettings = (): Promise<InstitutionSettings> =>
  apiClient.get('/institutions/settings').then(r => r.data)

export const updateInstitutionSettings = (
  data: UpdateInstitutionSettingsPayload
): Promise<InstitutionSettings> =>
  apiClient.patch('/institutions/settings', data).then(r => r.data)

export const getTeam = (): Promise<TeamMember[]> =>
  apiClient.get('/institutions/settings/team').then(r => r.data)

export const inviteTeamMember = (email: string, role: string): Promise<TeamMember> =>
  apiClient.post('/institutions/settings/team/invite', { email, role }).then(r => r.data)

export const revokeTeamInvite = (inviteId: string) =>
  apiClient.post(`/institutions/settings/team/invite/${inviteId}/revoke`).then(r => r.data)
