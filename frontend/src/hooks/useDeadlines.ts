import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../api/applications'
import { getMyRsvps } from '../api/events'
import { getMyInterviews } from '../api/interviews'
import { parseISO } from 'date-fns'

export interface DeadlineItem {
  date: Date
  label: string
  sublabel?: string
  type: 'application' | 'event' | 'interview'
  link: string
}

export function useDeadlines() {
  const { data: applications, isLoading: appsLoading, isError: appsError } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })

  const { data: rsvps, isLoading: rsvpsLoading, isError: rsvpsError } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
  })

  const { data: interviews, isLoading: interviewsLoading, isError: interviewsError } = useQuery({
    queryKey: ['my-interviews'],
    queryFn: getMyInterviews,
  })

  const isLoading = appsLoading || rsvpsLoading || interviewsLoading
  const isError = appsError || rsvpsError || interviewsError

  const deadlines = useMemo(() => {
    const applicationsList: any[] = Array.isArray(applications) ? applications : []
    const rsvpsList: any[] = Array.isArray(rsvps) ? rsvps : []
    const interviewsList: any[] = Array.isArray(interviews) ? interviews : []
    const now = new Date()
    const items: DeadlineItem[] = []

    applicationsList.forEach((a: any) => {
      if (a.program?.application_deadline) {
        const d = parseISO(a.program.application_deadline)
        if (d >= now) {
          items.push({
            date: d,
            label: `${a.program.program_name} deadline`,
            sublabel: a.status === 'draft' ? 'Application not submitted yet' : `Status: ${a.status.replace(/_/g, ' ')}`,
            type: 'application',
            link: `/s/applications/${a.id}`,
          })
        }
      }
    })

    rsvpsList.forEach((r: any) => {
      if (r.event?.start_time) {
        const d = parseISO(r.event.start_time)
        if (d >= now) {
          items.push({
            date: d,
            label: r.event.event_name || 'Event',
            sublabel: r.event.location || r.event.event_type,
            type: 'event',
            link: '/s/calendar',
          })
        }
      }
    })

    interviewsList.forEach((i: any) => {
      const time = i.confirmed_time || i.proposed_times?.[0]
      if (time) {
        const d = parseISO(time)
        if (d >= now) {
          items.push({
            date: d,
            label: `Interview — ${i.interview_type || 'Video'}`,
            sublabel: i.status === 'confirmed' ? 'Confirmed' : 'Pending confirmation',
            type: 'interview',
            link: '/s/calendar',
          })
        }
      }
    })

    items.sort((a, b) => a.date.getTime() - b.date.getTime())
    return items
  }, [applications, rsvps, interviews])

  return { deadlines, isLoading, isError, applications, rsvps, interviews }
}
