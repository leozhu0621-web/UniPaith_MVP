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

const MONEY_RE = /^\s*\$?\s*(\d+|\d{1,3}(,\d{3})+)(\.\d{1,2})?\s*$/
const FIELD_NAMES = ['scholarship', 'currency', 'tuition', 'totalCost', 'deadline', 'season', 'year'] as const

type FieldName = typeof FIELD_NAMES[number]
type FormErrors = Partial<Record<FieldName, string>>
type TouchedState = Partial<Record<FieldName, boolean>>

function moneyError(label: string, value: string): string | undefined {
  if (!value.trim()) return undefined
  return MONEY_RE.test(value) ? undefined : `Enter ${label.toLowerCase()} as a dollar amount, like 20000.`
}

function validateOfferForm({
  scholarship,
  currency,
  tuition,
  totalCost,
  deadline,
  season,
  year,
}: {
  scholarship: string
  currency: string
  tuition: string
  totalCost: string
  deadline: string
  season: string
  year: string
}): FormErrors {
  const errors: FormErrors = {}
  const scholarshipError = moneyError('Scholarship amount', scholarship)
  const tuitionError = moneyError('Tuition estimate', tuition)
  const totalCostError = moneyError('Total cost estimate', totalCost)
  if (scholarshipError) errors.scholarship = scholarshipError
  if (tuitionError) errors.tuition = tuitionError
  if (totalCostError) errors.totalCost = totalCostError

  if (!/^[A-Z]{3}$/.test(currency.trim())) {
    errors.currency = 'Use a 3-letter currency code such as USD.'
  }

  if (deadline) {
    const selected = new Date(`${deadline}T00:00:00`)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    if (Number.isNaN(selected.getTime())) {
      errors.deadline = 'Use a valid response deadline.'
    } else if (selected < today) {
      errors.deadline = 'Use today or a future response deadline.'
    }
  }

  if (year.trim() && !season) {
    errors.season = 'Choose a start term season for this year.'
  }
  if (season && !year.trim()) {
    errors.year = 'Add the year for this start term.'
  } else if (year.trim()) {
    const parsedYear = Number(year)
    const currentYear = new Date().getFullYear()
    if (!/^\d{4}$/.test(year.trim())) {
      errors.year = 'Use a four-digit year.'
    } else if (parsedYear < currentYear || parsedYear > currentYear + 10) {
      errors.year = `Use a year from ${currentYear} to ${currentYear + 10}.`
    }
  }

  const scholarshipAmount = numeric(scholarship)
  const totalCostAmount = numeric(totalCost)
  if (!errors.scholarship && !errors.totalCost && scholarshipAmount != null && totalCostAmount != null && scholarshipAmount > totalCostAmount) {
    errors.scholarship = 'Scholarship should not be greater than total cost.'
  }

  return errors
}

function friendlyOfferError(detail?: string): string {
  const text = detail?.trim()
  if (!text) return 'Could not record the offer. Check the details and try again.'
  const lower = text.toLowerCase()
  if (lower.includes('deadline')) return 'Check the response deadline and try again.'
  if (lower.includes('currency')) return 'Check the currency code and try again.'
  if (lower.includes('amount') || lower.includes('cost') || lower.includes('tuition')) return 'Check the cost and scholarship amounts, then try again.'
  return text
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
  const [touched, setTouched] = useState<TouchedState>({})
  const [submitAttempted, setSubmitAttempted] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const validationErrors = validateOfferForm({ scholarship, currency, tuition, totalCost, deadline, season, year })
  const errorFor = (field: FieldName) => (submitAttempted || touched[field] ? validationErrors[field] : undefined)
  const markTouched = (field: FieldName) => setTouched(prev => ({ ...prev, [field]: true }))
  const clearServerError = () => {
    if (formError) setFormError(null)
  }

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
    setTouched({})
    setSubmitAttempted(false)
    setFormError(null)
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
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const message = friendlyOfferError(err.response?.data?.detail)
      setFormError(message)
      showToast(message, 'error')
    },
  })

  const saveOffer = () => {
    setSubmitAttempted(true)
    setTouched(FIELD_NAMES.reduce<TouchedState>((acc, field) => ({ ...acc, [field]: true }), {}))
    if (Object.keys(validationErrors).length > 0) {
      setFormError('Fix the highlighted fields before saving this offer.')
      return
    }
    setFormError(null)
    mut.mutate()
  }

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
          onChange={e => { setOfferType(e.target.value); clearServerError() }}
        />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Scholarship amount"
            inputMode="numeric"
            placeholder="20000"
            value={scholarship}
            onBlur={() => markTouched('scholarship')}
            onChange={e => { setScholarship(e.target.value); clearServerError() }}
            error={errorFor('scholarship')}
            helperText="Optional. Use the amount shown in the offer letter."
          />
          <Input
            label="Currency"
            value={currency}
            onBlur={() => markTouched('currency')}
            onChange={e => { setCurrency(e.target.value.toUpperCase().slice(0, 3)); clearServerError() }}
            error={errorFor('currency')}
            success={touched.currency && !validationErrors.currency ? 'Currency looks valid.' : undefined}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Tuition estimate (/yr)"
            inputMode="numeric"
            placeholder="48000"
            value={tuition}
            onBlur={() => markTouched('tuition')}
            onChange={e => { setTuition(e.target.value); clearServerError() }}
            error={errorFor('tuition')}
            helperText="Optional annual tuition before scholarships."
          />
          <Input
            label="Total cost estimate"
            inputMode="numeric"
            placeholder="96000"
            value={totalCost}
            onBlur={() => markTouched('totalCost')}
            onChange={e => { setTotalCost(e.target.value); clearServerError() }}
            error={errorFor('totalCost')}
            helperText="Optional full attendance estimate."
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Input
            label="Respond by"
            type="date"
            value={deadline}
            onBlur={() => markTouched('deadline')}
            onChange={e => { setDeadline(e.target.value); clearServerError() }}
            error={errorFor('deadline')}
            helperText="Leave blank if the school has not set one."
          />
          <Select
            label="Start term"
            options={SEASONS}
            value={season}
            onBlur={() => markTouched('season')}
            onChange={e => { setSeason(e.target.value); clearServerError() }}
            error={errorFor('season')}
          />
          <Input
            label="Year"
            inputMode="numeric"
            placeholder="2027"
            value={year}
            onBlur={() => markTouched('year')}
            onChange={e => { setYear(e.target.value.replace(/\D/g, '').slice(0, 4)); clearServerError() }}
            error={errorFor('year')}
          />
        </div>
        <Textarea
          label="Conditions (optional)"
          placeholder="e.g. complete the linear algebra prerequisite by August"
          value={conditions}
          onChange={e => { setConditions(e.target.value); clearServerError() }}
          helperText="Capture constraints, deposit notes, or prerequisites exactly as written."
        />
        {formError && (
          <div role="alert" className="rounded-lg border border-error/30 bg-error-soft px-3 py-2 text-sm text-error">
            {formError}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="tertiary" onClick={() => { resetForm(); onClose() }}>
            Cancel
          </Button>
          <Button variant="secondary" loading={mut.isPending} onClick={saveOffer}>
            Save offer
          </Button>
        </div>
      </div>
    </Modal>
  )
}
