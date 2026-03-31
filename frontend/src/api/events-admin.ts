import apiClient from './client'
import type { EventItem, RSVP } from '../types'

export async function getInstitutionEvents(status?: string): Promise<EventItem[]> {
  const params = status ? { status } : {}
  const { data } = await apiClient.get('/events/manage', { params })
  return data
}

export async function createEvent(payload: {
  event_name: string; event_type: string; start_time: string; end_time: string;
  description?: string; location?: string; capacity?: number; program_id?: string | null
}): Promise<EventItem> {
  const { data } = await apiClient.post('/events/manage', payload)
  return data
}

export async function getEventAttendees(eventId: string): Promise<RSVP[]> {
  const { data } = await apiClient.get(`/events/manage/${eventId}/attendees`)
  return data
}
