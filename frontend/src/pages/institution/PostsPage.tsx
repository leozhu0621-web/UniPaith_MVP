import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText, Plus, Pin, PinOff, Send, Edit2, Trash2, Eye, Clock,
  Image, Tag, Copy,
} from 'lucide-react'
import {
  getPosts, createPost, updatePost, deletePost, publishPost, pinPost,
  requestPostMediaUpload, getPostTemplates, getInstitutionPrograms,
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
import { formatDateTime } from '../../utils/format'
import type { InstitutionPost, Program } from '../../types'

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  published: 'success',
  scheduled: 'info',
  archived: 'warning',
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

  const postsQ = useQuery({ queryKey: ['posts'], queryFn: getPosts })
  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const templatesQ = useQuery({ queryKey: ['post-templates'], queryFn: getPostTemplates, enabled: showTemplatesModal })

  const posts: InstitutionPost[] = Array.isArray(postsQ.data) ? postsQ.data : []
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const filtered = activeTab === 'all'
    ? posts
    : posts.filter(p => p.status === activeTab)

  const resetForm = () => {
    setTitle(''); setBody(''); setMediaUrls([]); setTaggedProgramIds([])
    setTaggedIntake(''); setPostStatus('draft'); setScheduledFor('')
    setIsTemplate(false); setTemplateName('')
  }

  const openCreate = () => { resetForm(); setEditTarget(null); setShowCreateModal(true) }
  const openEdit = (p: InstitutionPost) => {
    setTitle(p.title); setBody(p.body)
    setMediaUrls(Array.isArray(p.media_urls) ? p.media_urls : [])
    setTaggedProgramIds(Array.isArray(p.tagged_program_ids) ? p.tagged_program_ids : [])
    setTaggedIntake(p.tagged_intake ?? '')
    setPostStatus(p.status === 'archived' ? 'draft' : p.status as 'draft' | 'published' | 'scheduled')
    setScheduledFor(p.scheduled_for ? p.scheduled_for.slice(0, 16) : '')
    setIsTemplate(p.is_template); setTemplateName(p.template_name ?? '')
    setEditTarget(p); setShowCreateModal(true)
  }
  const fillFromTemplate = (t: InstitutionPost) => {
    setTitle(t.title); setBody(t.body)
    setMediaUrls(Array.isArray(t.media_urls) ? t.media_urls : [])
    setTaggedProgramIds(Array.isArray(t.tagged_program_ids) ? t.tagged_program_ids : [])
    setTaggedIntake(t.tagged_intake ?? '')
    setPostStatus('draft'); setScheduledFor('')
    setIsTemplate(false); setTemplateName('')
    setShowTemplatesModal(false); setEditTarget(null); setShowCreateModal(true)
  }

  const createM = useMutation({
    mutationFn: (data: Parameters<typeof createPost>[0]) => createPost(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post-templates'] })
      setShowCreateModal(false); showToast('Post created', 'success')
    },
  })
  const updateM = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updatePost>[1] }) => updatePost(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post-templates'] })
      setShowCreateModal(false); showToast('Post updated', 'success')
    },
  })
  const deleteM = useMutation({
    mutationFn: (id: string) => deletePost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      setDeleteTarget(null); showToast('Post deleted', 'success')
    },
  })
  const publishM = useMutation({
    mutationFn: (id: string) => publishPost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      showToast('Post published', 'success')
    },
  })
  const pinM = useMutation({
    mutationFn: (id: string) => pinPost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const handleMediaUpload = async (file: File) => {
    setUploading(true)
    try {
      const { upload_url, media_key } = await requestPostMediaUpload(file.type)
      await fetch(upload_url, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })
      const fileUrl = media_key
      setMediaUrls(prev => [...prev, { url: fileUrl, type: file.type.startsWith('image/') ? 'image' : 'file' }])
      showToast('Media uploaded', 'success')
    } catch {
      showToast('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = () => {
    const payload = {
      title, body,
      media_urls: mediaUrls.length > 0 ? mediaUrls : undefined,
      tagged_program_ids: taggedProgramIds.length > 0 ? taggedProgramIds : undefined,
      tagged_intake: taggedIntake || undefined,
      status: postStatus,
      scheduled_for: postStatus === 'scheduled' && scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
      is_template: isTemplate,
      template_name: isTemplate ? templateName || undefined : undefined,
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
            <Button size="sm" onClick={openCreate}>
              <Plus size={16} className="mr-1" /> New Post
            </Button>
          </div>
        }
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {postsQ.isLoading ? (
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
                      <Pin size={14} className="text-amber-500 flex-shrink-0" />
                    )}
                    <h3 className="text-sm font-semibold text-gray-900 truncate">{post.title}</h3>
                    <Badge variant={STATUS_BADGE[post.status] ?? 'neutral'}>{post.status}</Badge>
                    {post.is_template && <Badge variant="info">Template</Badge>}
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2 mb-2">{post.body}</p>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    {post.published_at && (
                      <span>Published {formatDateTime(post.published_at)}</span>
                    )}
                    {post.status === 'scheduled' && post.scheduled_for && (
                      <span className="flex items-center gap-1">
                        <Clock size={12} /> Scheduled {formatDateTime(post.scheduled_for)}
                      </span>
                    )}
                    {post.view_count > 0 && (
                      <span className="flex items-center gap-1">
                        <Eye size={12} /> {post.view_count}
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
                    className="p-1.5 rounded hover:bg-gray-100"
                    title={post.pinned ? 'Unpin' : 'Pin'}
                  >
                    {post.pinned ? <PinOff size={16} className="text-amber-500" /> : <Pin size={16} className="text-gray-400" />}
                  </button>
                  {post.status !== 'published' && (
                    <button
                      onClick={() => publishM.mutate(post.id)}
                      className="p-1.5 rounded hover:bg-gray-100"
                      title="Publish"
                    >
                      <Send size={16} className="text-green-600" />
                    </button>
                  )}
                  <button onClick={() => openEdit(post)} className="p-1.5 rounded hover:bg-gray-100" title="Edit">
                    <Edit2 size={16} className="text-gray-500" />
                  </button>
                  <button onClick={() => setDeleteTarget(post)} className="p-1.5 rounded hover:bg-gray-100" title="Delete">
                    <Trash2 size={16} className="text-red-400" />
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Media</label>
            <div className="flex items-center gap-2 flex-wrap">
              {mediaUrls.map((m, i) => (
                <div key={i} className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs">
                  <Image size={12} /> {m.type === 'image' ? 'Image' : 'File'} {i + 1}
                  <button onClick={() => setMediaUrls(prev => prev.filter((_, j) => j !== i))} className="text-red-400 ml-1">&times;</button>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Tag Programs</label>
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

          <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
            <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button
              onClick={handleSubmit}
              disabled={!title.trim() || !body.trim() || createM.isPending || updateM.isPending}
            >
              {createM.isPending || updateM.isPending ? 'Saving...' : editTarget ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Post">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete &ldquo;{deleteTarget?.title}&rdquo;? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
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
          <p className="text-sm text-gray-500 py-4 text-center">No templates saved yet. Create a post and check &ldquo;Save as template&rdquo;.</p>
        ) : (
          <div className="space-y-3">
            {templatesQ.data.map(t => (
              <Card key={t.id} className="p-3 cursor-pointer hover:bg-gray-50" onClick={() => fillFromTemplate(t)}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{t.template_name || t.title}</h4>
                    <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">{t.body}</p>
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
