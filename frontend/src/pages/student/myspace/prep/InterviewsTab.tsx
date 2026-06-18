/**
 * My Space › Prep › Interviews (Spec 2026-06-10 §5) — the consolidated
 * interview list the app never had: everything needing a response, everything
 * scheduled, and the past, in one place. Scheduling availability and
 * accommodations move here from Profile › Preparation (they exist to support
 * interviews and visits). Contextual respond panels elsewhere stay.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Accessibility, Clock, Pencil, Video, MapPin } from 'lucide-react'

import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import Card from '../../../../components/ui/Card'
import Modal from '../../../../components/ui/Modal'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import EmptyState from '../../../../components/ui/EmptyState'
import { getMyInterviews } from '../../../../api/interviews'
import { getAccommodations, getScheduling, upsertAccommodations, upsertScheduling } from '../../../../api/students'
import { showToast } from '../../../../stores/toast-store'
import { AccommodationForm, SchedulingForm } from '../../components/ProfileForms'
import { SectionHeader } from '../../profile/shared'
import InterviewRespondPanel from '../../interviews/InterviewRespondPanel'
import type { Interview } from '../../../../types'

const RESPOND_STATUSES = new Set(['proposed', 'reschedule_requested'])
const SCHEDULED_STATUSES = new Set(['scheduled', 'confirmed'])

function InterviewRow({ iv }: { iv: Interview }) {
  const when = iv.confirmed_time ?? iv.scheduled_at
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border py-2.5 last:border-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-foreground">{iv.program.name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {when ? new Date(when).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : iv.interview_type}
          {iv.duration_minutes ? ` · ${iv.duration_minutes} min` : ''}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {iv.meeting_link && (
          <a href={iv.meeting_link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
            <Video size={12} /> Join
          </a>
        )}
        {!iv.meeting_link && iv.location && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground"><MapPin size={12} /> {iv.location}</span>
        )}
        <Badge variant={SCHEDULED_STATUSES.has(String(iv.status)) ? 'success' : 'neutral'}>{String(iv.status).replace(/_/g, ' ')}</Badge>
      </div>
    </div>
  )
}

export default function InterviewsTab() {
  const qc = useQueryClient()
  const { data: interviews, isLoading, isError, refetch } = useQuery({ queryKey: ['interviews', 'prep'], queryFn: getMyInterviews })
  const { data: accommodations } = useQuery({ queryKey: ['accommodations'], queryFn: getAccommodations, retry: false })
  const { data: scheduling } = useQuery({ queryKey: ['scheduling'], queryFn: getScheduling, retry: false })
  const [modal, setModal] = useState<null | 'accommodations' | 'scheduling'>(null)

  const accommMut = useMutation({
    mutationFn: upsertAccommodations,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['accommodations'] }); setModal(null); showToast('Saved', 'success') },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })
  const schedMut = useMutation({
    mutationFn: upsertScheduling,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['scheduling'] }); setModal(null); showToast('Saved', 'success') },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const list: Interview[] = Array.isArray(interviews) ? interviews : []
  const needsResponse = list.filter(iv => RESPOND_STATUSES.has(String(iv.status)) && !iv.async_expired)
  const scheduled = list.filter(iv => SCHEDULED_STATUSES.has(String(iv.status)))
  const past = list.filter(iv => !RESPOND_STATUSES.has(String(iv.status)) && !SCHEDULED_STATUSES.has(String(iv.status)))

  return (
    <div className="w-full px-4 sm:px-6 py-6 space-y-10">
      <section>
        <SectionHeader title="Interviews" />
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-14" />
            <Skeleton className="h-14" />
          </div>
        ) : isError ? (
          <QueryError variant="inline" detail="We couldn't load your interviews." onRetry={() => refetch()} />
        ) : list.length === 0 ? (
          <EmptyState
            icon={<Video size={40} />}
            title="No interviews yet"
          />
        ) : (
          <div className="stagger-list space-y-6">
            {needsResponse.length > 0 && (
              <div>
                <p className="mb-2 text-eyebrow uppercase text-warning">Needs your response</p>
                <div className="space-y-3">
                  {needsResponse.map(iv => <InterviewRespondPanel key={iv.id} interview={iv} />)}
                </div>
              </div>
            )}
            {scheduled.length > 0 && (
              <div>
                <p className="mb-1 text-eyebrow uppercase text-muted-foreground">Scheduled</p>
                {scheduled.map(iv => <InterviewRow key={iv.id} iv={iv} />)}
              </div>
            )}
            {past.length > 0 && (
              <div>
                <p className="mb-1 text-eyebrow uppercase text-muted-foreground">Past & other</p>
                {past.map(iv => <InterviewRow key={iv.id} iv={iv} />)}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Scheduling availability — moved here from Profile › Preparation. */}
      <section>
        <SectionHeader
          title="Scheduling"
          action={<Button size="sm" variant="tertiary" onClick={() => setModal('scheduling')}><Pencil size={14} /> Edit</Button>}
        />
        <Card pad={false} className="p-5">
          {!scheduling ? (
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              <Clock size={16} /> No scheduling preferences set.
            </div>
          ) : (
            <dl className="grid sm:grid-cols-2 gap-3 text-sm">
              <div><dt className="text-muted-foreground">Timezone</dt><dd className="text-foreground">{scheduling.timezone || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Preferred format</dt><dd className="text-foreground">{scheduling.preferred_interview_format || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Campus visit</dt><dd className="text-foreground">{scheduling.campus_visit_interest ? 'Interested' : 'Not interested'}</dd></div>
              {scheduling.notes && <div className="sm:col-span-2"><dt className="text-muted-foreground">Notes</dt><dd className="text-foreground">{scheduling.notes}</dd></div>}
            </dl>
          )}
        </Card>
      </section>

      <section>
        <SectionHeader
          title="Accommodations"
          action={<Button size="sm" variant="tertiary" onClick={() => setModal('accommodations')}><Pencil size={14} /> Edit</Button>}
        />
        <Card pad={false} className="p-5">
          {!accommodations?.accommodations_needed ? (
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              <Accessibility size={16} /> No accommodations specified (optional).
            </div>
          ) : (
            <dl className="grid sm:grid-cols-2 gap-3 text-sm">
              <div><dt className="text-muted-foreground">Category</dt><dd className="text-foreground">{accommodations.category || '—'}</dd></div>
              <div><dt className="text-muted-foreground">Documentation</dt><dd className="text-foreground">{accommodations.documentation_status || '—'}</dd></div>
              {accommodations.details_text && <div className="sm:col-span-2"><dt className="text-muted-foreground">Details</dt><dd className="text-foreground">{accommodations.details_text}</dd></div>}
            </dl>
          )}
        </Card>
      </section>

      <Modal isOpen={modal === 'accommodations'} onClose={() => setModal(null)} title="Accommodations">
        <AccommodationForm defaultValues={accommodations || {}} loading={accommMut.isPending} onSubmit={(d: any) => accommMut.mutate(d)} />
      </Modal>
      <Modal isOpen={modal === 'scheduling'} onClose={() => setModal(null)} title="Scheduling & availability">
        <SchedulingForm defaultValues={scheduling || {}} loading={schedMut.isPending} onSubmit={(d: any) => schedMut.mutate(d)} />
      </Modal>
    </div>
  )
}
