/**
 * AI Structure (Spec 2/3) — recruiting-preference editor for a claimed program.
 *
 * Self-contained: fetches + saves its own state via the preferences API, so it
 * drops into the program editor without touching that page's form state. Saving
 * stamps the row first-party (source="claimed"), so the enrichment routine never
 * overwrites it. Powers the program→student match direction (CPEF p2s).
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import Button from '../../../components/ui/Button'
import { showToast } from '../../../stores/toast-store'
import { getProgramPreferences, updateProgramPreferences } from '../../../api/institutions'

const QK = (id: string) => ['program-preferences', id]

function parseList(s: string): string[] | null {
  const arr = s.split(',').map((x) => x.trim()).filter(Boolean)
  return arr.length ? arr : null
}

const INPUT = 'mt-1 w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm'

export default function ProgramPreferenceEditor({ programId }: { programId: string }) {
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: QK(programId),
    queryFn: () => getProgramPreferences(programId),
    enabled: !!programId,
  })

  const [gpa, setGpa] = useState('')
  const [fields, setFields] = useState('')
  const [levels, setLevels] = useState('')
  const [wAcademic, setWAcademic] = useState('')

  useEffect(() => {
    if (!data) return
    setGpa(data.pref_min_gpa != null ? String(data.pref_min_gpa) : '')
    setFields((data.pref_fields ?? []).join(', '))
    setLevels((data.pref_levels ?? []).join(', '))
    setWAcademic(data.weight_academic != null ? String(data.weight_academic) : '')
  }, [data])

  const mutation = useMutation({
    mutationFn: () =>
      updateProgramPreferences(programId, {
        pref_min_gpa: gpa ? Number(gpa) : null,
        pref_fields: parseList(fields),
        pref_levels: parseList(levels),
        weight_academic: wAcademic ? Number(wAcademic) : null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK(programId) })
      showToast('Recruiting preferences saved', 'success')
    },
    onError: () => showToast('Could not save preferences', 'error'),
  })

  if (!programId) return null

  return (
    <div className="mt-4 rounded-lg border border-border bg-card p-5">
      <p className="text-sm font-medium text-foreground">Recruiting preferences</p>
      <p className="mb-4 mt-1 text-xs text-muted-foreground">
        Your target applicant — this shapes which students the matcher surfaces for this
        program. Once you save it here it&apos;s yours; the enrichment routine won&apos;t overwrite it.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          <span className="text-muted-foreground">Min GPA (e.g. 3.5)</span>
          <input
            type="number"
            step="0.01"
            value={gpa}
            onChange={(e) => setGpa(e.target.value)}
            className={INPUT}
          />
        </label>
        <label className="text-sm">
          <span className="text-muted-foreground">Academic importance (0–10)</span>
          <input
            type="number"
            min={0}
            max={10}
            value={wAcademic}
            onChange={(e) => setWAcademic(e.target.value)}
            className={INPUT}
          />
        </label>
        <label className="text-sm sm:col-span-2">
          <span className="text-muted-foreground">Preferred fields (comma-separated)</span>
          <input
            value={fields}
            onChange={(e) => setFields(e.target.value)}
            placeholder="data science, statistics"
            className={INPUT}
          />
        </label>
        <label className="text-sm sm:col-span-2">
          <span className="text-muted-foreground">Preferred applicant levels (comma-separated)</span>
          <input
            value={levels}
            onChange={(e) => setLevels(e.target.value)}
            placeholder="bachelors"
            className={INPUT}
          />
        </label>
      </div>
      <div className="mt-3 flex items-center justify-end gap-3">
        {data?.source === 'derived' && (
          <span className="text-xs text-muted-foreground">
            currently auto-derived — saving makes it yours
          </span>
        )}
        <Button
          variant="secondary"
          size="sm"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          Save preferences
        </Button>
      </div>
    </div>
  )
}
