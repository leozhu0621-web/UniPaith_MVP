import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Star, Plus, Edit2, Trash2, Play, Pause, Eye, MousePointerClick } from 'lucide-react'
import {
  getPromotions, createPromotion, updatePromotion, deletePromotion,
  getInstitutionPrograms,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime, formatDate } from '../../utils/format'
import type { Promotion, Program } from '../../types'

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  active: 'success',
  paused: 'warning',
  expired: 'neutral',
}

const TYPE_OPTIONS = [
  { value: 'spotlight', label: 'Spotlight' },
  { value: 'featured', label: 'Featured' },
  { value: 'banner', label: 'Banner' },
]

export default function PromotionsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Promotion | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Promotion | null>(null)

  // Form
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [promoType, setPromoType] = useState('spotlight')
  const [programId, setProgramId] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [targetRegions, setTargetRegions] = useState('')
  const [targetCountries, setTargetCountries] = useState('')
  const [targetDegrees, setTargetDegrees] = useState('')

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'active', label: 'Active' },
    { id: 'draft', label: 'Draft' },
    { id: 'paused', label: 'Paused' },
    { id: 'expired', label: 'Expired' },
  ]

  const promosQ = useQuery({ queryKey: ['promotions'], queryFn: getPromotions })
  const allPromos: Promotion[] = Array.isArray(promosQ.data) ? promosQ.data : []
  const promos = activeTab === 'all' ? allPromos : allPromos.filter(p => p.status === activeTab)

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const programOptions = [{ value: '', label: 'Institution-wide' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const resetForm = () => {
    setTitle(''); setDescription(''); setPromoType('spotlight'); setProgramId('')
    setStartsAt(''); setEndsAt(''); setTargetRegions(''); setTargetCountries(''); setTargetDegrees('')
    setEditTarget(null)
  }

  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (p: Promotion) => {
    setEditTarget(p)
    setTitle(p.title)
    setDescription(p.description || '')
    setPromoType(p.promotion_type)
    setProgramId(p.program_id || '')
    setStartsAt(p.starts_at ? p.starts_at.slice(0, 16) : '')
    setEndsAt(p.ends_at ? p.ends_at.slice(0, 16) : '')
    setTargetRegions(p.targeting?.regions?.join(', ') || '')
    setTargetCountries(p.targeting?.countries?.join(', ') || '')
    setTargetDegrees(p.targeting?.degree_types?.join(', ') || '')
    setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: createPromotion,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['promotions'] }); setShowModal(false); resetForm(); showToast('Promotion created', 'success') },
  })

  const updateMut = useMutation({
    mutationFn: (p: { id: string; payload: Parameters<typeof updatePromotion>[1] }) => updatePromotion(p.id, p.payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['promotions'] }); setShowModal(false); resetForm(); showToast('Promotion updated', 'success') },
  })

  const deleteMut = useMutation({
    mutationFn: deletePromotion,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['promotions'] }); setDeleteTarget(null); showToast('Promotion deleted', 'success') },
  })

  const statusMut = useMutation({
    mutationFn: (p: { id: string; status: string }) => updatePromotion(p.id, { status: p.status }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['promotions'] }); showToast('Status updated', 'success') },
  })

  const buildTargeting = () => {
    const t: Record<string, string[]> = {}
    if (targetRegions.trim()) t.regions = targetRegions.split(',').map(s => s.trim()).filter(Boolean)
    if (targetCountries.trim()) t.countries = targetCountries.split(',').map(s => s.trim()).filter(Boolean)
    if (targetDegrees.trim()) t.degree_types = targetDegrees.split(',').map(s => s.trim()).filter(Boolean)
    return Object.keys(t).length > 0 ? t : undefined
  }

  const handleSubmit = () => {
    if (!title.trim()) { showToast('Title is required', 'warning'); return }
    const payload = {
      title,
      description: description || undefined,
      promotion_type: promoType,
      program_id: programId || undefined,
      starts_at: startsAt ? new Date(startsAt).toISOString() : undefined,
      ends_at: endsAt ? new Date(endsAt).toISOString() : undefined,
      targeting: buildTargeting(),
    }
    if (editTarget) {
      updateMut.mutate({ id: editTarget.id, payload })
    } else {
      createMut.mutate(payload)
    }
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Promotions"
        description="Spotlight programs with featured placements, targeting scopes, and time-boxed visibility."
        actions={(
          <Button onClick={openCreate} className="flex items-center gap-2">
            <Plus size={16} /> New Promotion
          </Button>
        )}
      />

      {allPromos.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Total</p>
            <p className="text-xl font-semibold text-gray-900">{allPromos.length}</p>
          </Card>
          <Card className="p-3 border-green-200">
            <p className="text-xs text-green-600">Active</p>
            <p className="text-xl font-bold text-green-600">{allPromos.filter(p => p.status === 'active').length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500 flex items-center gap-1"><Eye size={12} /> Impressions</p>
            <p className="text-xl font-semibold text-gray-900">{allPromos.reduce((s, p) => s + p.impression_count, 0)}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500 flex items-center gap-1"><MousePointerClick size={12} /> Clicks</p>
            <p className="text-xl font-semibold text-gray-900">{allPromos.reduce((s, p) => s + p.click_count, 0)}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {promosQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : promos.length === 0 ? (
        <EmptyState
          icon={<Star size={40} />}
          title="No promotions"
          description="Create spotlight or featured placements to boost program visibility."
          action={{ label: 'New Promotion', onClick: openCreate }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {promos.map(p => (
            <Card key={p.id} className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{p.title}</h3>
                    <Badge variant={STATUS_BADGE[p.status] ?? 'neutral'}>{p.status}</Badge>
                    <Badge variant="info">{p.promotion_type}</Badge>
                  </div>
                  {p.program_name && <p className="text-xs text-gray-500 mt-1">Program: {p.program_name}</p>}
                </div>
                {!p.is_eligible && <Badge variant="warning">Ineligible</Badge>}
              </div>
              {p.description && <p className="text-sm text-gray-600 line-clamp-2 mb-2">{p.description}</p>}
              <div className="flex items-center gap-4 text-xs text-gray-400 mb-2">
                {p.starts_at && <span>From: {formatDate(p.starts_at)}</span>}
                {p.ends_at && <span>Until: {formatDate(p.ends_at)}</span>}
                <span className="flex items-center gap-1"><Eye size={11} /> {p.impression_count}</span>
                <span className="flex items-center gap-1"><MousePointerClick size={11} /> {p.click_count}</span>
              </div>
              {p.targeting && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {p.targeting.regions?.map(r => <Badge key={r} variant="neutral">{r}</Badge>)}
                  {p.targeting.countries?.map(c => <Badge key={c} variant="neutral">{c}</Badge>)}
                  {p.targeting.degree_types?.map(d => <Badge key={d} variant="info">{d}</Badge>)}
                </div>
              )}
              <div className="flex gap-2 mt-2">
                <Button variant="ghost" size="sm" onClick={() => openEdit(p)} className="flex items-center gap-1">
                  <Edit2 size={14} /> Edit
                </Button>
                {p.status === 'draft' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: p.id, status: 'active' })}
                    className="flex items-center gap-1 text-green-600">
                    <Play size={14} /> Activate
                  </Button>
                )}
                {p.status === 'active' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: p.id, status: 'paused' })}
                    className="flex items-center gap-1 text-amber-600">
                    <Pause size={14} /> Pause
                  </Button>
                )}
                {p.status === 'paused' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: p.id, status: 'active' })}
                    className="flex items-center gap-1 text-green-600">
                    <Play size={14} /> Resume
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(p)}
                  className="flex items-center gap-1 text-red-600">
                  <Trash2 size={14} />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm() }} title={editTarget ? 'Edit Promotion' : 'New Promotion'}>
        <div className="space-y-4">
          <Input label="Title *" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Spring 2026 Spotlight" />
          <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Brief description of this promotion..." />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Type" options={TYPE_OPTIONS} value={promoType} onChange={e => setPromoType(e.target.value)} />
            <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Start Date" type="datetime-local" value={startsAt} onChange={e => setStartsAt(e.target.value)} />
            <Input label="End Date" type="datetime-local" value={endsAt} onChange={e => setEndsAt(e.target.value)} />
          </div>

          <div className="border-t pt-3">
            <p className="text-sm font-medium text-gray-700 mb-2">Targeting Scope</p>
            <div className="space-y-2">
              <Input label="Regions (comma-separated)" value={targetRegions} onChange={e => setTargetRegions(e.target.value)} placeholder="e.g. North America, Europe" />
              <Input label="Countries (comma-separated)" value={targetCountries} onChange={e => setTargetCountries(e.target.value)} placeholder="e.g. United States, Canada" />
              <Input label="Degree Types (comma-separated)" value={targetDegrees} onChange={e => setTargetDegrees(e.target.value)} placeholder="e.g. masters, phd" />
            </div>
            <p className="text-xs text-gray-400 mt-1">Leave blank to show to all students.</p>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowModal(false); resetForm() }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Promotion">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <strong>{deleteTarget?.title}</strong>?
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
