// Spec 23 · Program editor — brand-compliant building blocks.
// All colors reference brand tokens (no gray-*); gold stays punctuation, cobalt
// is the workhorse accent. Each section is collapsible (§8) and carries an
// optional "Advanced (raw JSON)" escape hatch (§2) in restrained warning style.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ChevronDown, ExternalLink, Plus, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'

export function MiniLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="block text-[13px] font-semibold text-muted-foreground mb-1.5">{children}</span>
  )
}

export function SectionCard({
  id,
  index,
  title,
  description,
  children,
  open,
  onToggle,
  crossLink,
  rawValue,
  onApplyRaw,
  invalid,
}: {
  id: string
  index: number
  title: string
  description?: string
  children: React.ReactNode
  open: boolean
  onToggle: () => void
  crossLink?: { label: string; to: string }
  rawValue?: unknown
  onApplyRaw?: (parsed: any) => void
  invalid?: boolean
}) {
  const [showRaw, setShowRaw] = useState(false)
  const [rawText, setRawText] = useState('')
  const [rawError, setRawError] = useState('')

  const openRaw = () => {
    setRawText(JSON.stringify(rawValue ?? null, null, 2))
    setRawError('')
    setShowRaw(v => !v)
  }
  const applyRaw = () => {
    try {
      const parsed = rawText.trim() ? JSON.parse(rawText) : null
      onApplyRaw?.(parsed)
      setRawError('')
      setShowRaw(false)
    } catch (e: any) {
      setRawError(`Invalid JSON: ${e?.message ?? 'parse error'}`)
    }
  }

  return (
    <Card
      className={clsx('overflow-hidden p-0', invalid && 'ring-2 ring-error/60')}
    >
      <button
        id={id}
        type="button"
        onClick={onToggle}
        className="flex w-full scroll-mt-24 items-center justify-between gap-3 px-6 py-4 text-left"
        aria-expanded={open}
        aria-controls={`${id}-body`}
      >
        <span className="flex items-baseline gap-3">
          <span className="text-eyebrow uppercase tracking-[0.22em] text-secondary font-semibold">
            {String(index).padStart(2, '0')}
          </span>
          <span className="text-h3 font-semibold text-foreground">{title}</span>
        </span>
        <ChevronDown
          size={20}
          className={clsx('shrink-0 text-muted-foreground transition-transform duration-200', open && 'rotate-180')}
        />
      </button>

      {open && (
        <div id={`${id}-body`} className="border-t border-border px-6 py-5 space-y-5">
          {description && <p className="text-sm text-muted-foreground -mt-1">{description}</p>}
          {children}

          {(crossLink || onApplyRaw) && (
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              {crossLink ? (
                <Link
                  to={crossLink.to}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-secondary hover:underline"
                >
                  {crossLink.label} <ExternalLink size={14} />
                </Link>
              ) : (
                <span />
              )}
              {onApplyRaw && (
                <button
                  type="button"
                  onClick={openRaw}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-warning hover:underline"
                >
                  <AlertTriangle size={13} /> Advanced (raw JSON)
                </button>
              )}
            </div>
          )}

          {showRaw && onApplyRaw && (
            <div className="rounded-md border border-warning/40 bg-warning-soft/50 p-3 space-y-2">
              <p className="text-xs text-warning">
                Power-user escape hatch. Edits here overwrite the guided fields when applied. Malformed
                JSON is rejected.
              </p>
              <textarea
                className="w-full rounded-md border border-border bg-background p-3 font-mono text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                rows={8}
                value={rawText}
                onChange={e => setRawText(e.target.value)}
                spellCheck={false}
              />
              {rawError && <p className="text-xs text-error">{rawError}</p>}
              <div className="flex gap-2">
                <Button type="button" variant="secondary" size="sm" onClick={applyRaw}>
                  Apply JSON
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowRaw(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

// Generic repeatable list with an add button + per-row remove control.
export function Repeatable<T>({
  items,
  onAdd,
  onRemove,
  addLabel,
  emptyHint,
  renderRow,
}: {
  items: T[]
  onAdd: () => void
  onRemove: (index: number) => void
  addLabel: string
  emptyHint?: string
  renderRow: (item: T, index: number) => React.ReactNode
}) {
  return (
    <div className="space-y-3">
      {items.length === 0 && emptyHint && (
        <p className="text-sm text-muted-foreground italic">{emptyHint}</p>
      )}
      {items.map((item, i) => (
        <div key={i} className="flex items-start gap-2">
          <div className="flex-1 min-w-0">{renderRow(item, i)}</div>
          <button
            type="button"
            onClick={() => onRemove(i)}
            className="mt-1 shrink-0 rounded-md p-1.5 text-muted-foreground hover:text-error hover:bg-error-soft/60 transition-colors"
            aria-label="Remove"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      <Button type="button" variant="ghost" size="sm" onClick={onAdd} className="gap-1.5">
        <Plus size={15} /> {addLabel}
      </Button>
    </div>
  )
}

// Brand toggle (checkbox styled as a labeled control).
export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
}) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer select-none">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={clsx(
          'relative h-5 w-9 shrink-0 rounded-full transition-colors duration-200',
          checked ? 'bg-secondary' : 'bg-border',
        )}
      >
        <span
          className={clsx(
            'absolute top-0.5 h-4 w-4 rounded-full bg-card shadow-sm transition-transform duration-200',
            checked ? 'translate-x-4' : 'translate-x-0.5',
          )}
        />
      </button>
      <span className="text-sm text-foreground">{label}</span>
    </label>
  )
}

// Comma / Enter to add string chips (e.g. accepted tests, common roles, employers).
export function ChipsInput({
  values,
  onChange,
  placeholder,
}: {
  values: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}) {
  const [draft, setDraft] = useState('')
  const commit = () => {
    const v = draft.trim().replace(/,$/, '').trim()
    if (v && !values.includes(v)) onChange([...values, v])
    setDraft('')
  }
  return (
    <div className="rounded-md border border-border bg-background px-2 py-1.5 focus-within:ring-2 focus-within:ring-ring">
      <div className="flex flex-wrap gap-1.5">
        {values.map((v, i) => (
          <span
            key={`${v}-${i}`}
            className="inline-flex items-center gap-1 rounded-full bg-secondary/10 px-2.5 py-0.5 text-xs font-medium text-secondary"
          >
            {v}
            <button
              type="button"
              onClick={() => onChange(values.filter((_, idx) => idx !== i))}
              className="text-secondary/70 hover:text-secondary"
              aria-label={`Remove ${v}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          className="flex-1 min-w-[8rem] bg-transparent py-0.5 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          value={draft}
          placeholder={values.length ? '' : placeholder}
          onChange={e => {
            if (e.target.value.includes(',')) {
              setDraft(e.target.value)
              setTimeout(commit, 0)
            } else setDraft(e.target.value)
          }}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault()
              commit()
            } else if (e.key === 'Backspace' && !draft && values.length) {
              onChange(values.slice(0, -1))
            }
          }}
          onBlur={commit}
        />
      </div>
    </div>
  )
}
