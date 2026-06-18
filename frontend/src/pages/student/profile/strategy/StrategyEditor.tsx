/**
 * Strategy editor (Spec 2026-06-15 Ship B) — the "develop" half of the living
 * strategy doc. Edits career / degree / narrative AND the three path tracks
 * (academic · financial · geographic). The backend PATCH already accepts the
 * path arrays; saving creates a new draft (clone-and-modify), not auto-activated.
 */
import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import Button from '../../../../components/ui/Button'
import type {
  UpdateStrategyBody,
  StudentStrategy,
  AcademicPathStep,
  FinancialPathItem,
  GeographicPathItem,
} from '../../../../api/strategy'

const fieldCls =
  'w-full rounded-md border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-secondary'

function csvToList(v: string): string[] {
  return v.split(',').map(s => s.trim()).filter(Boolean)
}

interface Props {
  initial: StudentStrategy
  onCancel: () => void
  onSubmit: (body: UpdateStrategyBody) => void
  submitting: boolean
}

export default function StrategyEditor({ initial, onCancel, onSubmit, submitting }: Props) {
  const [career, setCareer] = useState(initial.career_target ?? '')
  const [degree, setDegree] = useState(initial.target_degree ?? '')
  const [narrative, setNarrative] = useState(initial.narrative ?? '')
  const [academic, setAcademic] = useState<AcademicPathStep[]>(initial.academic_path ?? [])
  const [financial, setFinancial] = useState<FinancialPathItem[]>(initial.financial_path ?? [])
  const [geographic, setGeographic] = useState<GeographicPathItem[]>(initial.geographic_path ?? [])

  return (
    <form
      onSubmit={e => {
        e.preventDefault()
        onSubmit({
          career_target: career.trim() || null,
          target_degree: degree.trim() || null,
          narrative: narrative.trim() || null,
          academic_path: academic,
          financial_path: financial,
          geographic_path: geographic,
        })
      }}
      className="space-y-5"
    >
      <div>
        <label htmlFor="strategy-career-target" className="block text-sm font-medium text-foreground mb-1">Career target</label>
        <input id="strategy-career-target" className={fieldCls} maxLength={500} value={career}
          onChange={e => setCareer(e.target.value)}
          placeholder="e.g., Family medicine physician practicing in underserved areas." />
      </div>
      <div>
        <label htmlFor="strategy-target-degree" className="block text-sm font-medium text-foreground mb-1">Target degree</label>
        <input id="strategy-target-degree" className={fieldCls} maxLength={120} value={degree}
          onChange={e => setDegree(e.target.value)} placeholder="e.g., MD, MBA, PhD" />
      </div>
      <div>
        <label htmlFor="strategy-narrative" className="block text-sm font-medium text-foreground mb-1">Narrative</label>
        <textarea id="strategy-narrative" className={fieldCls} rows={8} maxLength={20000} value={narrative}
          onChange={e => setNarrative(e.target.value)} placeholder="The prose explanation of your strategy." />
      </div>

      {/* Academic path */}
      <TrackEditor
        title="Academic path"
        rows={academic}
        onAdd={() => setAcademic([...academic, { step: '', options: [], rationale: '' }])}
        onRemove={i => setAcademic(academic.filter((_, x) => x !== i))}
        render={(row, i) => (
          <>
            <input className={fieldCls} value={row.step} placeholder="Step (e.g., Complete prerequisite coursework)"
              onChange={e => setAcademic(academic.map((r, x) => x === i ? { ...r, step: e.target.value } : r))} />
            <input className={fieldCls} value={row.options.join(', ')} placeholder="Options (comma-separated)"
              onChange={e => setAcademic(academic.map((r, x) => x === i ? { ...r, options: csvToList(e.target.value) } : r))} />
            <input className={fieldCls} value={row.rationale} placeholder="Why this step matters"
              onChange={e => setAcademic(academic.map((r, x) => x === i ? { ...r, rationale: e.target.value } : r))} />
          </>
        )}
      />

      {/* Financial path */}
      <TrackEditor
        title="Financial path"
        rows={financial}
        onAdd={() => setFinancial([...financial, { aid_type: '', eligibility: '', estimated_value: null }])}
        onRemove={i => setFinancial(financial.filter((_, x) => x !== i))}
        render={(row, i) => (
          <>
            <input className={fieldCls} value={row.aid_type} placeholder="Aid type (e.g., Need-based grant)"
              onChange={e => setFinancial(financial.map((r, x) => x === i ? { ...r, aid_type: e.target.value } : r))} />
            <input className={fieldCls} value={row.eligibility} placeholder="Eligibility"
              onChange={e => setFinancial(financial.map((r, x) => x === i ? { ...r, eligibility: e.target.value } : r))} />
            <input className={fieldCls} value={row.estimated_value ?? ''} placeholder="Estimated value (optional)"
              onChange={e => setFinancial(financial.map((r, x) => x === i ? { ...r, estimated_value: e.target.value.trim() || null } : r))} />
          </>
        )}
      />

      {/* Geographic path */}
      <TrackEditor
        title="Geographic path"
        rows={geographic}
        onAdd={() => setGeographic([...geographic, { region: '', rationale: '', constraints: [] }])}
        onRemove={i => setGeographic(geographic.filter((_, x) => x !== i))}
        render={(row, i) => (
          <>
            <input className={fieldCls} value={row.region} placeholder="Region (e.g., US Northeast)"
              onChange={e => setGeographic(geographic.map((r, x) => x === i ? { ...r, region: e.target.value } : r))} />
            <input className={fieldCls} value={row.rationale} placeholder="Why this region"
              onChange={e => setGeographic(geographic.map((r, x) => x === i ? { ...r, rationale: e.target.value } : r))} />
            <input className={fieldCls} value={row.constraints.join(', ')} placeholder="Constraints (comma-separated)"
              onChange={e => setGeographic(geographic.map((r, x) => x === i ? { ...r, constraints: csvToList(e.target.value) } : r))} />
          </>
        )}
      />

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={submitting}>Save as new draft</Button>
      </div>
    </form>
  )
}

function TrackEditor<T>({
  title, rows, onAdd, onRemove, render,
}: {
  title: string
  rows: T[]
  onAdd: () => void
  onRemove: (i: number) => void
  render: (row: T, i: number) => React.ReactNode
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs uppercase tracking-wide text-muted-foreground">{title}</span>
        <Button type="button" size="sm" variant="ghost" onClick={onAdd}><Plus size={13} className="mr-1" />Add</Button>
      </div>
      {rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">None yet</p>
      ) : (
        <div className="space-y-3">
          {rows.map((row, i) => (
            <div key={i} className="rounded-lg border border-border p-3 space-y-2">
              <div className="flex justify-end">
                <button type="button" aria-label="Remove" onClick={() => onRemove(i)} className="text-muted-foreground hover:text-error">
                  <Trash2 size={14} />
                </button>
              </div>
              {render(row, i)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
