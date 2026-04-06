import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProgram } from '../../api/programs'
import { getMatchDetail, logEngagement } from '../../api/matching'
import { listEvents, rsvpEvent } from '../../api/events'
import { listMyApplications, createApplication } from '../../api/applications'
import { saveProgram, unsaveProgram, listSaved } from '../../api/saved-lists'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatPercent, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import { ArrowLeft, Heart, HeartOff, MessageSquare } from 'lucide-react'
import type { Program, MatchResult, EventItem } from '../../types'

export default function SchoolDetailPage() {
  const { programId } = useParams<{ programId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('overview')

  const { data: program, isLoading } = useQuery({
    queryKey: ['program', programId],
    queryFn: () => getProgram(programId!),
  })

  const { data: matchResult } = useQuery({
    queryKey: ['match', programId],
    queryFn: () => getMatchDetail(programId!),
    retry: false,
  })

  const { data: events } = useQuery({
    queryKey: ['events', { program_id: programId }],
    queryFn: () => listEvents({ program_id: programId, limit: 5 }),
  })

  const { data: saved } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const savedList: any[] = Array.isArray(saved) ? saved : []
  const isSaved = savedList.some((s: any) => s.program_id === programId)

  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
  const applicationsList: any[] = Array.isArray(applications) ? applications : []
  const existingApp = applicationsList.find((a: any) => a.program_id === programId)
  const eventsList: EventItem[] = Array.isArray(events) ? events : []

  useEffect(() => {
    if (programId) logEngagement(programId, 'viewed_program', 1).catch(() => {})
    const start = Date.now()
    return () => {
      const secs = Math.round((Date.now() - start) / 1000)
      if (programId && secs > 5) logEngagement(programId, 'time_spent', secs).catch(() => {})
    }
  }, [programId])

  const saveMut = useMutation({
    mutationFn: () => isSaved ? unsaveProgram(programId!) : saveProgram(programId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saved'] }),
  })

  const applyMut = useMutation({
    mutationFn: () => createApplication(programId!),
    onSuccess: (app) => { showToast('Application created', 'success'); navigate(`/s/applications/${app.id}`) },
  })

  const rsvpMut = useMutation({
    mutationFn: rsvpEvent,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['events'] }); showToast('RSVP confirmed', 'success') },
  })
  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
  if (!program) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-sm text-gray-600 mb-3">Program details are unavailable right now.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/discover')}>
          Back to Discover
        </Button>
      </div>
    )
  }

  const p: Program = program
  const match: MatchResult | null = matchResult ?? null
  const tierInfo = match ? TIER_LABELS[match.match_tier] : null

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <button onClick={() => navigate('/s/discover')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Back to Discover
      </button>

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">{p.program_name}</h1>
          <p className="text-gray-500">{p.department || ''}</p>
          {match && tierInfo && (
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={tierInfo.color as any}>{tierInfo.label}</Badge>
              <span className="text-lg font-bold">{formatScore(match.match_score)} fit</span>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => saveMut.mutate()} loading={saveMut.isPending}>
            {isSaved ? <><HeartOff size={14} className="mr-1" /> Unsave</> : <><Heart size={14} className="mr-1" /> Save</>}
          </Button>
          {existingApp ? (
            <Button onClick={() => navigate(`/s/applications/${existingApp.id}`)}>View Application</Button>
          ) : (
            <Button onClick={() => applyMut.mutate()} loading={applyMut.isPending}>Apply</Button>
          )}
        </div>
      </div>

      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'requirements', label: 'Requirements' },
          { id: 'match', label: 'Match Analysis' },
        ]}
        activeTab={tab}
        onChange={setTab}
      />

      <div className="mt-6">
        {tab === 'overview' && (
          <div className="space-y-4">
            {p.description_text && <p className="text-sm text-gray-700">{p.description_text}</p>}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500">Degree:</span> {DEGREE_LABELS[p.degree_type] || p.degree_type}</div>
              <div><span className="text-gray-500">Duration:</span> {p.duration_months ? `${p.duration_months} months` : '—'}</div>
              <div><span className="text-gray-500">Tuition:</span> {formatCurrency(p.tuition)}</div>
              <div><span className="text-gray-500">Acceptance Rate:</span> {formatPercent(p.acceptance_rate, 1)}</div>
              <div><span className="text-gray-500">Deadline:</span> {formatDate(p.application_deadline)}</div>
              <div><span className="text-gray-500">Start:</span> {formatDate(p.program_start_date)}</div>
            </div>
            {p.highlights?.length ? (
              <div>
                <h3 className="font-medium text-sm mb-2">Highlights</h3>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {p.highlights.map((h, i) => <li key={i}>{h}</li>)}
                </ul>
              </div>
            ) : null}
          </div>
        )}

        {tab === 'requirements' && (
          <div>
            {p.requirements && Object.keys(p.requirements).length > 0 ? (
              <dl className="space-y-2 text-sm">
                {Object.entries(p.requirements).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-gray-100 pb-2">
                    <dt className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</dt>
                    <dd className="font-medium">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-gray-500">No specific requirements listed.</p>
            )}
          </div>
        )}

        {tab === 'match' && (
          <div>
            {match ? (
              <div className="space-y-4">
                {match.score_breakdown && Object.entries(match.score_breakdown).map(([k, v]) => (
                  <div key={k}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                      <span>{formatScore(v)}</span>
                    </div>
                    <ProgressBar value={v * 100} />
                  </div>
                ))}
                {match.reasoning_text && (
                  <div className="mt-4">
                    <h3 className="font-medium text-sm mb-2">AI Explanation</h3>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{match.reasoning_text}</p>
                  </div>
                )}
                <div className="mt-4 border-t pt-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-500">Want to understand this match better?</p>
                    <Button size="sm" variant="secondary" onClick={() => navigate('/s/chat')}>
                      <MessageSquare size={14} className="mr-1" /> Ask Counselor
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No match analysis available. Complete your profile to see how you fit.</p>
            )}
          </div>
        )}
      </div>

      {/* Events */}
      {eventsList.length > 0 && (
        <div className="mt-8">
          <h3 className="font-medium text-sm mb-3">Upcoming Events</h3>
          <div className="space-y-2">
            {eventsList.map((e: EventItem) => (
              <Card key={e.id} className="p-3 flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">{e.event_name}</p>
                  <p className="text-xs text-gray-500">{formatDate(e.start_time)}</p>
                </div>
                <Button size="sm" variant="secondary" onClick={() => rsvpMut.mutate(e.id)}>RSVP</Button>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
