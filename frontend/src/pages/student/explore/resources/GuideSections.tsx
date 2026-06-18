// Shared presentational renderer for an authored guide (Spec 2026-06-14).
// Takes a typed section array + a standing disclaimer and renders accessible
// cards. Pure — no data fetching; the content lives in aidGuide.ts / intlGuide.ts.
import { Info } from 'lucide-react'
import type { GuideSection } from './guideTypes'

export default function GuideSections({
  sections,
  disclaimer,
}: {
  sections: GuideSection[]
  disclaimer: string
}) {
  return (
    <div>
      <div className="mb-5 flex items-start gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2.5">
        <Info size={14} className="mt-0.5 shrink-0 text-muted-foreground" aria-hidden />
        <p className="text-xs text-muted-foreground">{disclaimer}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 [&>*]:min-w-0">
        {sections.map(s => {
          const Icon = s.icon
          return (
            <section key={s.id} className="rounded-xl border border-border bg-card p-5">
              <h3 className="flex items-center gap-2 text-sm font-bold text-foreground">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-secondary/10">
                  <Icon size={15} className="text-secondary" aria-hidden />
                </span>
                {s.heading}
              </h3>
              <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">{s.body}</p>
              {s.bullets && s.bullets.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {s.bullets.map((b, i) => (
                    <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-foreground">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-secondary" aria-hidden />
                      <span className="min-w-0">{b}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )
        })}
      </div>
    </div>
  )
}
