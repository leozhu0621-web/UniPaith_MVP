import { useConfirmStore } from '../../stores/confirm-store'
import Modal from './Modal'
import Button from './Button'

// ConfirmHost — renders the active confirm dialog (Spec 78 §6). Mount once at
// the app root, beside ToastContainer. Open it from anywhere via
// `confirmDialog({...})` (confirm-store). Replaces native window.confirm.
export default function ConfirmHost() {
  const current = useConfirmStore((s) => s.current)
  const settle = useConfirmStore((s) => s.settle)

  if (!current) return null

  return (
    <Modal
      isOpen
      onClose={() => settle(false)}
      title={current.title}
      size="sm"
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" onClick={() => settle(false)}>
            {current.cancelLabel ?? 'Cancel'}
          </Button>
          <Button
            variant={current.destructive ? 'destructive' : 'secondary'}
            onClick={() => settle(true)}
          >
            {current.confirmLabel ?? 'Confirm'}
          </Button>
        </div>
      }
    >
      {current.body && <p className="text-sm text-muted-foreground">{current.body}</p>}
    </Modal>
  )
}
