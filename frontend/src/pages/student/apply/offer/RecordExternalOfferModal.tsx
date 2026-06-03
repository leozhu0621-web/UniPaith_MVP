import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from '../../../../components/ui/Modal'
import Input from '../../../../components/ui/Input'
import Select from '../../../../components/ui/Select'
import Textarea from '../../../../components/ui/Textarea'
import Button from '../../../../components/ui/Button'
import { showToast } from '../../../../stores/toast-store'
import { recordExternalOffer, type RecordOfferPayload } from '../../../../api/offers'

const OFFER_TYPES = [
  { value: 'full_admission', label: 'Full admission' },
  { value: 'conditional', label: 'Conditional offer' },
  { value: 'waitlist_to_admit', label: 'Waitlist-to-admit' },
  { value: 'partial', label: 'Partial offer' },
  { value: 'transfer_credit_offer', label: 'Transfer credit offer' },
]
const SEASONS = [
  { value: '', label: '—' },
  { value: 'Fall', label: 'Fall' },
  { value: 'Spring', label: 'Spring' },
  { value: 'Summer', label: 'Summer' },
  { value: 'Winter', label: 'Winter' },
]

const numeric = (v: string): number | null => {
  const n = Number(v.replace(/[^0-9.]/g, ''))
  return v.trim() === '' || Number.isNaN(n) ? null : Math.round(n)
}

export default function RecordExternalOfferModal({
  appId,
  isOpen,
  onClose,
}: {
  appId: string
  isOpen: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [offerType, setOfferType] = useState('full_admission')
  const [scholarship, setScholarship] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [tuition, setTuition] = useState('')
  const [totalCost, setTotalCost] = useState('')
  const [deadline, setDeadline] = useState('')
  const [season, setSeason] = useState('')
  const [year, setYear] = useState('')
  const [conditions, setConditions] = useState('')

  const resetForm = () => {
    setOfferType('full_admission')
    setScholarship('')
    setCurrency('USD')
    setTuition('')
    setTotalCost('')
    setDeadline('')
    setSeason('')
    setYear('')
    setConditions('')
  }

  const mut = useMutation({
    mutationFn: () => {
      const payload: RecordOfferPayload = {
        offer_type: offerType,
        scholarship_amount: numeric(scholarship),
        scholarship_currency: currency || 'USD',
        tuition_estimate: numeric(tuition),
        total_cost_estimate: numeric(totalCost),
        response_deadline: deadline || null,
        start_term: season ? { season, year: numeric(year) ?? undefined } : null,
        conditions: conditions.trim() ? { summary: conditions.trim() } : null,
      }
      return recordExternalOffer(appId, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      queryClient.invalidateQueries({ queryKey: ['offers-comparison'] })
      showToast('Offer recorded', 'success')
      resetForm()
      onClose()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      showToast(err.response?.data?.detail || 'Could not record the offer', 'error'),
  })

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        resetForm()
        onClose()
      }}
      title="Record an offer you received"
      size="lg"
    >
      <div className="space-y-3">
        <p className="text-sm text-foreground">
          Applied somewhere off-platform? Add the offer here to compare it alongside the rest.
        </p>
        <Select
          label="Offer type"
          options={OFFER_TYPES}
          value={offerType}
          onChange={e => setOfferType(e.target.value)}
        />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Scholarship amount"
            inputMode="numeric"
            placeholder="20000"
            value={scholarship}
            onChange={e => setScholarship(e.target.value)}
          />
          <Input
            label="Currency"
            value={currency}
            onChange={e => setCurrency(e.target.value.toUpperCase().slice(0, 8))}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Tuition estimate (/yr)"
            inputMode="numeric"
            placeholder="48000"
            value={tuition}
            onChange={e => setTuition(e.target.value)}
          />
          <Input
            label="Total cost estimate"
            inputMode="numeric"
            placeholder="96000"
            value={totalCost}
            onChange={e => setTotalCost(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Input
            label="Respond by"
            type="date"
            value={deadline}
            onChange={e => setDeadline(e.target.value)}
          />
          <Select
            label="Start term"
            options={SEASONS}
            value={season}
            onChange={e => setSeason(e.target.value)}
          />
          <Input
            label="Year"
            inputMode="numeric"
            placeholder="2027"
            value={year}
            onChange={e => setYear(e.target.value)}
          />
        </div>
        <Textarea
          label="Conditions (optional)"
          placeholder="e.g. complete the linear algebra prerequisite by August"
          value={conditions}
          onChange={e => setConditions(e.target.value)}
        />
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="tertiary" onClick={() => { resetForm(); onClose() }}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} onClick={() => mut.mutate()}>
            Save offer
          </Button>
        </div>
      </div>
    </Modal>
  )
}
