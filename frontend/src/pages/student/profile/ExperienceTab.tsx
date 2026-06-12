/**
 * Profile → Experience tab (Spec/08 §7).
 * Activities · Work & Service · Competitions · Portfolio · Online Presence.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Briefcase, ExternalLink, FolderOpen, Pencil, Plus, Trophy, Trash2 } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import {
  createActivity,
  createCompetition,
  createOnlinePresence,
  createPortfolioItem,
  createWorkExperience,
  deleteActivity,
  deleteCompetition,
  deleteOnlinePresence,
  deletePortfolioItem,
  deleteWorkExperience,
  getProfile,
  listCompetitions,
  listWorkExperiences,
  updateActivity,
  updateCompetition,
  updateOnlinePresence,
  updatePortfolioItem,
  updateWorkExperience,
} from '../../../api/students'
import { confirmDialog } from '../../../stores/confirm-store'
import { showToast } from '../../../stores/toast-store'
import { formatDate } from '../../../utils/format'
import { ACTIVITY_TYPES, PLATFORM_TYPES, PORTFOLIO_ITEM_TYPES } from '../../../utils/constants'
import {
  ActivityForm,
  CompetitionForm,
  OnlinePresenceForm,
  PortfolioItemForm,
  WorkExperienceForm,
} from '../components/ProfileForms'
import { SectionHeader } from './shared'

/**
 * Normalize a user-supplied URL to a safe http(s) href, or null if it can't be
 * trusted. Guards against `javascript:`, `data:`, and other script-bearing
 * schemes that would otherwise execute when rendered in an anchor's href.
 */
function safeUrl(raw: unknown): string | null {
  if (typeof raw !== 'string') return null
  const trimmed = raw.trim()
  if (!trimmed) return null
  // Bare domains (no scheme) — assume https.
  const candidate = /^[a-zA-Z][a-zA-Z\d+.-]*:/.test(trimmed) ? trimmed : `https://${trimmed}`
  try {
    const parsed = new URL(candidate)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : null
  } catch {
    return null
  }
}

function RowActions({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  return (
    <div className="flex gap-0.5 shrink-0">
      <Button size="sm" variant="ghost" onClick={onEdit}>
        <Pencil size={12} />
      </Button>
      <Button size="sm" variant="ghost" onClick={onDelete}>
        <Trash2 size={12} />
      </Button>
    </div>
  )
}

export default function ExperienceTab() {
  const qc = useQueryClient()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: workExperiences } = useQuery({ queryKey: ['work-experiences'], queryFn: listWorkExperiences })
  const { data: competitions } = useQuery({ queryKey: ['competitions'], queryFn: listCompetitions })
  const [modal, setModal] = useState<null | 'activity' | 'work' | 'competition' | 'portfolio' | 'online'>(null)
  const [editItem, setEditItem] = useState<any>(null)

  const invProfile = () => qc.invalidateQueries({ queryKey: ['profile'] })
  const open = (kind: typeof modal, item: any = null) => {
    setEditItem(item)
    setModal(kind)
  }
  const close = () => setModal(null)
  const ok = (msg: string, key?: string) => {
    if (key) qc.invalidateQueries({ queryKey: [key] })
    else invProfile()
    setModal(null)
    showToast(msg, 'success')
  }
  const onErr = () => showToast("Something didn't work. Try again.", 'error')

  // Gate every destructive delete behind a confirm dialog (mirrors IdentityTab).
  const confirmDelete = async (thing: string, run: () => void) => {
    const okToDelete = await confirmDialog({
      title: `Delete ${thing}?`,
      body: "This can't be undone.",
      confirmLabel: 'Delete',
      destructive: true,
    })
    if (!okToDelete) return
    run()
  }

  const actCreate = useMutation({ mutationFn: createActivity, onSuccess: () => ok('Activity added'), onError: onErr })
  const actUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateActivity(id, data), onSuccess: () => ok('Activity updated'), onError: onErr })
  const actDelete = useMutation({ mutationFn: deleteActivity, onSuccess: () => { invProfile(); showToast('Activity removed', 'success') }, onError: onErr })
  const weCreate = useMutation({ mutationFn: createWorkExperience, onSuccess: () => ok('Experience added', 'work-experiences'), onError: onErr })
  const weUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateWorkExperience(id, data), onSuccess: () => ok('Experience updated', 'work-experiences'), onError: onErr })
  const weDelete = useMutation({ mutationFn: deleteWorkExperience, onSuccess: () => { qc.invalidateQueries({ queryKey: ['work-experiences'] }); showToast('Experience removed', 'success') }, onError: onErr })
  const compCreate = useMutation({ mutationFn: createCompetition, onSuccess: () => ok('Competition added', 'competitions'), onError: onErr })
  const compUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateCompetition(id, data), onSuccess: () => ok('Competition updated', 'competitions'), onError: onErr })
  const compDelete = useMutation({ mutationFn: deleteCompetition, onSuccess: () => { qc.invalidateQueries({ queryKey: ['competitions'] }); showToast('Competition removed', 'success') }, onError: onErr })
  const pfCreate = useMutation({ mutationFn: createPortfolioItem, onSuccess: () => ok('Item added'), onError: onErr })
  const pfUpdate = useMutation({ mutationFn: ({ id, data }: any) => updatePortfolioItem(id, data), onSuccess: () => ok('Item updated'), onError: onErr })
  const pfDelete = useMutation({ mutationFn: deletePortfolioItem, onSuccess: () => { invProfile(); showToast('Item removed', 'success') }, onError: onErr })
  const opCreate = useMutation({ mutationFn: createOnlinePresence, onSuccess: () => ok('Link added'), onError: onErr })
  const opUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateOnlinePresence(id, data), onSuccess: () => ok('Link updated'), onError: onErr })
  const opDelete = useMutation({ mutationFn: deleteOnlinePresence, onSuccess: () => { invProfile(); showToast('Link removed', 'success') }, onError: onErr })

  if (isLoading || !profile) return <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const p: any = profile
  const activities: any[] = p.activities ?? []
  const portfolio: any[] = p.portfolio_items ?? []
  const online: any[] = p.online_presence ?? []
  const work: any[] = Array.isArray(workExperiences) ? workExperiences : []
  const comps: any[] = Array.isArray(competitions) ? competitions : []

  return (
    <div className="space-y-10">
      {/* Activities */}
      <section>
        <SectionHeader title="Activities" description="Clubs, leadership, and extracurriculars." action={<Button size="sm" onClick={() => open('activity')}><Plus size={14} /> Add activity</Button>} />
        {activities.length === 0 ? (
          <EmptyState title="No activities yet" description="Add your first to surface relevant programs." action={{ label: 'Add an activity', onClick: () => open('activity') }} />
        ) : (
          <div className="space-y-2">
            {activities.map(act => (
              <Card pad={false} key={act.id} className="p-4 flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-medium text-foreground">{act.title}{act.organization ? ` — ${act.organization}` : ''}</p>
                  <p className="text-sm text-muted-foreground">
                    {ACTIVITY_TYPES.find(t => t.value === act.activity_type)?.label || act.activity_type}
                    {act.start_date ? ` · ${act.start_date.slice(0, 7)}–${act.is_current ? 'Present' : act.end_date?.slice(0, 7) ?? ''}` : ''}
                    {act.hours_per_week ? ` · ${act.hours_per_week} hrs/wk` : ''}
                  </p>
                </div>
                <RowActions onEdit={() => open('activity', act)} onDelete={() => confirmDelete('activity', () => actDelete.mutate(act.id))} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Work & Service */}
      <section>
        <SectionHeader title="Work & service" description="Internships, jobs, volunteering, and fellowships." action={<Button size="sm" onClick={() => open('work')}><Plus size={14} /> Add experience</Button>} />
        {work.length === 0 ? (
          <EmptyState title="No work or service yet" description="Add internships, part-time roles, or volunteering." action={{ label: 'Add experience', onClick: () => open('work') }} />
        ) : (
          <div className="space-y-2">
            {work.map(w => (
              <Card pad={false} key={w.id} className="p-4 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5 min-w-0">
                  <Briefcase size={16} className="text-muted-foreground mt-0.5" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">{w.role_title} at {w.organization}</p>
                    <p className="text-sm text-muted-foreground">
                      {w.experience_type}{w.is_current ? ' · Current' : ''}{w.start_date ? ` · ${formatDate(w.start_date)}` : ''}{w.end_date ? ` – ${formatDate(w.end_date)}` : ''}
                    </p>
                    {w.description && <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{w.description}</p>}
                  </div>
                </div>
                <RowActions onEdit={() => open('work', w)} onDelete={() => confirmDelete('experience', () => weDelete.mutate(w.id))} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Competitions */}
      <section>
        <SectionHeader title="Competitions" description="Hackathons, olympiads, and contests." action={<Button size="sm" onClick={() => open('competition')}><Plus size={14} /> Add competition</Button>} />
        {comps.length === 0 ? (
          <EmptyState title="No competitions yet" description="Add hackathons, olympiads, or other contests you've entered." action={{ label: 'Add a competition', onClick: () => open('competition') }} />
        ) : (
          <div className="space-y-2">
            {comps.map(c => (
              <Card pad={false} key={c.id} className="p-4 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5 min-w-0">
                  <Trophy size={16} className="text-muted-foreground mt-0.5" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">{c.competition_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {c.level}{c.result_placement ? ` · ${c.result_placement}` : ''}{c.year ? ` · ${c.year}` : ''}{c.domain ? ` · ${c.domain}` : ''}
                    </p>
                  </div>
                </div>
                <RowActions onEdit={() => open('competition', c)} onDelete={() => confirmDelete('competition', () => compDelete.mutate(c.id))} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Portfolio */}
      <section>
        <SectionHeader title="Portfolio" description="Projects and work samples." action={<Button size="sm" onClick={() => open('portfolio')}><Plus size={14} /> Add piece</Button>} />
        {portfolio.length === 0 ? (
          <EmptyState title="No portfolio pieces yet" description="Showcase projects, writing, art, or code." action={{ label: 'Add a piece', onClick: () => open('portfolio') }} />
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {portfolio.map(item => (
              <Card pad={false} key={item.id} className="p-4 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5 min-w-0">
                  <FolderOpen size={16} className="text-muted-foreground mt-0.5" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">{item.title}</p>
                    <p className="text-xs text-muted-foreground">{PORTFOLIO_ITEM_TYPES.find(t => t.value === item.item_type)?.label || item.item_type}</p>
                    {safeUrl(item.url) && <a href={safeUrl(item.url)!} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline mt-0.5"><ExternalLink size={11} /> View</a>}
                  </div>
                </div>
                <RowActions onEdit={() => open('portfolio', item)} onDelete={() => confirmDelete('portfolio piece', () => pfDelete.mutate(item.id))} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Online Presence */}
      <section>
        <SectionHeader title="Online presence" description="LinkedIn, GitHub, personal site, and more." action={<Button size="sm" onClick={() => open('online')}><Plus size={14} /> Add link</Button>} />
        {online.length === 0 ? (
          <EmptyState title="No links yet" description="Add your LinkedIn, GitHub, or portfolio site to strengthen your entries." action={{ label: 'Add a link', onClick: () => open('online') }} />
        ) : (
          <div className="space-y-2">
            {online.map(op => (
              <Card pad={false} key={op.id} className="p-4 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5 min-w-0">
                  <ExternalLink size={16} className="text-muted-foreground mt-0.5" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">{PLATFORM_TYPES.find(t => t.value === op.platform_type)?.label || op.platform_type}</p>
                    {safeUrl(op.url) ? (
                      <a href={safeUrl(op.url)!} target="_blank" rel="noopener noreferrer" className="text-sm text-secondary hover:underline truncate block max-w-xs">{op.display_name || op.url}</a>
                    ) : (
                      <span className="text-sm text-muted-foreground truncate block max-w-xs">{op.display_name || op.url}</span>
                    )}
                  </div>
                </div>
                <RowActions onEdit={() => open('online', op)} onDelete={() => confirmDelete('link', () => opDelete.mutate(op.id))} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Modals */}
      <Modal isOpen={modal === 'activity'} onClose={close} title={editItem ? 'Edit activity' : 'Add activity'}>
        <ActivityForm defaultValues={editItem} loading={actCreate.isPending || actUpdate.isPending} onSubmit={(d: any) => (editItem ? actUpdate.mutate({ id: editItem.id, data: d }) : actCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'work'} onClose={close} title={editItem ? 'Edit work experience' : 'Add work experience'} size="lg">
        <WorkExperienceForm defaultValues={editItem} loading={weCreate.isPending || weUpdate.isPending} onSubmit={(d: any) => (editItem ? weUpdate.mutate({ id: editItem.id, data: d }) : weCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'competition'} onClose={close} title={editItem ? 'Edit competition' : 'Add competition'} size="lg">
        <CompetitionForm defaultValues={editItem} loading={compCreate.isPending || compUpdate.isPending} onSubmit={(d: any) => (editItem ? compUpdate.mutate({ id: editItem.id, data: d }) : compCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'portfolio'} onClose={close} title={editItem ? 'Edit portfolio piece' : 'Add portfolio piece'}>
        <PortfolioItemForm defaultValues={editItem} loading={pfCreate.isPending || pfUpdate.isPending} onSubmit={(d: any) => (editItem ? pfUpdate.mutate({ id: editItem.id, data: d }) : pfCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={modal === 'online'} onClose={close} title={editItem ? 'Edit link' : 'Add link'}>
        <OnlinePresenceForm defaultValues={editItem} loading={opCreate.isPending || opUpdate.isPending} onSubmit={(d: any) => (editItem ? opUpdate.mutate({ id: editItem.id, data: d }) : opCreate.mutate(d))} />
      </Modal>
    </div>
  )
}
