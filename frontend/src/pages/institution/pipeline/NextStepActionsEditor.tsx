import { Plus, X } from 'lucide-react'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'

export type NextStepRow = { action: string; by_date: string }

/** Spec 34 §4 — optional next-step actions on an offer. */
export default function NextStepActionsEditor({
  rows,
  onChange,
}: {
  rows: NextStepRow[]
  onChange: (rows: NextStepRow[]) => void
}) {
  const update = (index: number, patch: Partial<NextStepRow>) => {
    onChange(rows.map((r, i) => (i === index ? { ...r, ...patch } : r)))
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-gray-500">Next steps (optional)</p>
      {rows.map((row, i) => (
        <div key={i} className="flex flex-wrap items-end gap-2">
          <Input
            label={i === 0 ? 'Action' : ''}
            value={row.action}
            onChange={e => update(i, { action: e.target.value })}
            placeholder="e.g. Submit deposit"
            className="flex-1 min-w-[10rem]"
          />
          <Input
            label={i === 0 ? 'By date' : ''}
            type="date"
            value={row.by_date}
            onChange={e => update(i, { by_date: e.target.value })}
            className="w-40"
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label="Remove step"
            onClick={() => onChange(rows.filter((_, j) => j !== i))}
            className="mb-0.5"
          >
            <X size={14} />
          </Button>
        </div>
      ))}
      {rows.length < 4 && (
        <Button
          type="button"
          variant="tertiary"
          size="sm"
          onClick={() => onChange([...rows, { action: '', by_date: '' }])}
          className="flex items-center gap-1"
        >
          <Plus size={14} /> Add step
        </Button>
      )}
    </div>
  )
}
