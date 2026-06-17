import { useEffect, useState } from 'react'
import { useAuthStore } from '../../stores/auth-store'
import Modal from '../ui/Modal'
import Button from '../ui/Button'

const SEEN_KEY = 'unipaith.demo-notice-seen'

// Once-per-BROWSER demo notice, shown right after the first sign-in (UX
// overhaul Ship C: was once-per-session, which re-interrupted every sign-in).
// Dismissal persists in localStorage; the legacy sessionStorage flag is read
// for back-compat and migrated forward so mid-session users aren't re-shown.
function hasSeenNotice(): boolean {
  try {
    if (localStorage.getItem(SEEN_KEY) === '1') return true
    if (sessionStorage.getItem(SEEN_KEY) === '1') {
      localStorage.setItem(SEEN_KEY, '1') // migrate the old key forward
      return true
    }
  } catch {
    /* private mode / quota — fall through and show once */
  }
  return false
}

export default function DemoNotice() {
  const user = useAuthStore(s => s.user)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (user && !hasSeenNotice()) {
      setOpen(true)
    }
  }, [user])

  const dismiss = () => {
    try {
      localStorage.setItem(SEEN_KEY, '1')
    } catch {
      /* ignore */
    }
    setOpen(false)
  }

  if (!user || !open) return null

  return (
    <Modal
      isOpen
      onClose={dismiss}
      title="Welcome — this is a live demo"
      size="sm"
      footer={
        <div className="flex justify-end">
          <Button variant="secondary" onClick={dismiss}>
            Got it
          </Button>
        </div>
      }
    >
      <div className="space-y-2 text-sm text-muted-foreground">
        <p>This is a live demo — try everything. Your data resets each time you sign in.</p>
        <p>Spot something to improve? Use the Feedback button — we read every note.</p>
      </div>
    </Modal>
  )
}
