import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from '../../../../components/ui/Modal'
import Button from '../../../../components/ui/Button'
import { showToast } from '../../../../stores/toast-store'
import { respondToOfferV2, bulkWithdraw } from '../../../../api/offers'
import type { WithdrawableApp } from '../../../../types'
import { PartyPopper, Check } from 'lucide-react'

type Step = 'confirm' | 'withdraw' | 'done'

export default function AcceptOfferModal({
  appId,
  offerId,
  institutionName,
  isOpen,
  onClose,
}: {
  appId: string
  offerId: string
  institutionName: string
  isOpen: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>('confirm')
  const [withdrawable, setWithdrawable] = useState<WithdrawableApp[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['application', appId] })
    queryClient.invalidateQueries({ queryKey: ['my-applications'] })
    queryClient.invalidateQueries({ queryKey: ['offers-comparison'] })
  }

  const acceptMut = useMutation({
    mutationFn: () => respondToOfferV2(appId, offerId, 'accepted'),
    onSuccess: result => {
      invalidate()
      const others = result.withdrawable_apps || []
      setWithdrawable(others)
      setSelected(new Set(others.map(a => a.id)))
      setStep(others.length > 0 ? 'withdraw' : 'done')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not accept the offer', 'error'),
  })

  const withdrawMut = useMutation({
    mutationFn: () => bulkWithdraw(Array.from(selected)),
    onSuccess: () => {
      invalidate()
      setStep('done')
    },
    onError: () => showToast('Could not withdraw the other applications', 'error'),
  })

  const close = () => {
    setStep('confirm')
    setWithdrawable([])
    setSelected(new Set())
    onClose()
  }

  const toggle = (id: string) =>
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  return (
    <Modal
      isOpen={isOpen}
      onClose={close}
      title={step === 'done' ? '' : 'Accept this offer'}
    >
      {step === 'confirm' && (
        <div className="space-y-4">
          <p className="text-sm text-student-ink">
            You're about to accept your offer from{' '}
            <span className="font-semibold">{institutionName}</span>. This confirms your decision
            and starts your enrollment steps.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={close}>
              Not yet
            </Button>
            {/* Gold — the rare earned accent (spec 18 §10). */}
            <Button variant="primary" loading={acceptMut.isPending} onClick={() => acceptMut.mutate()}>
              Accept offer
            </Button>
          </div>
        </div>
      )}

      {step === 'withdraw' && (
        <div className="space-y-4">
          <p className="text-sm text-student-ink">
            Now that you've accepted, would you like to withdraw your other open applications? You
            can keep any you're still considering.
          </p>
          <div className="space-y-2">
            {withdrawable.map(a => (
              <label
                key={a.id}
                className="flex items-center gap-3 rounded-lg border border-divider px-3 py-2 cursor-pointer hover:bg-student-mist"
              >
                <input
                  type="checkbox"
                  checked={selected.has(a.id)}
                  onChange={() => toggle(a.id)}
                  className="rounded border-divider text-cobalt focus:ring-cobalt"
                />
                <span className="min-w-0">
                  <span className="block text-sm text-student-ink truncate">
                    {a.program_name || 'Application'}
                  </span>
                  {a.institution_name && (
                    <span className="block text-xs text-student-text">{a.institution_name}</span>
                  )}
                </span>
              </label>
            ))}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setStep('done')}>
              Keep them all
            </Button>
            <Button
              variant="secondary"
              loading={withdrawMut.isPending}
              disabled={selected.size === 0}
              onClick={() => withdrawMut.mutate()}
            >
              Withdraw {selected.size > 0 ? selected.size : ''} selected
            </Button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="text-center py-4">
          <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-success-soft flex items-center justify-center">
            <PartyPopper size={30} className="text-success" />
          </div>
          {/* The one soft moment in the app (spec 18 §13). */}
          <h2 className="text-2xl font-bold text-student-ink mb-1">You're in. Congrats.</h2>
          <p className="text-sm text-student-text mb-5">
            Your enrollment steps are on your calendar — deposit, orientation, and housing.
          </p>
          <Button variant="secondary" onClick={close} className="mx-auto">
            <Check size={16} className="mr-1" /> Done
          </Button>
        </div>
      )}
    </Modal>
  )
}
