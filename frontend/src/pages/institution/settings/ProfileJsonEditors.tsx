import { useId, useRef, useState, type ReactNode } from 'react'
import clsx from 'clsx'
import { Plus, Trash2 } from 'lucide-react'
import { fieldBaseClasses, fieldStateClasses } from '../../../components/ui/Input'

/**
 * Guided editors for the institution-profile JSONB fields (Spec 22 §3 / gap
 * G-I1). These replace the raw JSON `<textarea>`s on the institution Settings
 * Profile tab — an admin fills labelled rows, never types JSON.
 *
 * Every editor is self-seeding (internal row state from `initial`, emits a
 * rebuilt dict via `onChange`) and **lossless**: any entry it can't model as a
 * row (nested objects in the metric editors, etc.) is stashed in `preserved`
 * and merged back on every change, so editing one field never drops another.
 *
 * The emitted shapes match exactly what `student/institution/InstitutionDetail.tsx`
 * renders (Overview / About tabs):
 *   - social_links / inquiry_routing → flat `{ key: string }`
 *   - support_services → `{ slug: { name, url } }`
 *   - policies        → `{ slug: { summary?, url? } }`  (key drives the displayed name)
 *   - international_info / school_outcomes → `{ key: string | number | string[] }`
 */

let _rid = 0
const nextId = () => `row${++_rid}`

export function slugify(s: string): string {
  return s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
}

function deslug(k: string): string {
  return k.replace(/_/g, ' ').trim().replace(/\b\w/g, (c) => c.toUpperCase())
}

// fieldBaseClasses starts with `w-full`, which would override the per-row width
// utilities (w-44 / flex-1) below — strip it so row layouts size correctly.
const cell = clsx(fieldBaseClasses.replace('w-full', '').trim(), fieldStateClasses(), 'h-9 px-2.5 text-[13px]')

function AddButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 text-[13px] font-medium text-cobalt hover:underline"
    >
      <Plus size={14} /> {label}
    </button>
  )
}

function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Remove row"
      className="p-1.5 text-muted-foreground/70 hover:text-destructive flex-shrink-0"
    >
      <Trash2 size={15} />
    </button>
  )
}

function EmptyHint({ children }: { children: ReactNode }) {
  return <p className="text-xs text-muted-foreground/70 italic">{children}</p>
}

function useDatalistId(): string {
  // useId can contain colons; strip them so the id is a clean `list=` target.
  return 'dl-' + useId().replace(/[^a-zA-Z0-9_-]/g, '')
}

/* ────────────────────────────────────────────────────────────────────────
   PairRowsEditor — flat dict<string,string>.
   Used for social_links (platform→URL) and inquiry_routing (type→destination).
   ──────────────────────────────────────────────────────────────────────── */
type Pair = { id: string; key: string; value: string }

interface PairProps {
  initial: Record<string, unknown> | null | undefined
  onChange: (dict: Record<string, unknown>) => void
  keyLabel: string
  valueLabel: string
  keySuggestions?: string[]
  valuePlaceholder?: string
  valueType?: 'text' | 'url' | 'email'
  addLabel: string
}

function decomposePairs(initial: Record<string, unknown> | null | undefined) {
  const rows: Pair[] = []
  const preserved: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(initial ?? {})) {
    if (v == null) continue
    if (typeof v === 'object') preserved[k] = v
    else rows.push({ id: nextId(), key: k, value: String(v) })
  }
  return { rows, preserved }
}

export function PairRowsEditor({
  initial, onChange, keyLabel, valueLabel, keySuggestions = [], valuePlaceholder, valueType = 'text', addLabel,
}: PairProps) {
  const listId = useDatalistId()
  const seed = useRef<ReturnType<typeof decomposePairs> | null>(null)
  if (seed.current === null) seed.current = decomposePairs(initial)
  const preserved = seed.current.preserved
  const [rows, setRows] = useState<Pair[]>(seed.current.rows)

  const emit = (next: Pair[]) => {
    setRows(next)
    const dict: Record<string, unknown> = { ...preserved }
    for (const r of next) {
      const k = r.key.trim()
      if (!k) continue
      dict[k] = r.value
    }
    onChange(dict)
  }
  const update = (i: number, field: 'key' | 'value', val: string) =>
    emit(rows.map((r, idx) => (idx === i ? { ...r, [field]: val } : r)))
  const add = () => emit([...rows, { id: nextId(), key: '', value: '' }])
  const remove = (i: number) => emit(rows.filter((_, idx) => idx !== i))

  return (
    <div className="space-y-2">
      {rows.length === 0 && <EmptyHint>None added yet.</EmptyHint>}
      {rows.map((r, i) => (
        <div key={r.id} className="flex items-center gap-2">
          <input
            list={keySuggestions.length ? listId : undefined}
            className={clsx(cell, 'w-40 flex-shrink-0')}
            placeholder={keyLabel}
            value={r.key}
            onChange={(e) => update(i, 'key', e.target.value)}
          />
          <input
            type={valueType}
            className={clsx(cell, 'flex-1 min-w-0')}
            placeholder={valuePlaceholder ?? valueLabel}
            value={r.value}
            onChange={(e) => update(i, 'value', e.target.value)}
          />
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
      {keySuggestions.length > 0 && (
        <datalist id={listId}>
          {keySuggestions.map((s) => <option key={s} value={s} />)}
        </datalist>
      )}
      <AddButton onClick={add} label={addLabel} />
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   LinkRowsEditor — dict<slug, {name?, summary?, url?, ...rest}>.
   Used for support_services (name + url) and policies (name + summary + url).
   ──────────────────────────────────────────────────────────────────────── */
type LinkRow = { id: string; name: string; summary: string; url: string; rest: Record<string, unknown> }

interface LinkProps {
  initial: Record<string, unknown> | null | undefined
  onChange: (dict: Record<string, unknown>) => void
  withSummary: boolean
  nameLabel: string
  nameSuggestions?: string[]
  urlLabel?: string
  addLabel: string
}

function decomposeLinks(initial: Record<string, unknown> | null | undefined, withSummary: boolean) {
  const rows: LinkRow[] = []
  const preserved: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(initial ?? {})) {
    if (v == null) continue
    if (Array.isArray(v) || typeof v === 'number' || typeof v === 'boolean') {
      preserved[k] = v
      continue
    }
    if (typeof v === 'string') {
      rows.push({ id: nextId(), name: deslug(k), summary: withSummary ? v : '', url: withSummary ? '' : v, rest: {} })
    } else {
      const { name, summary, url, ...rest } = v as Record<string, unknown>
      rows.push({
        id: nextId(),
        name: typeof name === 'string' ? name : deslug(k),
        summary: typeof summary === 'string' ? summary : '',
        url: typeof url === 'string' ? url : '',
        rest,
      })
    }
  }
  return { rows, preserved }
}

export function LinkRowsEditor({
  initial, onChange, withSummary, nameLabel, nameSuggestions = [], urlLabel = 'Link URL (optional)', addLabel,
}: LinkProps) {
  const listId = useDatalistId()
  const seed = useRef<ReturnType<typeof decomposeLinks> | null>(null)
  if (seed.current === null) seed.current = decomposeLinks(initial, withSummary)
  const preserved = seed.current.preserved
  const [rows, setRows] = useState<LinkRow[]>(seed.current.rows)

  const emit = (next: LinkRow[]) => {
    setRows(next)
    const dict: Record<string, unknown> = { ...preserved }
    for (const r of next) {
      const nm = r.name.trim()
      if (!nm) continue
      const key = slugify(nm) || `entry_${Object.keys(dict).length + 1}`
      const val: Record<string, unknown> = { ...r.rest, name: nm }
      if (withSummary && r.summary.trim()) val.summary = r.summary.trim()
      if (r.url.trim()) val.url = r.url.trim()
      dict[key] = val
    }
    onChange(dict)
  }
  const update = (i: number, field: 'name' | 'summary' | 'url', val: string) =>
    emit(rows.map((r, idx) => (idx === i ? { ...r, [field]: val } : r)))
  const add = () => emit([...rows, { id: nextId(), name: '', summary: '', url: '', rest: {} }])
  const remove = (i: number) => emit(rows.filter((_, idx) => idx !== i))

  return (
    <div className="space-y-2.5">
      {rows.length === 0 && <EmptyHint>None added yet.</EmptyHint>}
      {rows.map((r, i) => (
        <div key={r.id} className="rounded-md border border-border bg-muted/40 p-2.5 space-y-2">
          <div className="flex items-center gap-2">
            <input
              list={nameSuggestions.length ? listId : undefined}
              className={clsx(cell, 'flex-1 min-w-0')}
              placeholder={nameLabel}
              value={r.name}
              onChange={(e) => update(i, 'name', e.target.value)}
            />
            <RemoveButton onClick={() => remove(i)} />
          </div>
          {withSummary && (
            <textarea
              className={clsx(fieldBaseClasses, fieldStateClasses(), 'w-full px-2.5 py-1.5 text-[13px]')}
              rows={2}
              placeholder="Short summary (optional)"
              value={r.summary}
              onChange={(e) => update(i, 'summary', e.target.value)}
            />
          )}
          <input
            type="url"
            className={clsx(cell, 'w-full')}
            placeholder={urlLabel}
            value={r.url}
            onChange={(e) => update(i, 'url', e.target.value)}
          />
        </div>
      ))}
      {nameSuggestions.length > 0 && (
        <datalist id={listId}>
          {nameSuggestions.map((s) => <option key={s} value={s} />)}
        </datalist>
      )}
      <AddButton onClick={add} label={addLabel} />
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   MetricRowsEditor — dict<string, string | number | string[]>, typed per row.
   Used for international_info and school_outcomes (mixed scalar / list values).
   Object-valued entries are preserved untouched.
   ──────────────────────────────────────────────────────────────────────── */
type Kind = 'text' | 'number' | 'list'
type MetricRow = { id: string; key: string; kind: Kind; value: string }

interface MetricProps {
  initial: Record<string, unknown> | null | undefined
  onChange: (dict: Record<string, unknown>) => void
  keySuggestions?: string[]
  addLabel: string
}

function decomposeMetrics(initial: Record<string, unknown> | null | undefined) {
  const rows: MetricRow[] = []
  const preserved: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(initial ?? {})) {
    if (v == null) continue
    if (typeof v === 'number') rows.push({ id: nextId(), key: k, kind: 'number', value: String(v) })
    else if (Array.isArray(v)) rows.push({ id: nextId(), key: k, kind: 'list', value: v.map(String).join(', ') })
    else if (typeof v === 'string') rows.push({ id: nextId(), key: k, kind: 'text', value: v })
    else if (typeof v === 'boolean') rows.push({ id: nextId(), key: k, kind: 'text', value: v ? 'true' : 'false' })
    else preserved[k] = v
  }
  return { rows, preserved }
}

const KIND_PLACEHOLDER: Record<Kind, string> = {
  text: 'Value',
  number: 'e.g. 0.94',
  list: 'comma, separated, values',
}

export function MetricRowsEditor({ initial, onChange, keySuggestions = [], addLabel }: MetricProps) {
  const listId = useDatalistId()
  const seed = useRef<ReturnType<typeof decomposeMetrics> | null>(null)
  if (seed.current === null) seed.current = decomposeMetrics(initial)
  const preserved = seed.current.preserved
  const [rows, setRows] = useState<MetricRow[]>(seed.current.rows)

  const emit = (next: MetricRow[]) => {
    setRows(next)
    const dict: Record<string, unknown> = { ...preserved }
    for (const r of next) {
      const key = slugify(r.key)
      if (!key) continue
      if (r.kind === 'number') {
        if (!r.value.trim()) continue
        const n = Number(r.value)
        dict[key] = Number.isFinite(n) ? n : r.value
      } else if (r.kind === 'list') {
        const arr = r.value.split(',').map((s) => s.trim()).filter(Boolean)
        if (arr.length) dict[key] = arr
      } else {
        if (!r.value.trim()) continue
        dict[key] = r.value
      }
    }
    onChange(dict)
  }
  const update = (i: number, field: 'key' | 'kind' | 'value', val: string) =>
    emit(rows.map((r, idx) => (idx === i ? { ...r, [field]: val } : r)))
  const add = () => emit([...rows, { id: nextId(), key: '', kind: 'text', value: '' }])
  const remove = (i: number) => emit(rows.filter((_, idx) => idx !== i))

  return (
    <div className="space-y-2">
      {rows.length === 0 && <EmptyHint>None added yet.</EmptyHint>}
      {rows.map((r, i) => (
        <div key={r.id} className="flex items-center gap-2">
          <input
            list={keySuggestions.length ? listId : undefined}
            className={clsx(cell, 'w-44 flex-shrink-0')}
            placeholder="Metric key"
            value={r.key}
            onChange={(e) => update(i, 'key', e.target.value)}
          />
          <select
            className={clsx(cell, 'w-[88px] flex-shrink-0 cursor-pointer')}
            value={r.kind}
            onChange={(e) => update(i, 'kind', e.target.value)}
          >
            <option value="text">Text</option>
            <option value="number">Number</option>
            <option value="list">List</option>
          </select>
          <input
            className={clsx(cell, 'flex-1 min-w-0')}
            placeholder={KIND_PLACEHOLDER[r.kind]}
            value={r.value}
            onChange={(e) => update(i, 'value', e.target.value)}
          />
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
      {keySuggestions.length > 0 && (
        <datalist id={listId}>
          {keySuggestions.map((s) => <option key={s} value={s} />)}
        </datalist>
      )}
      <AddButton onClick={add} label={addLabel} />
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   StringListEditor — string[] (one value per row).
   Used for the optional media gallery (S3 URLs).
   ──────────────────────────────────────────────────────────────────────── */
type StrRow = { id: string; value: string }

interface StringListProps {
  initial: string[] | null | undefined
  onChange: (xs: string[]) => void
  placeholder?: string
  addLabel: string
  inputType?: 'text' | 'url'
}

export function StringListEditor({ initial, onChange, placeholder, addLabel, inputType = 'url' }: StringListProps) {
  const seed = useRef<StrRow[] | null>(null)
  if (seed.current === null) seed.current = (initial ?? []).map((v) => ({ id: nextId(), value: v }))
  const [rows, setRows] = useState<StrRow[]>(seed.current)

  const emit = (next: StrRow[]) => {
    setRows(next)
    onChange(next.map((r) => r.value.trim()).filter(Boolean))
  }
  const update = (i: number, val: string) => emit(rows.map((r, idx) => (idx === i ? { ...r, value: val } : r)))
  const add = () => emit([...rows, { id: nextId(), value: '' }])
  const remove = (i: number) => emit(rows.filter((_, idx) => idx !== i))

  return (
    <div className="space-y-2">
      {rows.length === 0 && <EmptyHint>None added yet.</EmptyHint>}
      {rows.map((r, i) => (
        <div key={r.id} className="flex items-center gap-2">
          <input
            type={inputType}
            className={clsx(cell, 'flex-1 min-w-0')}
            placeholder={placeholder}
            value={r.value}
            onChange={(e) => update(i, e.target.value)}
          />
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
      <AddButton onClick={add} label={addLabel} />
    </div>
  )
}
