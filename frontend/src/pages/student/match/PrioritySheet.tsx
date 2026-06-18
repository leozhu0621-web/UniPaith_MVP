/**
 * Spec 09 §5.2 — "Refine priorities" sheet.
 *
 * Six 0–10 importance sliders. Save writes the weights to
 * `student_preferences` (PUT /me/preferences) and triggers a match re-rank
 * (the parent's onSaved → refreshMatches). The 6 sliders map to the
 * persisted weight_* fields used by the matcher's priority→weight mapping.
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { getPreferences, upsertPreferences } from '../../../api/students'
import Button from '../../../components/ui/Button'
import Sheet from '../../../components/ui/Sheet'
import { showToast } from '../../../stores/toast-store'

type WeightKey =
  | 'weight_cost'
  | 'weight_outcomes'
  | 'weight_ranking'
  | 'weight_location'
  | 'weight_flexibility'
  | 'weight_time_to_degree'

// Spec 09 §5.2 slider order + labels.
const SLIDERS: Array<{ key: WeightKey; label: string }> = [
  { key: 'weight_cost', label: 'Cost' },
  { key: 'weight_outcomes', label: 'Outcomes' },
  { key: 'weight_ranking', label: 'Selectivity' },
  { key: 'weight_location', label: 'Location' },
  { key: 'weight_flexibility', label: 'Modality' },
  { key: 'weight_time_to_degree', label: 'Time to degree' },
]

const DEFAULT = 5

type Weights = Record<WeightKey, number>

export interface PrioritySheetProps {
  isOpen: boolean
  onClose: () => void
  /** Fired after a successful save so the parent can re-rank matches. */
  onSaved: () => void
}

export default function PrioritySheet({ isOpen, onClose, onSaved }: PrioritySheetProps) {
  const { data: prefs } = useQuery({
    queryKey: ['preferences'],
    queryFn: getPreferences,
    enabled: isOpen,
    retry: false,
  })

  const [weights, setWeights] = useState<Weights>(() =>
    Object.fromEntries(SLIDERS.map(s => [s.key, DEFAULT])) as Weights,
  )

  // Seed from server prefs once they arrive (and on each open).
  useEffect(() => {
    if (!prefs) return
    setWeights(
      Object.fromEntries(
        SLIDERS.map(s => [s.key, (prefs as Record<string, number | null>)[s.key] ?? DEFAULT]),
      ) as Weights,
    )
  }, [prefs])

  const saveMut = useMutation({
    mutationFn: () => upsertPreferences(weights),
    onSuccess: () => {
      showToast('Priorities saved — re-ranking your matches.', 'success')
      onSaved()
      onClose()
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not save priorities.', 'error'),
  })

  const set = (key: WeightKey, value: number) =>
    setWeights(prev => ({ ...prev, [key]: value }))

  return (
    <Sheet
      isOpen={isOpen}
      onClose={onClose}
      title="Refine priorities"
      footer={
        <>
          <Button variant="tertiary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" variant="secondary" onClick={() => saveMut.mutate()} loading={saveMut.isPending}>
            Save &amp; re-rank
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        {SLIDERS.map(s => (
          <div key={s.key}>
            <div className="flex items-baseline justify-between mb-1">
              <label htmlFor={s.key} className="text-sm font-medium text-foreground">
                {s.label}
              </label>
              <span className="text-xs font-bold text-secondary tabular-nums">{weights[s.key]}</span>
            </div>
            <input
              id={s.key}
              type="range"
              min={0}
              max={10}
              step={1}
              value={weights[s.key]}
              onChange={e => set(s.key, Number(e.target.value))}
              className="w-full accent-secondary cursor-pointer"
            />
          </div>
        ))}
      </div>
    </Sheet>
  )
}
