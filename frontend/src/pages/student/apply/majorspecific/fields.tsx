// Spec 43 — generic field widgets driven by the catalog field `kind`. One
// dispatcher (`TrackField`) renders the right control so all 15 tracks share a
// single, catalog-driven renderer (no hand-coded per-track forms).
import clsx from 'clsx'
import { useState } from 'react'
import { X } from 'lucide-react'

import type { CatalogField, TrackSignalValue } from '../../../../types/majorSpecific'

import { RATING_LABELS } from './constants'

const inputCls =
  'w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground ' +
  'placeholder:text-muted-foreground/60 focus:border-secondary focus:outline-none'

function RatingScale({
  value,
  onChange,
  id,
}: {
  value: number | undefined
  onChange: (v: number | undefined) => void
  id: string
}) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1" role="radiogroup" aria-labelledby={id}>
        {[1, 2, 3, 4, 5].map(n => {
          const active = value != null && n <= value
          const selected = value === n
          return (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-label={`${n} — ${RATING_LABELS[n]}`}
              onClick={() => onChange(value === n ? undefined : n)}
              className={clsx(
                'h-7 w-7 rounded-md border text-xs font-semibold transition-colors',
                active
                  ? 'border-secondary bg-secondary text-secondary-foreground'
                  : 'border-border bg-background text-muted-foreground hover:border-secondary/60',
              )}
            >
              {n}
            </button>
          )
        })}
      </div>
      <span className="min-w-[64px] text-xs text-muted-foreground">
        {value != null ? RATING_LABELS[value] : '—'}
      </span>
    </div>
  )
}

function TagInput({
  value,
  onChange,
  options,
}: {
  value: string[]
  onChange: (v: string[]) => void
  options?: string[]
}) {
  const [draft, setDraft] = useState('')
  const add = (raw: string) => {
    const t = raw.trim()
    if (t && !value.includes(t)) onChange([...value, t])
    setDraft('')
  }
  return (
    <div>
      <div className="flex flex-wrap items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1.5">
        {value.map(t => (
          <span
            key={t}
            className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-foreground"
          >
            {t}
            <button
              type="button"
              aria-label={`Remove ${t}`}
              onClick={() => onChange(value.filter(x => x !== t))}
              className="text-muted-foreground hover:text-foreground"
            >
              <X size={12} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ',') {
              e.preventDefault()
              add(draft)
            } else if (e.key === 'Backspace' && !draft && value.length) {
              onChange(value.slice(0, -1))
            }
          }}
          list={options?.length ? 'taginput-options' : undefined}
          placeholder={value.length ? '' : 'Type and press Enter…'}
          className="min-w-[120px] flex-1 bg-transparent py-0.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
        />
        {options?.length ? (
          <datalist id="taginput-options">
            {options.map(o => (
              <option key={o} value={o} />
            ))}
          </datalist>
        ) : null}
      </div>
    </div>
  )
}

export default function TrackField({
  field,
  value,
  onChange,
}: {
  field: CatalogField
  value: TrackSignalValue | undefined
  onChange: (v: TrackSignalValue | undefined) => void
}) {
  const id = `f-${field.key}`
  const label = (
    <label id={id} htmlFor={id} className="text-sm text-foreground">
      {field.label}
      {field.unit ? <span className="text-muted-foreground"> ({field.unit})</span> : null}
    </label>
  )

  // Rating rows put the label + control on one line (dense, scannable).
  if (field.kind === 'rating_1_5') {
    return (
      <div className="flex flex-wrap items-center justify-between gap-2 py-1">
        {label}
        <RatingScale
          id={id}
          value={typeof value === 'number' ? value : undefined}
          onChange={onChange}
        />
      </div>
    )
  }

  if (field.kind === 'bool') {
    return (
      <label className="flex cursor-pointer items-center gap-2 py-1 text-sm text-foreground">
        <input
          type="checkbox"
          checked={value === true}
          onChange={e => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-border text-secondary focus:ring-secondary"
        />
        {field.label}
      </label>
    )
  }

  return (
    <div className="space-y-1 py-1">
      {label}
      {field.kind === 'enum' ? (
        <select
          id={id}
          value={typeof value === 'string' ? value : ''}
          onChange={e => onChange(e.target.value || undefined)}
          className={inputCls}
        >
          <option value="">Select…</option>
          {(field.options ?? []).map(o => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      ) : field.kind === 'tags' ? (
        <TagInput
          value={Array.isArray(value) ? value : []}
          onChange={v => onChange(v.length ? v : undefined)}
          options={field.options}
        />
      ) : field.kind === 'number' ? (
        <input
          id={id}
          type="number"
          min={0}
          value={typeof value === 'number' ? value : ''}
          onChange={e => onChange(e.target.value === '' ? undefined : Number(e.target.value))}
          className={inputCls}
        />
      ) : (
        <input
          id={id}
          type={field.kind === 'link' ? 'url' : 'text'}
          value={typeof value === 'string' ? value : ''}
          onChange={e => onChange(e.target.value || undefined)}
          placeholder={field.kind === 'link' ? 'https://…' : ''}
          className={inputCls}
        />
      )}
    </div>
  )
}
