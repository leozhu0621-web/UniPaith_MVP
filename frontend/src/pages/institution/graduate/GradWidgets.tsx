import { useState } from 'react'
import { X } from 'lucide-react'

/** Compact add-and-remove chip input (research interests, advisor names, areas). */
export function TagInput({
  label,
  values,
  onChange,
  placeholder,
}: {
  label?: string
  values: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}) {
  const [text, setText] = useState('')
  const add = () => {
    const t = text.trim()
    if (t && !values.some(v => v.toLowerCase() === t.toLowerCase())) onChange([...values, t])
    setText('')
  }
  return (
    <div>
      {label && <label className="mb-1 block text-sm font-medium text-foreground">{label}</label>}
      <div className="flex flex-wrap gap-1.5 rounded-lg border border-border bg-background p-2">
        {values.map((v, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 rounded bg-cobalt/10 px-2 py-0.5 text-xs text-cobalt"
          >
            {v}
            <button type="button" onClick={() => onChange(values.filter((_, x) => x !== i))}>
              <X size={11} />
            </button>
          </span>
        ))}
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault()
              add()
            }
          }}
          onBlur={add}
          placeholder={placeholder}
          className="min-w-[8rem] flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
        />
      </div>
    </div>
  )
}
