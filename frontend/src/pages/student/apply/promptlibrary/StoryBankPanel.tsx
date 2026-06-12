// Spec 42 §3.20 — story bank panel: the reusable narrative units a student maps
// to prompts and essays.
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Plus } from 'lucide-react'

import { deleteStory } from '../../../../api/prompt-library'
import Button from '../../../../components/ui/Button'
import Card from '../../../../components/ui/Card'
import { confirmDialog } from '../../../../stores/confirm-store'
import { showToast } from '../../../../stores/toast-store'
import type { Story } from '../../../../types/promptLibrary'

import StoryCard from './StoryCard'
import StoryEditor from './StoryEditor'

export default function StoryBankPanel({ stories }: { stories: Story[] }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<Story | null>(null)
  const [open, setOpen] = useState(false)

  const del = useMutation({
    mutationFn: (s: Story) => deleteStory(s.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prompt-library'] })
      showToast('Story removed.', 'success')
    },
    onError: (e: unknown) => showToast((e as Error).message ?? 'Could not delete.', 'error'),
  })

  const openNew = () => {
    setEditing(null)
    setOpen(true)
  }
  const openEdit = (s: Story) => {
    setEditing(s)
    setOpen(true)
  }
  const confirmDelete = async (s: Story) => {
    const ok = await confirmDialog({
      title: 'Remove this story?',
      body: `Delete “${s.title}” from your story bank? Any prompts drawing from it will lose the link. This can't be undone.`,
      confirmLabel: 'Remove story',
      destructive: true,
    })
    if (ok) del.mutate(s)
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="flex items-center gap-1.5 text-h3 text-foreground">
            <BookOpen size={18} /> Story bank
          </h3>
          <p className="text-sm text-muted-foreground">
            Reusable stories you can draw from across prompts and essays.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={openNew}>
          <Plus size={15} /> Add story
        </Button>
      </div>

      {stories.length === 0 ? (
        <Card pad={false} variant="card-flush" className="px-4 py-10 text-center">
          <p className="text-sm text-muted-foreground">
            No stories yet. Capture a few defining experiences once — then map them to any prompt.
          </p>
          <div className="mt-3">
            <Button variant="secondary" size="sm" onClick={openNew}>
              <Plus size={15} /> Add your first story
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {stories.map(s => (
            <StoryCard key={s.id} story={s} onEdit={openEdit} onDelete={confirmDelete} />
          ))}
        </div>
      )}

      <StoryEditor story={editing} isOpen={open} onClose={() => setOpen(false)} />
    </section>
  )
}
