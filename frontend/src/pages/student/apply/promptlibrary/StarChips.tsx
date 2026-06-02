// Spec 42 §3.19 — STAR completeness chips. Lights S·T·A·R·+ as each element is
// present. Used live in the editor (client preview) and on prompt cards (server
// flags).
import clsx from 'clsx'

import { STAR_ELEMENTS, type StarKey } from './constants'

export default function StarChips({
  flags,
  size = 'md',
}: {
  flags: Record<StarKey, boolean>
  size?: 'sm' | 'md'
}) {
  const dim = size === 'sm' ? 'h-5 w-5 text-[10px]' : 'h-6 w-6 text-xs'
  return (
    <div className="flex items-center gap-1" aria-label="STAR completeness">
      {STAR_ELEMENTS.map(el => (
        <span
          key={el.key}
          title={`${el.label}${flags[el.key] ? ' — present' : ' — missing'}`}
          className={clsx(
            'inline-flex items-center justify-center rounded-full font-bold transition-colors',
            dim,
            flags[el.key]
              ? 'bg-success-soft text-success'
              : 'bg-student-mist text-student-text/50',
          )}
        >
          {el.letter}
        </span>
      ))}
    </div>
  )
}
