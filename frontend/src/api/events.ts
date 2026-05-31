import apiClient from './client'
import { toArrayData } from './normalize'

export interface FollowedInstitution {
  institution_id: string
  name: string
  followed_at?: string | null
}

// ── Events ───────────────────────────────────────────────────────────────

export const listEvents = (params?: { program_id?: string; institution_id?: string; event_type?: string; limit?: number }) =>
  apiClient.get('/events', { params }).then(r => toArrayData<any>(r.data))

export const rsvpEvent = (eventId: string) =>
  apiClient.post(`/events/${eventId}/rsvp`).then(r => r.data)

export const cancelRsvp = (eventId: string) =>
  apiClient.delete(`/events/${eventId}/rsvp`)

export const downloadIcs = (eventId: string) =>
  apiClient.get(`/events/${eventId}/calendar`, { responseType: 'blob' }).then(r => r.data)

/** Fetch the event's .ics and trigger a browser download (Spec 12 §3.5). */
export const addEventToCalendar = async (eventId: string, eventName = 'event') => {
  const blob = await downloadIcs(eventId)
  const url = URL.createObjectURL(blob as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${eventName.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.ics`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const getMyRsvps = () =>
  apiClient.get('/events/me/rsvps').then(r => toArrayData<any>(r.data))

// ── Connect: institution follows (Spec 12 §10 / Spec 20) ──────────────────
// "Save school" == follow the institution; drives the Connect feed.

export const getMyFollows = () =>
  apiClient.get('/students/me/follows').then(r => toArrayData<FollowedInstitution>(r.data))

export const followInstitution = (institutionId: string) =>
  apiClient.post(`/students/me/follows/${institutionId}`).then(r => r.data)

export const unfollowInstitution = (institutionId: string) =>
  apiClient.delete(`/students/me/follows/${institutionId}`)
