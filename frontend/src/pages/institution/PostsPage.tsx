import { useState, useRef } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText, Plus, Pin, PinOff, Send, Edit2, Trash2, Eye, Clock,
  Image, Tag, Copy, MousePointerClick, Bookmark, Mail, Megaphone, Archive,
} from 'lucide-react'
import {
  getPosts, createPost, updatePost, deletePost, publishPost, pinPost,
  requestPostMediaUpload, getPostTemplates, getInstitutionPrograms,
} from '../../api/institutions'
import { putFileToPresignedUrl } from '../../api/uploads'
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
import { formatDateTime } from '../../utils/format'
import type { InstitutionPost, PostCTA, Program } from '../../types'

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  published: 'success',
  scheduled: 'info',
  archived: 'warning',
}

// Spec 27 §2.4 — CTA types attachable to a post.
const CTA_TYPE_OPTIONS = [
  { value: 'view_program', label: 'View program' },
  { value: 'rsvp', label: 'RSVP to event' },
  { value: 'request_info', label: 'Request info' },
  { value: 'start_application', label: 'Start application' },
  { value: 'add_to_calendar', label: 'Add to calendar' },
]
const CTA_DEFAULT_LABEL: Record<string, string> = {
  view_program: 'View program',
  rsvp: 'RSVP',
  request_info: 'Request info',
  start_application: 'Start application',
  add_to_calendar: 'Add to calendar',
}

export default function PostsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showTemplatesModal, setShowTemplatesModal] = useState(false)
  const [editTarget, setEditTarget] = useState<InstitutionPost | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<InstitutionPost | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Form state
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [mediaUrls, setMediaUrls] = useState<{ url: string; type: string; caption?: string }[]>([])
  const [taggedProgramIds, setTaggedProgramIds] = useState<string[]>([])
  const [taggedIntake, setTaggedIntake] = useState('')
  const [postStatus, setPostStatus] = useState<'draft' | 'published' | 'scheduled'>('draft')
  const [scheduledFor, setScheduledFor] = useState('')
  const [isTemplate, setIsTemplate] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [uploading, setUploading] = useState(false)
  // Spec 27 §2.4 / §2.3 — CTAs + visibility scope.
  const [ctas, setCtas] = useState<PostCTA[]>([])
  const [visPublic, setVisPublic] = useState(true)
  const [visRegions, setVisRegions] = useState('')

  const postsQ = useQuery({ queryKey: ['posts'], queryFn: getPosts })
  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const templatesQ = useQuery({ queryKey: ['post-templates'], queryFn: getPostTemplates, enabled: showTemplatesModal })

  const posts: InstitutionPost[] = postsQ.data ?? []
  const programs: Program[] = programsQ.data ?? []

  const filtered = activeTab === 'all'
    ? posts
    : posts.filter(p => p.status === activeTab)

  const resetForm = () => {
    setTitle(''); setBody(''); setMediaUrls([]); setTaggedProgramIds([])
    setTaggedIntake(''); setPostStatus('draft'); setScheduledFor('')
    setIsTemplate(false); setTemplateName('')
    setCtas([]); setVisPublic(true); setVisRegions('')
  }

  const addCta = () =>
    setCtas(prev => [...prev, { type: 'view_program', label: CTA_DEFAULT_LABEL.view_program, target: '' }])
  const updateCta = (i: number, patch: Partial<PostCTA>) =>
    setCtas(prev => prev.map((c, j) => (j === i ? { ...c, ...patch } : c)))
  const removeCta = (i: number) => setCtas(prev => prev.filter((_, j) => j !== i))

  const openCreate = () => { resetForm(); setEditTarget(null); setShowCreateModal(true) }
  const openEdit = (p: InstitutionPost) => {
    setTitle(p.title); setBody(p.body)
    setMediaUrls(Array.isArray(p.media_urls) ? p.media_urls : [])
    setTaggedProgramIds(Array.isArray(p.tagged_program_ids) ? p.tagged_program_ids : [])
    setTaggedIntake(p.tagged_intake ?? '')
    setPostStatus(p.status === 'archived' ? 'draft' : p.status as 'draft' | 'published' | 'scheduled')
    setScheduledFor(p.scheduled_for ? p.scheduled_for.slice(0, 16) : '')
    setIsTemplate(p.is_template); setTemplateName(p.template_name ?? '')
    setCtas(Array.isArray(p.ctas) ? p.ctas : [])
    setVisPublic(p.visibility?.public ?? true)
    setVisRegions((p.visibility?.region_scopes ?? []).join(', '))
    setEditTarget(p); setShowCreateModal(true)
  }
  const fillFromTemplate = (t: InstitutionPost) => {
    setTitle(t.title); setBody(t.body)
    setMediaUrls(Array.isArray(t.media_urls) ? t.media_urls : [])
    setTaggedProgramIds(Array.isArray(t.tagged_program_ids) ? t.tagged_program_ids : [])
    setTaggedIntake(t.tagged_intake ?? '')
    setPostStatus('draft'); setScheduledFor('')
    setIsTemplate(false); setTemplateName('')
    setCtas(Array.isArray(t.ctas) ? t.ctas : [])
    setVisPublic(true); setVisRegions('')
    setShowTemplatesModal(false); setEditTarget(null); setShowCreateModal(true)
  }

  const createM = useMutation({
    mutationFn: (data: Parameters<typeof createPost>[0]) => createPost(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post-templates'] })
      setShowCreateModal(false); showToast('Post created', 'success')
    },
    onError: () => showToast("We couldn't create the post. Please try again.", 'error'),
  })
  const updateM = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updatePost>[1] }) => updatePost(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post-templates'] })
      setShowCreateModal(false); showToast('Post updated', 'success')
    },
    onError: () => showToast("We couldn't update the post. Please try again.", 'error'),
  })
  const deleteM = useMutation({
    mutationFn: (id: string) => deletePost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      setDeleteTarget(null); showToast('Post deleted', 'success')
    },
    onError: () => showToast("We couldn't delete the post. Please try again.", 'error'),
  })
  const publishM = useMutation({
    mutationFn: (id: string) => publishPost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      showToast('Post published', 'success')
    },
    onError: () => showToast("We couldn't publish the post. Please try again.", 'error'),
  })
  const pinM = useMutation({
    mutationFn: (id: string) => pinPost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
    onError: () => showToast("We couldn't update the post. Please try again.", 'error'),
  })
  const archiveM = useMutation({
    mutationFn: (id: string) => updatePost(id, { status: 'archived' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      showToast('Post archived', 'success')
    },
    onError: () => showToast("We couldn't archive the post. Please try again.", 'error'),
  })

  const handleMediaUpload = async (file: File) => {
    setUploading(true)
    try {
      const { upload_url, media_key } = await requestPostMediaUpload(file.type)
      await putFileToPresignedUrl(upload_url, file)
      const fileUrl = media_key
      setMediaUrls(prev => [...prev, { url: fileUrl, type: file.type.startsWith('image/') ? 'image' : 'file' }])
      showToast('Media uploaded', 'success')
    } catch {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = (statusOverride?: 'draft' | 'published' | 'scheduled') => {
    const status = statusOverride ?? postStatus
    if (status === 'scheduled' && !scheduledFor) {
      showToast('Pick a schedule date and time', 'error')
      return
    }
    const payload = {
      title, body,
      media_urls: mediaUrls.length > 0 ? mediaUrls : undefined,
      tagged_program_ids: taggedProgramIds.length > 0 ? taggedProgramIds : undefined,
      tagged_intake: taggedIntake || undefined,
      status,
      scheduled_for: status === 'scheduled' && scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
      is_template: isTemplate,
      template_name: isTemplate ? templateName || undefined : undefined,
      ctas: ctas.filter(c => c.label.trim()).length > 0 ? ctas.filter(c => c.label.trim()) : undefined,
      visibility: {
        public: visPublic,
        segment_ids: [],
        region_scopes: visRegions.split(',').map(s => s.trim()).filter(Boolean),
      },
    }
    if (editTarget) {
      updateM.mutate({ id: editTarget.id, data: payload })
    } else {
      createM.mutate(payload)
    }
  }

  const tabs = [
    { id: 'all', label: `All (${posts.length})` },
    { id: 'published', label: `Published (${posts.filter(p => p.status === 'published').length})` },
    { id: 'draft', label: `Drafts (${posts.filter(p => p.status === 'draft').length})` },
    { id: 'scheduled', label: `Scheduled (${posts.filter(p => p.status === 'scheduled').length})` },
    { id: 'archived', label: `Archived (${posts.filter(p => p.status === 'archived').length})` },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <InstitutionPageHeader
        title="Posts & Updates"
        description="Publish announcements, updates, and content to your public profile."
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setShowTemplatesModal(true)}>
              <Copy size={16} className="mr-1" /> Templates
            </Button>
            <Button variant="secondary" size="sm" onClick={openCreate}>
              <Plus size={16} className="mr-1" /> New Post
            </Button>
          </div>
        }
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {postsQ.isError ? (
        <QueryError detail="Couldn’t load posts." onRetry={() => postsQ.refetch()} />
      ) : postsQ.isLoading ? (
        <div className="space-y-4">{[1, 2, 3].map(i => <Skeleton key={i} className="h-32" />)}</div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<FileText size={40} />}
          title={activeTab === 'all' ? 'No posts yet' : `No ${activeTab} posts`}
          description="Create your first post to share updates with prospective students."
          action={activeTab === 'all' ? { label: 'New Post', onClick: openCreate } : undefined}
        />
      ) : (
        <div className="space-y-4">
          {filtered.map(post => (
            <Card key={post.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {post.pinned && (
                      <Pin size={14} className="text-secondary flex-shrink-0" />
                    )}
                    <h3 className="text-sm font-semibold text-foreground truncate">{post.title}</h3>
                    <Badge variant={STATUS_BADGE[post.status] ?? 'neutral'}>{post.status}</Badge>
                    {post.is_template && <Badge variant="info">Template</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-2">{post.body}</p>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    {post.published_at && (
                      <span>Published {formatDateTime(post.published_at)}</span>
                    )}
                    {post.status === 'scheduled' && post.scheduled_for && (
                      <span className="flex items-center gap-1">
                        <Clock size={12} /> Scheduled {formatDateTime(post.scheduled_for)}
                      </span>
                    )}
                    {post.view_count > 0 && (
                      <span className="flex items-center gap-1" title="Views">
                        <Eye size={12} /> {post.view_count}
                      </span>
                    )}
                    {(post.click_count ?? 0) > 0 && (
                      <span className="flex items-center gap-1" title="CTA clicks">
                        <MousePointerClick size={12} /> {post.click_count}
                      </span>
                    )}
                    {(post.save_count ?? 0) > 0 && (
                      <span className="flex items-center gap-1" title="Saves">
                        <Bookmark size={12} /> {post.save_count}
                      </span>
                    )}
                    {(post.request_info_count ?? 0) > 0 && (
                      <span className="flex items-center gap-1" title="Info requests">
                        <Mail size={12} /> {post.request_info_count}
                      </span>
                    )}
                    {(post.apply_started_count ?? 0) > 0 && (
                      <span className="flex items-center gap-1" title="Applications started">
                        <Send size={12} /> {post.apply_started_count}
                      </span>
                    )}
                    {post.ctas && post.ctas.length > 0 && (
                      <span className="flex items-center gap-1" title="Call-to-action buttons">
                        <Megaphone size={12} /> {post.ctas.length} CTA{post.ctas.length > 1 ? 's' : ''}
                      </span>
                    )}
                    {post.program_names && post.program_names.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Tag size={12} /> {post.program_names.join(', ')}
                      </span>
                    )}
                    {post.tagged_intake && (
                      <Badge variant="neutral">{post.tagged_intake}</Badge>
                    )}
                    {post.media_urls && Array.isArray(post.media_urls) && post.media_urls.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Image size={12} /> {post.media_urls.length} media
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => pinM.mutate(post.id)}
                    className="p-1.5 rounded hover:bg-muted"
                    title={post.pinned ? 'Unpin' : 'Pin'}
                  >
                    {post.pinned ? <PinOff size={16} className="text-secondary" /> : <Pin size={16} className="text-muted-foreground/70" />}
                  </button>
                  {post.status === 'published' && (
                    <button
                      onClick={() => archiveM.mutate(post.id)}
                      className="p-1.5 rounded hover:bg-muted"
                      title="Archive"
                    >
                      <Archive size={16} className="text-muted-foreground" />
                    </button>
                  )}
                  {post.status !== 'published' && (
                    <button
                      onClick={() => publishM.mutate(post.id)}
                      className="p-1.5 rounded hover:bg-muted"
                      title="Publish"
                    >
                      <Send size={16} className="text-success" />
                    </button>
                  )}
                  <button onClick={() => openEdit(post)} className="p-1.5 rounded hover:bg-muted" title="Edit">
                    <Edit2 size={16} className="text-muted-foreground" />
                  </button>
                  <button onClick={() => setDeleteTarget(post)} className="p-1.5 rounded hover:bg-muted" title="Delete">
                    <Trash2 size={16} className="text-destructive/70" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={editTarget ? 'Edit Post' : 'New Post'}
        size="lg"
      >
        <div className="space-y-4">
          <Input label="Title" value={title} onChange={e => setTitle(e.target.value)} placeholder="Post title" />
          <Textarea label="Body" value={body} onChange={e => setBody(e.target.value)} placeholder="Write your post content (supports markdown)..." rows={8} />

          {/* Media Upload */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Media</label>
            <div className="flex items-center gap-2 flex-wrap">
              {mediaUrls.map((m, i) => (
                <div key={i} className="flex items-center gap-1 px-2 py-1 bg-muted rounded text-xs">
                  <Image size={12} /> {m.type === 'image' ? 'Image' : 'File'} {i + 1}
                  <button onClick={() => setMediaUrls(prev => prev.filter((_, j) => j !== i))} className="text-destructive/70 ml-1">&times;</button>
                </div>
              ))}
              <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                <Image size={14} className="mr-1" /> {uploading ? 'Uploading...' : 'Add Media'}
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={e => { if (e.target.files?.[0]) handleMediaUpload(e.target.files[0]); e.target.value = '' }}
              />
            </div>
          </div>

          {/* Program Tags */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Tag Programs</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {taggedProgramIds.map(pid => {
                const prog = programs.find(p => p.id === pid)
                return (
                  <Badge key={pid} variant="info">
                    {prog?.program_name ?? pid}
                    <button onClick={() => setTaggedProgramIds(prev => prev.filter(id => id !== pid))} className="ml-1">&times;</button>
                  </Badge>
                )
              })}
            </div>
            {programs.length > 0 && (
              <Select
                value=""
                onChange={e => {
                  if (e.target.value && !taggedProgramIds.includes(e.target.value)) {
                    setTaggedProgramIds(prev => [...prev, e.target.value])
                  }
                }}
                options={[
                  { value: '', label: 'Select a program to tag...' },
                  ...programs.filter(p => !taggedProgramIds.includes(p.id)).map(p => ({ value: p.id, label: p.program_name })),
                ]}
              />
            )}
          </div>

          <Input label="Intake Tag" value={taggedIntake} onChange={e => setTaggedIntake(e.target.value)} placeholder="e.g. Fall 2026" />

          {/* Status / Schedule */}
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Status"
              value={postStatus}
              onChange={e => setPostStatus(e.target.value as 'draft' | 'published' | 'scheduled')}
              options={[
                { value: 'draft', label: 'Draft' },
                { value: 'published', label: 'Published' },
                { value: 'scheduled', label: 'Scheduled' },
              ]}
            />
            {postStatus === 'scheduled' && (
              <Input
                label="Schedule For"
                type="datetime-local"
                value={scheduledFor}
                onChange={e => setScheduledFor(e.target.value)}
              />
            )}
          </div>

          {/* CTAs (Spec 27 §2.4) */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Call-to-action buttons</label>
            <p className="text-xs text-muted-foreground mb-2">Buttons students see on this post in their feed.</p>
            <div className="space-y-2">
              {ctas.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Select
                    className="w-40"
                    value={c.type}
                    onChange={e => {
                      const type = e.target.value as PostCTA['type']
                      updateCta(i, { type, label: c.label || CTA_DEFAULT_LABEL[type] })
                    }}
                    options={CTA_TYPE_OPTIONS}
                  />
                  <Input
                    className="flex-1"
                    value={c.label}
                    onChange={e => updateCta(i, { label: e.target.value })}
                    placeholder="Button label"
                  />
                  <Input
                    className="flex-1"
                    value={c.target ?? ''}
                    onChange={e => updateCta(i, { target: e.target.value })}
                    placeholder="Target (program/event/URL — optional)"
                  />
                  <button onClick={() => removeCta(i)} className="text-destructive/70 p-1 text-lg leading-none" title="Remove CTA">&times;</button>
                </div>
              ))}
              <Button variant="secondary" size="sm" onClick={addCta}>
                <Plus size={14} className="mr-1" /> Add CTA
              </Button>
            </div>
          </div>

          {/* Visibility (Spec 27 §2.3) */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Visibility</label>
            <label className="flex items-center gap-2 text-sm mb-2">
              <input type="checkbox" checked={visPublic} onChange={e => setVisPublic(e.target.checked)} className="rounded" />
              Public on institution &amp; program pages
            </label>
            <Input
              label="Limit to regions (optional)"
              value={visRegions}
              onChange={e => setVisRegions(e.target.value)}
              placeholder="e.g. North America, Europe (comma-separated)"
            />
          </div>

          {/* Template */}
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={isTemplate} onChange={e => setIsTemplate(e.target.checked)} className="rounded" />
              Save as template
            </label>
            {isTemplate && (
              <Input
                className="flex-1"
                value={templateName}
                onChange={e => setTemplateName(e.target.value)}
                placeholder="Template name"
              />
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button variant="tertiary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button
              variant="secondary"
              onClick={() => handleSubmit('draft')}
              disabled={!title.trim() || !body.trim() || createM.isPending || updateM.isPending}
            >
              {createM.isPending || updateM.isPending ? 'Saving...' : 'Save draft'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => handleSubmit('scheduled')}
              disabled={!title.trim() || !body.trim() || !scheduledFor || createM.isPending || updateM.isPending}
            >
              Schedule post
            </Button>
            <Button
              variant="secondary"
              onClick={() => handleSubmit('published')}
              disabled={!title.trim() || !body.trim() || createM.isPending || updateM.isPending}
            >
              Publish post
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Post">
        <p className="text-sm text-muted-foreground mb-4">
          Are you sure you want to delete &ldquo;{deleteTarget?.title}&rdquo;? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteM.mutate(deleteTarget.id)} disabled={deleteM.isPending}>
            {deleteM.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>

      {/* Templates Modal */}
      <Modal isOpen={showTemplatesModal} onClose={() => setShowTemplatesModal(false)} title="Post Templates" size="lg">
        {templatesQ.isLoading ? (
          <div className="space-y-3">{[1, 2].map(i => <Skeleton key={i} className="h-20" />)}</div>
        ) : !templatesQ.data?.length ? (
          <p className="text-sm text-muted-foreground py-4 text-center">No templates saved yet. Create a post and check &ldquo;Save as template&rdquo;.</p>
        ) : (
          <div className="space-y-3">
            {templatesQ.data.map(t => (
              <Card key={t.id} className="p-3 cursor-pointer hover:bg-muted" onClick={() => fillFromTemplate(t)}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-foreground">{t.template_name || t.title}</h4>
                    <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{t.body}</p>
                  </div>
                  <Button variant="secondary" size="sm">Use</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
