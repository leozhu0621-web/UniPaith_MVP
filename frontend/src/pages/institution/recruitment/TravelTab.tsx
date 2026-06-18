import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plane, AlertTriangle, CalendarClock, Plus, MapPin, Wallet } from 'lucide-react'
import {
  listTrips,
  createTrip,
  addTripVisit,
  updateTripVisit,
} from '../../../api/recruitment'
import type { RecruitmentTrip, TripVisit } from '../../../types'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Skeleton from '../../../components/ui/Skeleton'
import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import { formatDate, formatCurrency } from '../../../utils/format'

const VISIT_STATUS: Record<string, 'neutral' | 'info' | 'success'> = {
  planned: 'neutral',
  confirmed: 'info',
  done: 'success',
}

export default function TravelTab() {
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [visitFor, setVisitFor] = useState<RecruitmentTrip | null>(null)

  const { data: trips, isLoading, isError, refetch } = useQuery({
    queryKey: ['recruitment-trips'],
    queryFn: listTrips,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['recruitment-trips'] })
    qc.invalidateQueries({ queryKey: ['recruitment-summary'] })
  }

  if (isError) {
    return (
      <Card pad={false} className="p-0">
        <QueryError detail="Couldn’t load travel plans." onRetry={() => refetch()} />
      </Card>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1].map(i => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    )
  }

  if (!trips || trips.length === 0) {
    return (
      <>
        <Card pad={false} className="p-0">
          <EmptyState
            icon={<Plane size={28} />}
            title="No trips planned"
            action={{ label: 'Plan a trip', onClick: () => setShowNew(true) }}
          />
        </Card>
        <TripModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
      </>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Travel calendar</h2>
        <Button variant="secondary" onClick={() => setShowNew(true)}>
          <Plus size={15} /> Plan a trip
        </Button>
      </div>

      <div className="space-y-3">
        {trips.map(trip => (
          <TripCard key={trip.id} trip={trip} onAddVisit={() => setVisitFor(trip)} onDone={invalidate} />
        ))}
      </div>

      <TripModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
      <VisitModal trip={visitFor} onClose={() => setVisitFor(null)} onDone={invalidate} />
    </div>
  )
}

function TripCard({
  trip,
  onAddVisit,
  onDone,
}: {
  trip: RecruitmentTrip
  onAddVisit: () => void
  onDone: () => void
}) {
  const qc = useQueryClient()
  const visitMut = useMutation({
    mutationFn: ({ visitId, status }: { visitId: string; status: string }) =>
      updateTripVisit(trip.id, visitId, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recruitment-trips'] })
      onDone()
    },
    onError: () => showToast('Could not update visit', 'error'),
  })

  const cycle = (v: TripVisit) => {
    const next = v.status === 'planned' ? 'confirmed' : v.status === 'confirmed' ? 'done' : 'planned'
    visitMut.mutate({ visitId: v.id, status: next })
  }

  return (
    <Card pad={false} className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground">{trip.name}</h3>
            {trip.over_budget && (
              <Badge variant="warning">
                <Wallet size={11} /> Over budget
              </Badge>
            )}
            {trip.conflict && (
              <Badge variant="danger">
                <AlertTriangle size={11} /> Date conflict
              </Badge>
            )}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <CalendarClock size={13} />
              {formatDate(trip.start_date)} – {formatDate(trip.end_date)}
            </span>
            {trip.region && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={13} /> {trip.region}
              </span>
            )}
            {trip.recruiter_name && <span>Recruiter: {trip.recruiter_name}</span>}
          </div>
        </div>
        <Badge variant="neutral">{trip.status}</Badge>
      </div>

      {trip.budget != null && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Spend {formatCurrency(trip.spend)} of {formatCurrency(trip.budget)}
            </span>
            <span>{Math.round((Number(trip.spend) / Number(trip.budget || 1)) * 100)}%</span>
          </div>
          <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full ${trip.over_budget ? 'bg-warning' : 'bg-secondary'}`}
              style={{ width: `${Math.min(100, (Number(trip.spend) / Number(trip.budget || 1)) * 100)}%` }}
            />
          </div>
        </div>
      )}

      <div className="mt-3 border-t border-border pt-3">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Visits ({trip.visits.length})
          </span>
          <Button variant="ghost" size="sm" onClick={onAddVisit}>
            <Plus size={14} /> Add visit
          </Button>
        </div>
        {trip.visits.length === 0 ? (
          <p className="text-sm text-muted-foreground">No visits yet.</p>
        ) : (
          <ul className="space-y-1.5">
            {trip.visits.map(v => (
              <li key={v.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="flex items-center gap-2">
                  <span className="text-muted-foreground">{v.kind === 'fair' ? 'Fair' : 'School'}</span>
                  <span className="font-medium text-foreground">{v.name}</span>
                  {v.visit_date && (
                    <span className="text-xs text-muted-foreground">{formatDate(v.visit_date)}</span>
                  )}
                  {v.prospects_met > 0 && (
                    <span className="text-xs text-muted-foreground">· {v.prospects_met} met</span>
                  )}
                </span>
                <button
                  onClick={() => cycle(v)}
                  className="ui-btn"
                  title="Cycle status"
                  aria-label={`Cycle status for ${v.name}`}
                >
                  <Badge variant={VISIT_STATUS[v.status]}>{v.status}</Badge>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  )
}

function TripModal({
  open,
  onClose,
  onDone,
}: {
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const [form, setForm] = useState({
    name: '',
    region: '',
    start_date: '',
    end_date: '',
    recruiter_name: '',
    budget: '',
    spend: '',
  })
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const mut = useMutation({
    mutationFn: () =>
      createTrip({
        name: form.name,
        region: form.region || null,
        start_date: form.start_date,
        end_date: form.end_date,
        recruiter_name: form.recruiter_name || null,
        budget: form.budget ? Number(form.budget) : null,
        spend: form.spend ? Number(form.spend) : 0,
      }),
    onSuccess: () => {
      showToast('Trip planned', 'success')
      setForm({ name: '', region: '', start_date: '', end_date: '', recruiter_name: '', budget: '', spend: '' })
      onClose()
      onDone()
    },
    onError: () => showToast('Could not create trip', 'error'),
  })

  const valid = form.name.trim() && form.start_date && form.end_date

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Plan a trip"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!valid} onClick={() => mut.mutate()}>
            Create trip
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Trip name" value={form.name} onChange={e => set('name', e.target.value)} required />
        <Input label="Region" value={form.region} onChange={e => set('region', e.target.value)} placeholder="e.g. New England" />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Start date" type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)} required />
          <Input label="End date" type="date" value={form.end_date} onChange={e => set('end_date', e.target.value)} required />
        </div>
        <Input label="Recruiter" value={form.recruiter_name} onChange={e => set('recruiter_name', e.target.value)} />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Budget" type="number" min={0} value={form.budget} onChange={e => set('budget', e.target.value)} placeholder="0" />
          <Input label="Spend" type="number" min={0} value={form.spend} onChange={e => set('spend', e.target.value)} placeholder="0" />
        </div>
      </div>
    </Modal>
  )
}

function VisitModal({
  trip,
  onClose,
  onDone,
}: {
  trip: RecruitmentTrip | null
  onClose: () => void
  onDone: () => void
}) {
  const [form, setForm] = useState({ kind: 'school', name: '', visit_date: '', status: 'planned' })
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const mut = useMutation({
    mutationFn: () =>
      addTripVisit(trip!.id, {
        kind: form.kind,
        name: form.name,
        visit_date: form.visit_date || null,
        status: form.status,
      }),
    onSuccess: () => {
      showToast('Visit added', 'success')
      setForm({ kind: 'school', name: '', visit_date: '', status: 'planned' })
      onClose()
      onDone()
    },
    onError: () => showToast('Could not add visit', 'error'),
  })

  return (
    <Modal
      isOpen={!!trip}
      onClose={onClose}
      title={trip ? `Add a visit to ${trip.name}` : 'Add visit'}
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!form.name.trim()} onClick={() => mut.mutate()}>
            Add visit
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Kind"
            options={[
              { value: 'school', label: 'High school' },
              { value: 'fair', label: 'Fair' },
            ]}
            value={form.kind}
            onChange={e => set('kind', e.target.value)}
          />
          <Input label="Date" type="date" value={form.visit_date} onChange={e => set('visit_date', e.target.value)} />
        </div>
        <Input label="Name" value={form.name} onChange={e => set('name', e.target.value)} placeholder="Lincoln High School" required />
        <Select
          label="Status"
          options={[
            { value: 'planned', label: 'Planned' },
            { value: 'confirmed', label: 'Confirmed' },
            { value: 'done', label: 'Done' },
          ]}
          value={form.status}
          onChange={e => set('status', e.target.value)}
        />
      </div>
    </Modal>
  )
}
