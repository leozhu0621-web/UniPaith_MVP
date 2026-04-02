import apiClient from './client'
import { toArrayData } from './normalize'

export const listEvents = (params?: { program_id?: string; institution_id?: string; event_type?: string; limit?: number }) =>
  apiClient.get('/events', { params }).then(r => toArrayData<any>(r.data))

export const rsvpEvent = (eventId: string) =>
  apiClient.post(`/events/${eventId}/rsvp`).then(r => r.data)

export const cancelRsvp = (eventId: string) =>
  apiClient.delete(`/events/${eventId}/rsvp`)

export const downloadIcs = (eventId: string) =>
  apiClient.get(`/events/${eventId}/calendar`, { responseType: 'blob' }).then(r => r.data)

export const getMyRsvps = () =>
  apiClient.get('/events/me/rsvps').then(r => toArrayData<any>(r.data))
