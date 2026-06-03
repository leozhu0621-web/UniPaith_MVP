import { useState } from 'react'
import { Plus } from 'lucide-react'
import type { SignalDef, SignalDictionary } from '../../../types'

interface Props {
  dict: SignalDictionary | undefined
  onPick: (signal: SignalDef) => void
  label?: string
}

/** Spec 26 §3 — "+ Add rule": pick a signal from the dictionary, grouped by
 *  category. The chosen signal is appended to the branch as a default rule. */
export default function SignalPicker({ dict, onPick, label = 'Add rule' }: Props) {
  const [open, setOpen] = useState(false)
  const categories = dict?.categories ?? []
  const byCat = (catKey: string) => (dict?.signals ?? []).filter((s) => s.category === catKey)

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 rounded-full border border-dashed border-secondary px-3 py-1 text-sm text-secondary hover:bg-secondary/5"
      >
        <Plus size={14} /> {label}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} aria-hidden />
          <div className="absolute top-full left-0 z-20 mt-1 max-h-80 w-72 overflow-y-auto rounded-lg border border-border bg-surface p-2 shadow-lg">
            {categories.map((cat) => {
              const sigs = byCat(cat.key)
              if (!sigs.length) return null
              return (
                <div key={cat.key} className="mb-2 last:mb-0">
                  <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {cat.label}
                  </p>
                  {sigs.map((s) => (
                    <button
                      key={s.key}
                      type="button"
                      onClick={() => {
                        onPick(s)
                        setOpen(false)
                      }}
                      className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted"
                    >
                      <span>{s.label}</span>
                      {s.protected && (
                        <span className="ml-2 rounded bg-warning-soft px-1 text-[10px] text-warning">
                          protected
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )
            })}
          </div>
        </>
      )}
    </span>
  )
}
