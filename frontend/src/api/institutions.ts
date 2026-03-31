import apiClient from './client'
import type { Institution, Program, Segment } from '../types'

export async function getInstitution(): Promise<Institution> {
  const { data } = await apiClient.get('/institutions/me')
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
  requirements?: Record<string, any>; description_text?: string;
  current_preferences_text?: string; application_deadline?: string;
  program_start_date?: string; page_header_image_url?: string;
  highlights?: string[]; faculty_contacts?: { name: string; email?: string; role?: string }[]
}): Promise<Program> {
  const { data } = await apiClient.post('/institutions/me/programs', payload)
  return data
}

export async function updateProgram(programId: string, payload: Partial<{
  program_name: string; degree_type: string; department: string;
  duration_months: number; tuition: number; acceptance_rate: number;
  requirements: Record<string, any>; description_text: string;
  current_preferences_text: string; application_deadline: string;
  program_start_date: string; page_header_image_url: string;
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
