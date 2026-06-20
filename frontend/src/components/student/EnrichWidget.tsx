/**
 * AI Structure (Spec 1) — the "enrich your profile" widget.
 *
 * A droppable card (sibling to a program card) that surfaces the next
 * Prompt-Library signal to fill and renders the right input by its ask_kind
 * (reusing the conversation's AnswerChoices for the 0–5 importance slider).
 * On submit it stores the value and advances to the next signal. Render it
 * anywhere — the chat thread, the profile page, the My Space home.
 *
 * Sub-components `KeywordPicker` and `TypeaheadPicker` are named exports so
 * tests can import and exercise them directly.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { Plus, X } from 'lucide-react'

import AnswerChoices from '../../pages/student/discover/AnswerChoices'
import Button from '../ui/Button'
import { getEnrichNext, setEnrichValue, type EnrichItem } from '../../api/enrichment'
import { ACTION_PROMPT, humanizeField } from './enrichHelpers'
import { COMMON_COUNTRIES, COUNTRIES } from './countries'

/** Section-scoped query key so each tab's panel caches independently
 *  (the unscoped home usage keys on 'all'). */
const qk = (section?: string) => ['enrichment', 'next', section ?? 'all'] as const

// ── KeywordPicker ───────────────────────────────────────────────────────────

/**
 * Keyword picker widget (ask_kind === 'keywords').
 *
 * Renders suggestion chips from `options`; each toggles selected (cobalt when
 * on). A dashed "+ Add your own" text input lets the student add custom chips
 * (confirmed on Enter). A Save button submits the string[] of all selected
 * labels (suggestions + custom).
 */
export function KeywordPicker({
  options = [],
  onSubmit,
  disabled,
}: {
  options?: string[]
  onSubmit: (value: string[]) => void
  disabled?: boolean
}) {
  const [selected, setSelected] = useState<string[]>([])
  const [custom, setCustom] = useState<string[]>([])
  const [inputVal, setInputVal] = useState('')

  const toggleSuggestion = (opt: string) => {
    setSelected(s => s.includes(opt) ? s.filter(x => x !== opt) : [...s, opt])
  }

  const addCustom = () => {
    const trimmed = inputVal.trim()
    if (!trimmed) return
    if (!custom.includes(trimmed) && !selected.includes(trimmed)) {
      setCustom(c => [...c, trimmed])
    }
    setInputVal('')
  }

  const removeCustom = (chip: string) => setCustom(c => c.filter(x => x !== chip))

  const allSelected = [...selected, ...custom]

  return (
    <div>
      {/* Suggestion chips */}
      {options.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {options.map(opt => {
            const on = selected.includes(opt)
            return (
              <button
                key={opt}
                type="button"
                disabled={disabled}
                aria-pressed={on}
                onClick={() => toggleSuggestion(opt)}
                className={clsx(
                  'rounded-full border-[1.5px] px-3 py-1 text-sm font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40',
                  on
                    ? 'border-secondary bg-secondary/10 text-secondary'
                    : 'border-border bg-card text-foreground hover:border-secondary/60',
                  disabled && 'pointer-events-none opacity-50',
                )}
              >
                {opt}
              </button>
            )
          })}
        </div>
      )}

      {/* Custom chips (added by user) */}
      {custom.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {custom.map(chip => (
            <span
              key={chip}
              className="flex items-center gap-1 rounded-full border-[1.5px] border-secondary bg-secondary/10 px-3 py-1 text-sm font-medium text-secondary"
            >
              {chip}
              <button
                type="button"
                disabled={disabled}
                aria-label={`Remove ${chip}`}
                onClick={() => removeCustom(chip)}
                className="ml-0.5 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Add-your-own input */}
      <div className="mb-3 flex items-center gap-2">
        <input
          type="text"
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustom() } }}
          placeholder="Add your own…"
          disabled={disabled}
          className="flex-1 rounded-lg border-[1.5px] border-dashed border-border bg-card px-3 py-2 text-sm focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
        />
        <button
          type="button"
          onClick={addCustom}
          disabled={disabled || !inputVal.trim()}
          aria-label="Add keyword"
          className="flex h-9 w-9 items-center justify-center rounded-lg border-[1.5px] border-border bg-card text-muted-foreground transition-colors hover:border-secondary/60 hover:text-secondary disabled:pointer-events-none disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Submit */}
      <div className="flex items-center justify-end">
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || allSelected.length === 0}
          onClick={() => onSubmit(allSelected)}
        >
          Save
        </Button>
      </div>
    </div>
  )
}

// ── TypeaheadPicker ─────────────────────────────────────────────────────────

/**
 * Typeahead picker widget (ask_kind === 'typeahead').
 *
 * Shows COMMON_COUNTRIES as single-select quick-pick chips. A search input
 * filters the full COUNTRIES list; picking a chip or a result submits that
 * string immediately. Common countries are excluded from search results when
 * their query already shows them as chips, to avoid duplicates.
 */
export function TypeaheadPicker({
  onSubmit,
  disabled,
}: {
  onSubmit: (value: string) => void
  disabled?: boolean
}) {
  const [query, setQuery] = useState('')

  // When a query is active the quick-pick chips are hidden, so we include ALL
  // matching countries in the search results (no dedup needed — the chips aren't
  // visible). This guarantees every country is reachable via search.
  const filtered = query.trim()
    ? COUNTRIES.filter(c => c.toLowerCase().includes(query.toLowerCase()))
    : []

  return (
    <div>
      {/* Common-country quick-pick chips (shown when no query) */}
      {!query && (
        <div className="mb-3 flex flex-wrap gap-2">
          {COMMON_COUNTRIES.map(country => (
            <button
              key={country}
              type="button"
              disabled={disabled}
              onClick={() => onSubmit(country)}
              className={clsx(
                'rounded-full border-[1.5px] border-border bg-card px-3 py-1 text-sm font-medium text-foreground transition-colors duration-150 hover:border-secondary/60 hover:text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40',
                disabled && 'pointer-events-none opacity-50',
              )}
            >
              {country}
            </button>
          ))}
        </div>
      )}

      {/* Search input */}
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search countries…"
        disabled={disabled}
        className="mb-2 w-full rounded-lg border-[1.5px] border-border bg-card px-3 py-2 text-sm focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
      />

      {/* Search results */}
      {filtered.length > 0 && (
        <div className="flex flex-col gap-1">
          {filtered.slice(0, 8).map(country => (
            <button
              key={country}
              type="button"
              disabled={disabled}
              onClick={() => onSubmit(country)}
              className="rounded-lg border-[1.5px] border-border bg-card px-3 py-2 text-left text-sm font-medium text-foreground transition-colors hover:border-secondary/60 hover:bg-secondary/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:pointer-events-none disabled:opacity-50"
            >
              {country}
            </button>
          ))}
        </div>
      )}

      {/* No results state */}
      {query.trim() && filtered.length === 0 && (
        <p className="text-xs text-muted-foreground">No matching countries found.</p>
      )}
    </div>
  )
}

// ── SignalInput ─────────────────────────────────────────────────────────────

/** The typed input for one signal. Keyed by field so state resets per signal. */
function SignalInput({
  item,
  onSubmit,
  disabled,
}: {
  item: EnrichItem
  onSubmit: (value: unknown) => void
  disabled?: boolean
}) {
  const [text, setText] = useState('')
  const [min, setMin] = useState('')
  const [max, setMax] = useState('')

  const options = item.options ?? []

  // keywords → keyword picker (string[])
  if (item.ask_kind === 'keywords') {
    return (
      <KeywordPicker
        options={options}
        onSubmit={onSubmit}
        disabled={disabled}
      />
    )
  }

  // typeahead → country typeahead (string)
  if (item.ask_kind === 'typeahead') {
    return (
      <TypeaheadPicker
        onSubmit={onSubmit}
        disabled={disabled}
      />
    )
  }

  // choice / multi → option cards (the picked label is the stored value).
  // When a choice/multi field has no fixed option set (nationality,
  // country_of_residence), fall through to the free-text input below.
  if ((item.ask_kind === 'choice' || item.ask_kind === 'multi') && options.length > 0) {
    return (
      <AnswerChoices
        kind={item.ask_kind}
        options={options}
        onPick={onSubmit}
        disabled={disabled}
        // multi enrichment submits a list so the backend receives proper array
        asList={item.ask_kind === 'multi'}
      />
    )
  }

  if (item.ask_kind === 'scale') {
    // 0–5 importance slider (reuses the conversation widget). `numeric` submits
    // the raw number — the backend scales it 0–10 onto StudentPreference.
    return <AnswerChoices kind="scale" options={[]} numeric onPick={onSubmit} disabled={disabled} />
  }

  if (item.ask_kind === 'range') {
    return (
      <div className="flex items-end gap-2">
        <label className="flex-1 text-sm">
          <span className="text-muted-foreground">Min</span>
          <input
            type="number"
            value={min}
            onChange={(e) => setMin(e.target.value)}
            className="mt-1 w-full rounded-lg border-[1.5px] border-border bg-card px-3 py-2 text-sm focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20"
          />
        </label>
        <label className="flex-1 text-sm">
          <span className="text-muted-foreground">Max</span>
          <input
            type="number"
            value={max}
            onChange={(e) => setMax(e.target.value)}
            className="mt-1 w-full rounded-lg border-[1.5px] border-border bg-card px-3 py-2 text-sm focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20"
          />
        </label>
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || (!min && !max)}
          onClick={() => onSubmit({ min: min ? Number(min) : null, max: max ? Number(max) : null })}
        >
          Set
        </Button>
      </div>
    )
  }

  const inputType = item.ask_kind === 'number' ? 'number' : item.ask_kind === 'date' ? 'date' : 'text'
  return (
    <div className="flex items-end gap-2">
      <input
        type={inputType}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`Your ${humanizeField(item.field).toLowerCase()}`}
        className="flex-1 rounded-lg border-[1.5px] border-border bg-card px-3 py-2 text-sm focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20"
      />
      <Button
        variant="secondary"
        size="sm"
        disabled={disabled || !text}
        onClick={() => onSubmit(inputType === 'number' ? Number(text) : text)}
      >
        {item.action === 'confirm' ? 'Confirm' : 'Save'}
      </Button>
    </div>
  )
}

// ── EnrichWidget ────────────────────────────────────────────────────────────

export default function EnrichWidget({ section }: { section?: string }) {
  const qc = useQueryClient()
  // limit 1 for a section-scoped per-tab panel; the unscoped home usage keeps 3.
  const limit = section ? 1 : 3
  const QK = qk(section)
  const { data, isLoading } = useQuery({ queryKey: QK, queryFn: () => getEnrichNext(limit, section) })
  const mutation = useMutation({
    mutationFn: ({ field, value }: { field: string; value: unknown }) => setEnrichValue(field, value),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })

  if (isLoading) return null
  const item = data?.items?.[0]
  if (!item) return null // nothing left to enrich

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Enrich your profile
        </span>
        {item.tier === 'essential' && (
          <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-[10px] font-medium text-secondary">
            needed to match
          </span>
        )}
      </div>
      <p className="mb-3 text-sm font-medium text-foreground">
        {item.question ? (
          item.question
        ) : (
          <>
            <span>{humanizeField(item.field)}</span>
            <span className="font-normal text-muted-foreground"> · {ACTION_PROMPT[item.action]}</span>
          </>
        )}
      </p>
      <SignalInput
        key={item.field}
        item={item}
        disabled={mutation.isPending}
        onSubmit={(value) => mutation.mutate({ field: item.field, value })}
      />
    </div>
  )
}
