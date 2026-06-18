import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Map, Plus, UserCheck, Sparkles, Check } from 'lucide-react'
import {
  getTerritoryDashboard,
  createTerritory,
  updateTerritory,
  optimizeTerritory,
} from '../../../api/recruitment'
import type { Territory, TerritorySuggestion } from '../../../types'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Modal from '../../../components/ui/Modal'
import Input from '../../../components/ui/Input'
import Skeleton from '../../../components/ui/Skeleton'
import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import AIBadge from '../../../components/ui/AIBadge'
import FallbackNote from '../../../components/ui/FallbackNote'
import { showToast } from '../../../stores/toast-store'
import { formatPercent } from '../../../utils/format'

function Kpi({ label, value }: { label: string; value: string | number }) {
  return (
    <Card pad={false} variant="card-flush" className="p-3">
      <div className="text-2xl font-semibold tabular-nums text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </Card>
  )
}

export default function TerritoriesTab() {
  const qc = useQueryClient()
  const [showNew, setShowNew] = useState(false)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['recruitment-territories'],
    queryFn: getTerritoryDashboard,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['recruitment-territories'] })
    qc.invalidateQueries({ queryKey: ['recruitment-summary'] })
  }

  if (isError) {
    return (
      <Card pad={false} className="p-0">
        <QueryError detail="Couldn’t load territories." onRetry={() => refetch()} />
      </Card>
    )
  }

  if (isLoading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {[0, 1, 2, 3].map(i => (
          <Skeleton key={i} className="h-36 w-full" />
        ))}
      </div>
    )
  }

  if (!data || data.territories.length === 0) {
    return (
      <>
        <Card pad={false} className="p-0">
          <EmptyState
            icon={<Map size={28} />}
            title="No territories yet"
            action={{ label: 'Create a territory', onClick: () => setShowNew(true) }}
          />
        </Card>
        <TerritoryModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
      </>
    )
  }

  const maxProspects = Math.max(1, ...data.territories.map(t => t.prospect_count))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Territories</h2>
        <Button variant="secondary" onClick={() => setShowNew(true)}>
          <Plus size={15} /> Create a territory
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Kpi label="Total prospects" value={data.total_prospects} />
        <Kpi label="Applicants" value={data.total_applicants} />
        <Kpi label="Conversion" value={formatPercent(data.overall_conversion_rate)} />
        <Kpi label="Unassigned" value={data.unassigned_count} />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {data.territories.map(t => (
          <TerritoryCard key={t.id} territory={t} maxProspects={maxProspects} onDone={invalidate} />
        ))}
      </div>

      <TerritoryModal open={showNew} onClose={() => setShowNew(false)} onDone={invalidate} />
    </div>
  )
}

function TerritoryCard({
  territory,
  maxProspects,
  onDone,
}: {
  territory: Territory
  maxProspects: number
  onDone: () => void
}) {
  const qc = useQueryClient()
  const [ownerInput, setOwnerInput] = useState('')
  const [suggestions, setSuggestions] = useState<TerritorySuggestion[] | null>(null)
  const [aiGenerated, setAiGenerated] = useState(false)

  const assignMut = useMutation({
    mutationFn: () => updateTerritory(territory.id, { owner_name: ownerInput }),
    onSuccess: () => {
      showToast('Owner assigned', 'success')
      qc.invalidateQueries({ queryKey: ['recruitment-territories'] })
      onDone()
    },
    onError: () => showToast('Could not assign owner', 'error'),
  })

  const optimizeMut = useMutation({
    mutationFn: () => optimizeTerritory(territory.id),
    onSuccess: res => {
      setSuggestions(res.suggestions)
      setAiGenerated(res.ai_generated)
    },
    onError: () => showToast('Could not load suggestions', 'error'),
  })

  return (
    <Card pad={false} className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-foreground">{territory.name}</h3>
          {territory.owner_name ? (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <UserCheck size={12} /> {territory.owner_name}
            </span>
          ) : (
            <Badge variant="warning">No owner</Badge>
          )}
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold tabular-nums text-foreground">
            {formatPercent(territory.conversion_rate)}
          </div>
          <div className="text-xs text-muted-foreground">conversion</div>
        </div>
      </div>

      <div className="mt-3 space-y-1.5">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{territory.prospect_count} prospects</span>
          <span>{territory.applicant_count} applicants</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-secondary"
            style={{ width: `${(territory.prospect_count / maxProspects) * 100}%` }}
          />
        </div>
      </div>

      {territory.unassigned && (
        <div className="mt-3 flex flex-wrap items-end gap-2 rounded-lg bg-warning-soft/50 p-2.5">
          <p className="w-full text-xs text-warning">This territory has no owner — assign one.</p>
          <Input
            uiSize="sm"
            placeholder="Recruiter name"
            value={ownerInput}
            onChange={e => setOwnerInput(e.target.value)}
            className="!w-44"
          />
          <Button
            variant="secondary"
            size="sm"
            disabled={!ownerInput.trim()}
            loading={assignMut.isPending}
            onClick={() => assignMut.mutate()}
          >
            <Check size={14} /> Assign
          </Button>
        </div>
      )}

      <div className="mt-3 border-t border-border pt-3">
        <Button
          variant="ghost"
          size="sm"
          loading={optimizeMut.isPending}
          onClick={() => optimizeMut.mutate()}
        >
          <Sparkles size={14} /> Optimize travel
        </Button>

        {suggestions && (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-2">
              <AIBadge fallback={!aiGenerated} label="TerritoryOptimizer" />
            </div>
            <ul className="space-y-1.5">
              {suggestions.map((s, i) => (
                <li key={i} className="rounded-lg bg-muted/50 p-2 text-sm">
                  <div className="font-medium text-foreground">{s.label}</div>
                  {s.rationale && <div className="text-xs text-muted-foreground">{s.rationale}</div>}
                </li>
              ))}
            </ul>
            {!aiGenerated && <FallbackNote>Showing rule-based suggestions.</FallbackNote>}
          </div>
        )}
      </div>
    </Card>
  )
}

function TerritoryModal({
  open,
  onClose,
  onDone,
}: {
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const [name, setName] = useState('')
  const [regions, setRegions] = useState('')
  const [owner, setOwner] = useState('')

  const mut = useMutation({
    mutationFn: () =>
      createTerritory({
        name,
        owner_name: owner || null,
        geo: regions
          ? { regions: regions.split(',').map(s => s.trim()).filter(Boolean) }
          : null,
      }),
    onSuccess: () => {
      showToast('Territory created', 'success')
      setName('')
      setRegions('')
      setOwner('')
      onClose()
      onDone()
    },
    onError: () => showToast('Could not create territory', 'error'),
  })

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Create a territory"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} disabled={!name.trim()} onClick={() => mut.mutate()}>
            Create
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input label="Territory name" value={name} onChange={e => setName(e.target.value)} placeholder="Northeast" required />
        <Input
          label="Regions"
          value={regions}
          onChange={e => setRegions(e.target.value)}
          placeholder="Comma-separated, e.g. MA, CT, RI"
        />
        <Input label="Owner (optional)" value={owner} onChange={e => setOwner(e.target.value)} placeholder="Recruiter name" />
      </div>
    </Modal>
  )
}
