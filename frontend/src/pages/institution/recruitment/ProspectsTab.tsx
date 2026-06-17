import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, UserPlus, Users, Search, ArrowRight, Send } from 'lucide-react'
import {
  listProspects,
  createProspect,
  updateProspect,
  convertProspect,
  importProspects,
  prospectsToSegment,
  type ProspectFilters,
  type ImportRow,
} from '../../../api/recruitment'
import type { Prospect } from '../../../types'
import Card from '../../../components/ui/Card'
import Table from '../../../components/ui/Table'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import Sheet from '../../../components/ui/Sheet'
import Select from '../../../components/ui/Select'
import Input from '../../../components/ui/Input'
import Textarea from '../../../components/ui/Textarea'
import Toggle from '../../../components/ui/Toggle'
import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import AIBadge from '../../../components/ui/AIBadge'
import FallbackNote from '../../../components/ui/FallbackNote'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import { STAGE_META, STAGE_OPTIONS, SOURCE_META, SOURCE_OPTIONS, BAND_META } from './constants'

function ConsentBadge({ on }: { on: boolean }) {
  return on ? (
    <Badge variant="success">Outreach OK</Badge>
  ) : (
    <Badge variant="neutral">No outreach</Badge>
  )
}

export default function ProspectsTab() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<ProspectFilters>({})
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [showImport, setShowImport] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [showSegment, setShowSegment] = useState(false)
  const [active, setActive] = useState<Prospect | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['recruitment-prospects', filters],
    queryFn: () => listProspects(filters),
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['recruitment-prospects'] })
    qc.invalidateQueries({ queryKey: ['recruitment-summary'] })
    qc.invalidateQueries({ queryKey: ['recruitment-territories'] })
  }

  const items = data?.items ?? []
  const hasAnyFilter = Boolean(filters.stage || filters.source || filters.search)

  const toggleSelect = (id: string) =>
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const columns = useMemo(
    () => [
      {
        key: 'select',
        label: '',
        render: (p: Prospect) => (
          <input
            type="checkbox"
            aria-label={`Select ${p.name}`}
            checked={selected.has(p.id)}
            onClick={e => e.stopPropagation()}
            onChange={() => toggleSelect(p.id)}
            className="h-4 w-4 rounded border-border accent-secondary"
          />
        ),
      },
      {
        key: 'name',
        label: 'Prospect',
        sortable: true,
        render: (p: Prospect) => (
          <div className="flex items-center gap-2">
            {p.priority_band && (
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${BAND_META[p.priority_band].dot}`}
                title={`${BAND_META[p.priority_band].label} lead`}
              />
            )}
            <div className="min-w-0">
              <div className="truncate font-medium text-foreground">{p.name}</div>
              {p.email && <div className="truncate text-xs text-muted-foreground">{p.email}</div>}
            </div>
          </div>
        ),
      },
      {
        key: 'location',
        label: 'Location',
        sortable: true,
        sortAccessor: (p: Prospect) => [p.city, p.region, p.country].filter(Boolean).join(', '),
        render: (p: Prospect) => (
          <span className="text-sm text-muted-foreground">
            {[p.city, p.region, p.country].filter(Boolean).join(', ') || '—'}
          </span>
        ),
      },
      {
        key: 'interests',
        label: 'Interests',
        render: (p: Prospect) =>
          p.interests && p.interests.length ? (
            <div className="flex flex-wrap gap-1">
              {p.interests.slice(0, 3).map(i => (
                <span key={i} className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                  {i}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          ),
      },
      {
        key: 'source',
        label: 'Source',
        render: (p: Prospect) => <Badge variant="neutral">{SOURCE_META[p.source]}</Badge>,
      },
      {
        key: 'stage',
        label: 'Stage',
        sortable: true,
        sortAccessor: (p: Prospect) => STAGE_META[p.stage].label,
        render: (p: Prospect) => (
          <Badge variant={STAGE_META[p.stage].tone}>{STAGE_META[p.stage].label}</Badge>
        ),
      },
      {
        key: 'consent',
        label: 'Consent',
        render: (p: Prospect) => <ConsentBadge on={p.consent_outreach} />,
      },
      {
        key: 'priority',
        label: 'Priority',
        align: 'right' as const,
        sortable: true,
        sortAccessor: (p: Prospect) => p.apply_likelihood,
        render: (p: Prospect) =>
          p.apply_likelihood != null ? (
            <span className="text-sm font-medium tabular-nums text-foreground">
              {Math.round(p.apply_likelihood * 100)}%
            </span>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          ),
      },
    ],
    [selected],
  )

  if (isError) {
    return (
      <Card pad={false} className="p-0">
        <QueryError detail="Couldn’t load prospects." onRetry={() => refetch()} />
      </Card>
    )
  }

  if (data && data.total === 0 && !hasAnyFilter) {
    return (
      <>
        <Card pad={false} className="p-0">
          <EmptyState
            icon={<Users size={28} />}
            title="No prospects yet"
            description="Import a prospect list or capture leads at a fair to start."
            action={{ label: 'Import prospects', onClick: () => setShowImport(true) }}
          />
        </Card>
        <ImportModal
          open={showImport}
          onClose={() => setShowImport(false)}
          onDone={invalidate}
        />
      </>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-foreground">Prospects</h2>
          <span className="text-sm text-muted-foreground">{data?.total ?? 0}</span>
          {data?.prioritized && <AIBadge label="Ranked by apply-likelihood" />}
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <Button variant="tertiary" onClick={() => setShowSegment(true)}>
              <Send size={15} /> Add {selected.size} to segment
            </Button>
          )}
          <Button variant="tertiary" onClick={() => setShowImport(true)}>
            <Upload size={15} /> Import
          </Button>
          <Button variant="secondary" onClick={() => setShowAdd(true)}>
            <UserPlus size={15} /> Add prospect
          </Button>
        </div>
      </div>

      {data?.prioritized && (
        <FallbackNote className="not-italic">
          Prospects ordered by ProspectPrioritizer apply-likelihood. Prioritization only — no
          selection decisions.
        </FallbackNote>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <Select
            label="Stage"
            uiSize="sm"
            options={[{ value: '', label: 'All stages' }, ...STAGE_OPTIONS]}
            value={filters.stage ?? ''}
            onChange={e => setFilters(f => ({ ...f, stage: e.target.value || undefined }))}
          />
        </div>
        <div className="w-40">
          <Select
            label="Source"
            uiSize="sm"
            options={[{ value: '', label: 'All sources' }, ...SOURCE_OPTIONS]}
            value={filters.source ?? ''}
            onChange={e => setFilters(f => ({ ...f, source: e.target.value || undefined }))}
          />
        </div>
        <div className="relative w-56">
          <Search size={15} className="absolute left-3 top-[34px] text-muted-foreground" />
          <Input
            label="Search"
            uiSize="sm"
            placeholder="Name or email"
            className="pl-9"
            value={filters.search ?? ''}
            onChange={e => setFilters(f => ({ ...f, search: e.target.value || undefined }))}
          />
        </div>
      </div>

      <Card pad={false} className="overflow-hidden p-0">
        <Table
          columns={columns}
          data={items}
          pageSize={25}
          density="compact"
          isLoading={isLoading}
          onRowClick={(p: Prospect) => setActive(p)}
          emptyMessage="No prospects match these filters."
        />
      </Card>

      <ImportModal open={showImport} onClose={() => setShowImport(false)} onDone={invalidate} />
      <AddProspectModal open={showAdd} onClose={() => setShowAdd(false)} onDone={invalidate} />
      <SegmentModal
        open={showSegment}
        count={selected.size}
        onClose={() => setShowSegment(false)}
        ids={[...selected]}
        onDone={() => {
          setSelected(new Set())
          invalidate()
        }}
      />
      <ProspectDrawer
        prospect={active}
        onClose={() => setActive(null)}
        onDone={invalidate}
        onConverted={appId => {
          if (appId) navigate(`/i/admissions/applicant/${appId}`)
        }}
      />
    </div>
  )
}

// ── Import modal ──────────────────────────────────────────────────────────

function ImportModal({
  open,
  onClose,
  onDone,
}: {
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const [raw, setRaw] = useState('')
  const [source, setSource] = useState('list')
  const [consent, setConsent] = useState(false)

  const parse = (): ImportRow[] =>
    raw
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .map(line => {
        const [name, email] = line.split(',').map(s => s?.trim())
        return { name: name || email || 'Unknown', email: email || null, consent_outreach: consent }
      })

  const mut = useMutation({
    mutationFn: () => importProspects({ source, rows: parse() }),
    onSuccess: res => {
      showToast(
        `Imported ${res.imported} · ${res.deduped} deduped · ${res.suppressed} suppressed`,
        'success',
      )
      setRaw('')
      onClose()
      onDone()
    },
    onError: () => showToast('Import failed', 'error'),
  })

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Import prospects"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            loading={mut.isPending}
            disabled={!raw.trim()}
            onClick={() => mut.mutate()}
          >
            Import
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          One prospect per line as <code className="rounded bg-muted px-1">Name, email</code>.
          Duplicates are merged by email and suppressed addresses are skipped for outreach.
        </p>
        <Textarea
          label="Prospects"
          rows={8}
          placeholder={'Ada Lovelace, ada@example.com\nGrace Hopper, grace@example.com'}
          value={raw}
          onChange={e => setRaw(e.target.value)}
        />
        <div className="w-44">
          <Select
            label="Source"
            options={SOURCE_OPTIONS}
            value={source}
            onChange={e => setSource(e.target.value)}
          />
        </div>
        <Toggle
          checked={consent}
          onChange={setConsent}
          label="These prospects opted in to marketing outreach"
        />
      </div>
    </Modal>
  )
}

// ── Add prospect modal ──────────────────────────────────────────────────────

function AddProspectModal({
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
    email: '',
    source: 'web',
    stage: 'prospect',
    interests: '',
    consent_outreach: false,
  })
  const set = (k: string, v: unknown) => setForm(f => ({ ...f, [k]: v }))

  const mut = useMutation({
    mutationFn: () =>
      createProspect({
        name: form.name,
        email: form.email || null,
        source: form.source as Prospect['source'],
        stage: form.stage as Prospect['stage'],
        interests: form.interests
          ? form.interests.split(',').map(s => s.trim()).filter(Boolean)
          : [],
        consent_outreach: form.consent_outreach,
      }),
    onSuccess: () => {
      showToast('Prospect added', 'success')
      setForm({ name: '', email: '', source: 'web', stage: 'prospect', interests: '', consent_outreach: false })
      onClose()
      onDone()
    },
    onError: () => showToast('Could not add prospect', 'error'),
  })

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Add prospect"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            loading={mut.isPending}
            disabled={!form.name.trim()}
            onClick={() => mut.mutate()}
          >
            Add
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Name" value={form.name} onChange={e => set('name', e.target.value)} required />
        <Input label="Email" type="email" value={form.email} onChange={e => set('email', e.target.value)} />
        <div className="grid grid-cols-2 gap-3">
          <Select label="Source" options={SOURCE_OPTIONS} value={form.source} onChange={e => set('source', e.target.value)} />
          <Select label="Stage" options={STAGE_OPTIONS} value={form.stage} onChange={e => set('stage', e.target.value)} />
        </div>
        <Input
          label="Interests"
          placeholder="Comma-separated, e.g. Computer Science, Design"
          value={form.interests}
          onChange={e => set('interests', e.target.value)}
        />
        <Toggle
          checked={form.consent_outreach}
          onChange={v => set('consent_outreach', v)}
          label="Opted in to marketing outreach"
        />
      </div>
    </Modal>
  )
}

// ── Add-to-segment modal ────────────────────────────────────────────────────

function SegmentModal({
  open,
  onClose,
  ids,
  count,
  onDone,
}: {
  open: boolean
  onClose: () => void
  ids: string[]
  count: number
  onDone: () => void
}) {
  const [name, setName] = useState('')
  const mut = useMutation({
    mutationFn: () => prospectsToSegment({ prospect_ids: ids, list_name: name }),
    onSuccess: res => {
      showToast(
        `${res.added} added · ${res.skipped_no_consent} no-consent · ${res.skipped_no_email} no-email`,
        'success',
      )
      setName('')
      onClose()
      onDone()
    },
    onError: () => showToast('Could not build the list', 'error'),
  })

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title={`Add ${count} prospects to a campaign list`}
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!name.trim()} onClick={() => mut.mutate()}>
            Create list
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Only prospects with an email and outreach consent are added — the rest are skipped to
          respect marketing consent.
        </p>
        <Input label="List name" value={name} onChange={e => setName(e.target.value)} placeholder="Warm leads — Fall" />
      </div>
    </Modal>
  )
}

// ── Prospect drawer ─────────────────────────────────────────────────────────

function ProspectDrawer({
  prospect,
  onClose,
  onDone,
  onConverted,
}: {
  prospect: Prospect | null
  onClose: () => void
  onDone: () => void
  onConverted: (appId: string | null) => void
}) {
  const qc = useQueryClient()
  const stageMut = useMutation({
    mutationFn: (stage: string) => updateProspect(prospect!.id, { stage: stage as Prospect['stage'] }),
    onSuccess: () => {
      showToast('Stage updated', 'success')
      qc.invalidateQueries({ queryKey: ['recruitment-prospects'] })
      onDone()
    },
    onError: () => showToast('Could not update stage', 'error'),
  })
  const consentMut = useMutation({
    mutationFn: (on: boolean) => updateProspect(prospect!.id, { consent_outreach: on }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recruitment-prospects'] })
      onDone()
    },
    onError: () => showToast('Could not update consent', 'error'),
  })
  const convertMut = useMutation({
    mutationFn: () => convertProspect(prospect!.id),
    onSuccess: p => {
      showToast('Converted to applicant', 'success')
      qc.invalidateQueries({ queryKey: ['recruitment-prospects'] })
      onDone()
      onClose()
      onConverted(p.converted_application_id)
    },
    onError: () => showToast('Could not convert prospect', 'error'),
  })

  if (!prospect) return null
  const converted = prospect.stage === 'applicant' || !!prospect.converted_application_id

  return (
    <Sheet isOpen={!!prospect} onClose={onClose} title={prospect.name}>
      <div className="space-y-5 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={STAGE_META[prospect.stage].tone}>{STAGE_META[prospect.stage].label}</Badge>
          <Badge variant="neutral">{SOURCE_META[prospect.source]}</Badge>
          <ConsentBadge on={prospect.consent_outreach} />
          {converted && <Badge variant="success">Converted to applicant</Badge>}
        </div>

        <dl className="space-y-2 text-sm">
          {prospect.email && <Row k="Email" v={prospect.email} />}
          {prospect.phone && <Row k="Phone" v={prospect.phone} />}
          <Row
            k="Location"
            v={[prospect.city, prospect.region, prospect.country].filter(Boolean).join(', ') || '—'}
          />
          {prospect.source_detail && <Row k="Source detail" v={prospect.source_detail} />}
          <Row k="Added" v={formatDate(prospect.created_at)} />
          {prospect.interests && prospect.interests.length > 0 && (
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">Interests</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {prospect.interests.map(i => (
                  <span key={i} className="rounded bg-muted px-1.5 py-0.5 text-xs">
                    {i}
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>

        {prospect.apply_likelihood != null && (
          <Card pad={false} variant="card-flush" className="space-y-1 p-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-sm font-medium">
                <AIBadge label="Apply-likelihood" /> {Math.round(prospect.apply_likelihood * 100)}%
              </span>
            </div>
            {prospect.priority_reason && (
              <p className="text-xs text-muted-foreground">{prospect.priority_reason}</p>
            )}
          </Card>
        )}

        <div className="space-y-3 border-t border-border pt-4">
          <div className="w-full">
            <Select
              label="Stage"
              options={STAGE_OPTIONS}
              value={prospect.stage}
              onChange={e => stageMut.mutate(e.target.value)}
            />
          </div>
          <Toggle
            checked={prospect.consent_outreach}
            onChange={v => consentMut.mutate(v)}
            label="Marketing outreach consent"
          />
          {!converted && (
            <Button
              variant="secondary"
              className="w-full"
              loading={convertMut.isPending}
              onClick={() => convertMut.mutate()}
            >
              Mark as applicant <ArrowRight size={15} />
            </Button>
          )}
          {converted && prospect.converted_application_id && (
            <Button
              variant="tertiary"
              className="w-full"
              onClick={() => onConverted(prospect.converted_application_id)}
            >
              View application <ArrowRight size={15} />
            </Button>
          )}
        </div>
      </div>
    </Sheet>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="shrink-0 text-xs uppercase tracking-wide text-muted-foreground">{k}</dt>
      <dd className="truncate text-right text-foreground">{v}</dd>
    </div>
  )
}
