// One real scholarship (Spec 2026-06-14). award_amount + deadline are verbatim
// source text — shown as-is, never reformatted into false precision.
import { Award, Building2, CalendarClock, ExternalLink, GraduationCap } from 'lucide-react'
import type { Scholarship } from '../../../../api/scholarships'

export default function ScholarshipCard({ s }: { s: Scholarship }) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card p-4">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-secondary/10">
          <Award size={15} className="text-secondary" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold leading-snug text-foreground line-clamp-2">{s.name}</h3>
          {s.organization && (
            <p className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
              <Building2 size={10} className="shrink-0 text-muted-foreground/70" />
              <span className="truncate">{s.organization}</span>
            </p>
          )}
        </div>
      </div>

      {s.purpose && (
        <p className="mt-2 line-clamp-3 text-[12px] leading-relaxed text-muted-foreground">{s.purpose}</p>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        {s.award_amount && s.award_amount !== 'N/A' && (
          <Chip>{s.award_amount}</Chip>
        )}
        {s.award_type && <Chip>{s.award_type}</Chip>}
        {s.deadline && (
          <Chip>
            <CalendarClock size={10} className="text-muted-foreground" /> {s.deadline}
          </Chip>
        )}
        {s.level_of_study && s.level_of_study !== 'N/A' && (
          <Chip>
            <GraduationCap size={10} className="text-muted-foreground" />
            {s.level_of_study.length > 28 ? s.level_of_study.slice(0, 28) + '…' : s.level_of_study}
          </Chip>
        )}
      </div>

      {s.url && (
        <a
          href={s.url}
          target="_blank"
          rel="noopener noreferrer"
          className="ui-btn mt-auto inline-flex items-center justify-center gap-1.5 self-start pt-3 text-xs font-semibold text-secondary hover:underline"
        >
          Apply / details <ExternalLink size={12} />
        </a>
      )}
    </div>
  )
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-muted/60 px-2 py-0.5 text-[11px] font-medium text-foreground">
      {children}
    </span>
  )
}
