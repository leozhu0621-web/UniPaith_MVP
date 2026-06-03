import { useEffect, useState } from 'react'
import { useAuthStore } from '../../stores/auth-store'
import Modal from '../ui/Modal'
import Button from '../ui/Button'

const SEEN_KEY = 'unipaith.demo-notice-seen'

// One-time-per-session demo notice, shown right after sign-in. Explains that
// this is a live demo whose data resets on each sign-in. Dismissal is stored in
// sessionStorage so it shows once per browser session.
export default function DemoNotice() {
  const user = useAuthStore(s => s.user)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (user && sessionStorage.getItem(SEEN_KEY) !== '1') {
      setOpen(true)
    }
  }, [user])

  const dismiss = () => {
    sessionStorage.setItem(SEEN_KEY, '1')
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
        <p>You're exploring a live demo of UniPaith — feel free to try everything.</p>
        <p>
          Your data resets every time you sign in, so each session starts fresh. Nothing you enter
          here is kept.
        </p>
        <p>Spot something to improve? Use the Feedback button to tell us — we read every note.</p>
      </div>
    </Modal>
  )
}
