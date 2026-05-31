import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertTriangle, LogOut, Trash2, RotateCcw } from 'lucide-react'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Modal from '../../../components/ui/Modal'
import SettingsSection from './SettingsSection'
import { deleteAccount, cancelDeletion } from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import { useAuthStore } from '../../../stores/auth-store'
import { formatDate } from '../../../utils/format'
import type { DeletionInfo } from '../../../types'

interface DangerZoneProps {
  deletion: DeletionInfo | null
  onChanged: () => void
}

export default function DangerZone({ deletion, onChanged }: DangerZoneProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const logout = useAuthStore(s => s.logout)

  const cancelMut = useMutation({
    mutationFn: cancelDeletion,
    onSuccess: () => {
      showToast('Account deletion canceled', 'success')
      onChanged()
    },
    onError: () => showToast('Could not cancel deletion', 'error'),
  })

  return (
    <SettingsSection
      icon={AlertTriangle}
      title="Danger zone"
      description="Sign out, or permanently delete your account."
      tone="danger"
    >
      {deletion ? (
        <div className="flex flex-col gap-3 rounded-lg border border-error/40 bg-error-soft/40 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-2.5">
            <Trash2 size={18} className="text-error mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-foreground">
                Scheduled for deletion on {formatDate(deletion.purge_at)}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Your account and data will be permanently removed then. You can undo until that date.
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => cancelMut.mutate()}
            loading={cancelMut.isPending}
          >
            <RotateCcw size={14} /> Undo
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="tertiary" onClick={logout}>
            <LogOut size={14} /> Sign out
          </Button>
          <Button variant="destructive" onClick={() => setConfirmOpen(true)}>
            <Trash2 size={14} /> Delete account
          </Button>
        </div>
      )}

      {confirmOpen && (
        <DeleteModal
          onClose={() => setConfirmOpen(false)}
          onDone={() => {
            setConfirmOpen(false)
            onChanged()
          }}
        />
      )}
    </SettingsSection>
  )
}

function DeleteModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [text, setText] = useState('')
  const mut = useMutation({
    mutationFn: () => deleteAccount(text),
    onSuccess: () => {
      showToast('Account scheduled for deletion', 'success')
      onDone()
    },
    onError: e => showToast(e instanceof Error ? e.message : 'Could not delete account', 'error'),
  })
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Delete account"
      size="sm"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Keep my account
          </Button>
          <Button
            variant="destructive"
            disabled={text.trim().toUpperCase() !== 'DELETE'}
            loading={mut.isPending}
            onClick={() => mut.mutate()}
          >
            Delete my account
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="flex items-start gap-2 rounded-lg border border-error/40 bg-error-soft/40 p-3 text-sm text-foreground">
          <AlertTriangle size={16} className="text-error mt-0.5 shrink-0" />
          This starts a 30-day grace period. After that, your profile, applications, and data are
          permanently erased. You can undo any time before then.
        </div>
        <Input
          label='Type "DELETE" to confirm'
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="DELETE"
        />
      </div>
    </Modal>
  )
}
