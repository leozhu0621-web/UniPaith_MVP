import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { School, Plus, UserPlus } from 'lucide-react'
import { listFairs, createFair, updateFair, captureLeads } from '../../../api/recruitment'
import type { RecruitmentFair } from '../../../types'
import Card from '../../../components/ui/Card'
import Table from '../../../components/ui/Table'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Toggle from '../../../components/ui/Toggle'
import EmptyState from '../../../components/ui/EmptyState'
import { showToast } from '../../../stores/toast-store'

export default function FairsTab() {
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [capture, setCapture] = useState<RecruitmentFair | null>(null)

  const { data: fairs, isLoading } = useQuery({
    queryKey: ['recruitment-fairs'],
    queryFn: listFairs,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['recruitment-fairs'] })
    qc.invalidateQueries({ queryKey: ['recruitment-prospects'] })
    qc.invalidateQueries({ queryKey: ['recruitment-summary'] })
  }

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateFair(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recruitment-fairs'] }),
  })

  const columns = [
    {
      key: 'name',
      label: 'School / fair',
      render: (f: RecruitmentFair) => (
        <div>
          <div className="font-medium text-foreground">{f.name}</div>
          <div className="text-xs text-muted-foreground">
            {f.kind === 'high_school' ? 'High school' : 'Fair'}
            {f.contact_name ? ` · ${f.contact_name}` : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'location',
      label: 'Location',
      render: (f: RecruitmentFair) => (
        <span className="text-sm text-muted-foreground">
          {[f.city, f.region, f.country].filter(Boolean).join(', ') || '—'}
        </span>
      ),
    },
    {
      key: 'yield',
      label: 'Prior-year yield',
      align: 'right' as const,
      render: (f: RecruitmentFair) =>
        f.prior_year_yield != null ? (
          <span className="font-medium tabular-nums text-foreground">{f.prior_year_yield}</span>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (f: RecruitmentFair) => (
        <Select
          uiSize="sm"
          options={[
            { value: 'prospective', label: 'Prospective' },
            { value: 'registered', label: 'Registered' },
            { value: 'confirmed', label: 'Confirmed' },
            { value: 'attended', label: 'Attended' },
            { value: 'skipped', label: 'Skipped' },
          ]}
          value={f.status}
          onClick={e => e.stopPropagation()}
          onChange={e => statusMut.mutate({ id: f.id, status: e.target.value })}
          className="!w-36"
        />
      ),
    },
    {
      key: 'actions',
      label: '',
      align: 'right' as const,
      render: (f: RecruitmentFair) => (
        <Button
          variant="tertiary"
          size="sm"
          onClick={e => {
            e.stopPropagation()
            setCapture(f)
          }}
        >
          <UserPlus size={14} /> Capture leads
        </Button>
      ),
    },
  ]

  if (!isLoading && (!fairs || fairs.length === 0)) {
    return (
      <>
        <Card className="p-0">
          <EmptyState
            icon={<School size={28} />}
            title="No schools or fairs yet"
            description="Build your directory of high schools and college fairs, then capture the prospects you meet."
            action={{ label: 'Add school or fair', onClick: () => setShowNew(true) }}
          />
        </Card>
        <FairModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
      </>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Schools &amp; fairs</h2>
        <Button variant="secondary" onClick={() => setShowNew(true)}>
          <Plus size={15} /> Add school or fair
        </Button>
      </div>

      <Card className="overflow-hidden p-0">
        <Table columns={columns} data={fairs ?? []} pageSize={25} density="compact" isLoading={isLoading} />
      </Card>

      <FairModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
      <CaptureModal fair={capture} onClose={() => setCapture(null)} onDone={invalidate} />
    </div>
  )
}

function FairModal({
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
    kind: 'fair',
    city: '',
    region: '',
    contact_name: '',
    contact_email: '',
    prior_year_yield: '',
  })
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const mut = useMutation({
    mutationFn: () =>
      createFair({
        name: form.name,
        kind: form.kind,
        city: form.city || null,
        region: form.region || null,
        contact_name: form.contact_name || null,
        contact_email: form.contact_email || null,
        prior_year_yield: form.prior_year_yield ? Number(form.prior_year_yield) : null,
      }),
    onSuccess: () => {
      showToast('Added to directory', 'success')
      setForm({ name: '', kind: 'fair', city: '', region: '', contact_name: '', contact_email: '', prior_year_yield: '' })
      onClose()
      onDone()
    },
    onError: () => showToast('Could not add', 'error'),
  })

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Add school or fair"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!form.name.trim()} onClick={() => mut.mutate()}>
            Add
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Name" value={form.name} onChange={e => set('name', e.target.value)} required />
        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Kind"
            options={[
              { value: 'fair', label: 'College fair' },
              { value: 'high_school', label: 'High school' },
            ]}
            value={form.kind}
            onChange={e => set('kind', e.target.value)}
          />
          <Input
            label="Prior-year yield"
            type="number"
            value={form.prior_year_yield}
            onChange={e => set('prior_year_yield', e.target.value)}
            placeholder="Enrolled last year"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="City" value={form.city} onChange={e => set('city', e.target.value)} />
          <Input label="Region" value={form.region} onChange={e => set('region', e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Contact name" value={form.contact_name} onChange={e => set('contact_name', e.target.value)} />
          <Input label="Contact email" type="email" value={form.contact_email} onChange={e => set('contact_email', e.target.value)} />
        </div>
      </div>
    </Modal>
  )
}

function CaptureModal({
  fair,
  onClose,
  onDone,
}: {
  fair: RecruitmentFair | null
  onClose: () => void
  onDone: () => void
}) {
  const [raw, setRaw] = useState('')
  const [consent, setConsent] = useState(false)

  const parse = () =>
    raw
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean)
      .map(line => {
        const [name, email] = line.split(',').map(s => s?.trim())
        return { name: name || email || 'Unknown', email: email || null, consent_outreach: consent }
      })

  const mut = useMutation({
    mutationFn: () => captureLeads(fair!.id, { leads: parse() }),
    onSuccess: res => {
      showToast(`Captured ${res.captured} · ${res.deduped} merged`, 'success')
      setRaw('')
      onClose()
      onDone()
    },
    onError: () => showToast('Capture failed', 'error'),
  })

  return (
    <Modal
      isOpen={!!fair}
      onClose={onClose}
      title={fair ? `Capture leads — ${fair.name}` : 'Capture leads'}
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!raw.trim()} onClick={() => mut.mutate()}>
            Capture
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          One lead per line as <code className="rounded bg-muted px-1">Name, email</code>. Each
          becomes a prospect tagged with this source and counted in attribution.
        </p>
        <Textarea
          label="Leads met"
          rows={7}
          placeholder={'Sam Carter, sam@example.com\nJordan Lee, jordan@example.com'}
          value={raw}
          onChange={e => setRaw(e.target.value)}
        />
        <Toggle checked={consent} onChange={setConsent} label="These leads opted in to outreach" />
      </div>
    </Modal>
  )
}
