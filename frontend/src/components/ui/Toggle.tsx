import clsx from 'clsx'

// Toggle — Spec/02 switch. Cobalt (secondary) when on; never gold. Semantic
// tokens so it tracks the dark theme. Used across Settings (Spec 21).

interface ToggleProps {
  checked: boolean
  onChange: (value: boolean) => void
  disabled?: boolean
  label: string
  size?: 'sm' | 'md'
  id?: string
}

export default function Toggle({ checked, onChange, disabled, label, size = 'md', id }: ToggleProps) {
  const track = size === 'sm' ? 'h-5 w-9' : 'h-6 w-11'
  const knob = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'
  const shift = size === 'sm' ? (checked ? 'translate-x-4' : 'translate-x-0.5') : checked ? 'translate-x-5' : 'translate-x-0.5'
  return (
    <button
      type="button"
      role="switch"
      id={id}
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={clsx(
        'ui-btn relative inline-flex shrink-0 items-center rounded-pill transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        track,
        checked ? 'bg-secondary' : 'bg-border'
      )}
    >
      <span
        className={clsx(
          'inline-block rounded-full bg-card shadow transition-transform',
          knob,
          shift
        )}
      />
    </button>
  )
}
