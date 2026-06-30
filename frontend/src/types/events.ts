// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === EVENTS ===
export interface EventItem {
  id: string
  institution_id: string
  program_id: string | null
  event_name: string
  event_type: 'webinar' | 'campus_visit' | 'info_session' | 'workshop'
  description: string | null
  location: string | null
  start_time: string
  end_time: string
  meeting_link?: string | null
  capacity: number | null
  rsvp_count: number
  // Spec 27 §3.1 — confirmed vs waitlisted split + impressions.
  confirmed_count?: number
  waitlist_count?: number
  view_count?: number
  status: string
}

export interface RSVP {
  id: string
  event_id: string
  student_id: string
  rsvp_status: string
  registered_at: string
  attended_at: string | null
  // Spec 27 §3.1 — attendance capture + roster identity.
  attendance_status?: string | null
  student_name?: string | null
  student_email?: string | null
}
