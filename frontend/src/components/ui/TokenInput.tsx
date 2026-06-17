import { useState, type KeyboardEvent } from 'react'
import { X } from 'lucide-react'

interface TokenInputProps {
  value: string[]
  onChange: (next: string[]) => void
  placeholder?: string
  /** Optional datalist hints — type-ahead only, never forced. */
  suggestions?: string[]
}

/** Free-form token field — type a phrase and press Enter (or comma) to commit it
 *  as a removable chip; Backspace on an empty input removes the last; the ✕ on a
 *  chip removes that one. The chips speak the same pill language as the
 *  multi-select chips in Preferences. Static — no motion to reduce. The chip row
 *  is a labelled group so assistive tech reads it as one control. */
export default function TokenInput({ value, onChange, placeholder, suggestions }: TokenInputProps) {
  const [draft, setDraft] = useState('')
  const listId = suggestions?.length ? 'token-suggestions' : undefined

  const commit = (raw: string) => {
    const token = raw.trim().slice(0, 80)
    if (token && !value.includes(token)) onChange([...value, token].slice(0, 25))
    setDraft('')
  }
  const removeAt = (i: number) => onChange(value.filter((_, idx) => idx !== i))

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      commit(draft)
    } else if (e.key === 'Backspace' && draft === '' && value.length) {
      e.preventDefault()
      removeAt(value.length - 1)
    }
  }

  return (
    <div
      className="flex flex-wrap items-center gap-1.5 rounded-md border border-border bg-card px-2 py-1.5 focus-within:ring-2 focus-within:ring-ring focus-within:border-secondary transition-colors"
      role="group"
      aria-label="Tokens"
    >
      {value.map((token, i) => (
        <span
          key={`${token}-${i}`}
          className="inline-flex items-center gap-1 rounded-pill border border-secondary bg-secondary/10 px-2.5 py-1 text-[13px] text-foreground"
        >
          {token}
          <button
            type="button"
            onClick={() => removeAt(i)}
            aria-label={`Remove ${token}`}
            className="shrink-0 text-secondary/70 hover:text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 rounded-full"
          >
            <X size={13} aria-hidden="true" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={draft}
        list={listId}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={() => commit(draft)}
        placeholder={value.length ? '' : placeholder}
        className="flex-1 min-w-[8ch] bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none py-0.5"
      />
      {listId && (
        <datalist id={listId}>
          {suggestions!.map(s => (
            <option key={s} value={s} />
          ))}
        </datalist>
      )}
    </div>
  )
}
