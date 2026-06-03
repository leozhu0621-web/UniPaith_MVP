import { useState } from 'react'
import { MessageSquarePlus } from 'lucide-react'
import { useAuthStore } from '../../stores/auth-store'
import { showToast } from '../../stores/toast-store'
import { submitFeedback } from '../../api/feedback'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import Input from '../ui/Input'
import Textarea from '../ui/Textarea'

// Floating feedback widget (demo feedback survey). A small button opens a
// title + message form; submissions are collected server-side. Authenticated
// users only.
export default function FeedbackWidget() {
  const user = useAuthStore(s => s.user)
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!user) return null

  const submit = async () => {
    if (!message.trim()) return
    setSubmitting(true)
    try {
      await submitFeedback({
        title: title.trim() || undefined,
        message: message.trim(),
        context: { path: window.location.pathname },
      })
      showToast('Thanks — your feedback was sent.', 'success')
      setTitle('')
      setMessage('')
      setOpen(false)
    } catch {
      showToast("Couldn't send your feedback. Try again.", 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 inline-flex items-center gap-2 rounded-full bg-secondary px-4 py-2.5 text-sm font-medium text-secondary-foreground elev-raised hover:brightness-95 transition-all"
        aria-label="Send feedback"
      >
        <MessageSquarePlus size={16} /> Feedback
      </button>

      <Modal
        isOpen={open}
        onClose={() => setOpen(false)}
        title="Send feedback"
        size="sm"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="secondary" loading={submitting} disabled={!message.trim()} onClick={submit}>
              Send
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Tell us what's working or what's not — we read every note.
          </p>
          <Input
            label="Title (optional)"
            value={title}
            onChange={e => setTitle(e.target.value)}
            maxLength={255}
          />
          <Textarea
            label="Your feedback"
            value={message}
            onChange={e => setMessage(e.target.value)}
            rows={4}
            showCount
            maxLength={2000}
          />
        </div>
      </Modal>
    </>
  )
}
