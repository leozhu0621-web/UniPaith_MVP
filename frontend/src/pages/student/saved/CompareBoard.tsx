// Saved Compare board (Discover review 2026-06-14 #3) — a sortable side-by-side
// matrix of the saved shortlist, with a balance summary that flags a
// reach-heavy list. Reads only fields on the saved row (no fabrication).
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUp, ArrowDown } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import BandBadge from '../../../components/ui/BandBadge'
import { formatCurrency } from '../../../utils/format'
import type { MatchBand, SavedProgram } from '../../../types'
import { COMPARE_COLUMNS, sortRows, type CompareColumn, type SortDir } from './compareSort'

/** Reach/target/safer counts over the shortlist (self-contained — the page's
 *  BandBalanceBar covers the headline; here we only need the reach-heavy flag). */
function bandCounts(programs: SavedProgram[]) {
  let reach = 0
  let target = 0
  let safer = 0
  let unscored = 0
  for (const p of programs) {
    if (p.band_label === 'reach') reach++
    else if (p.band_label === 'target') target++
    else if (p.band_label === 'safer') safer++
    else unscored++
  }
  return { reach, target, safer, unscored, scored: reach + target + safer }
}

function fmtAcceptance(r?: number | null): string {
  return r == null ? '—' : `${Math.round(r * (r <= 1 ? 100 : 1))}%`
}
function fmtDuration(m?: number | null): string {
  if (!m) return '—'
  return m < 12 ? `${m} mo` : `${(m / 12) % 1 === 0 ? m / 12 : (m / 12).toFixed(1)} yr`
}
function fmtDeadline(iso?: string | null): string {
  // parseISO reads a date-only string as LOCAL midnight; native `new Date`
  // would parse it as UTC and render a day early in the Americas.
  return iso ? format(parseISO(iso), 'MMM d, yyyy') : '—'
}

export default function CompareBoard({ programs }: { programs: SavedProgram[] }) {
  const [sort, setSort] = useState<{ key: CompareColumn; dir: SortDir }>({ key: 'band', dir: 'asc' })
  const rows = sortRows(programs, sort.key, sort.dir)
  const balance = bandCounts(programs)
  const reachHeavy = balance.scored >= 3 && balance.reach > balance.scored / 2

  const onHeader = (key: CompareColumn) =>
    setSort(s => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }))

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted-foreground tabular-nums">
          {balance.reach} reach · {balance.target} target · {balance.safer} safer
          {balance.unscored > 0 && <span className="text-muted-foreground/70"> · {balance.unscored} unscored</span>}
        </span>
        {reachHeavy && (
          <span className="rounded-full bg-warning-soft px-2 py-0.5 font-medium text-warning">
            Reach-heavy — consider a target or safer school
          </span>
        )}
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Saved programs compared by match band, acceptance, tuition, duration, and deadline. Sortable by column.</caption>
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {COMPARE_COLUMNS.map(col => {
                const active = sort.key === col.key
                return (
                  <th
                    key={col.key}
                    scope="col"
                    aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
                    className="px-3 py-2 font-semibold text-muted-foreground whitespace-nowrap"
                  >
                    <button
                      onClick={() => onHeader(col.key)}
                      className="inline-flex items-center gap-1 hover:text-foreground"
                      aria-label={`Sort by ${col.label}${active ? (sort.dir === 'asc' ? ', ascending' : ', descending') : ''}`}
                    >
                      {col.label}
                      {active && (sort.dir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />)}
                    </button>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map(sp => (
              <tr
                key={sp.program_id}
                className="border-b border-border last:border-0 hover:bg-muted/40"
              >
                <td className="px-3 py-2 font-medium max-w-[16rem] truncate">
                  <Link to={`/s/programs/${sp.program_id}`} className="text-foreground hover:text-secondary hover:underline">
                    {sp.program_name ?? 'Program'}
                  </Link>
                </td>
                <td className="px-3 py-2 text-muted-foreground max-w-[12rem] truncate">{sp.institution_name ?? '—'}</td>
                <td className="px-3 py-2">{sp.band_label ? <BandBadge band={sp.band_label as MatchBand} /> : <span className="text-muted-foreground">—</span>}</td>
                <td className="px-3 py-2 text-foreground tabular-nums">{fmtAcceptance(sp.acceptance_rate)}</td>
                <td className="px-3 py-2 text-foreground tabular-nums">{sp.tuition == null ? '—' : sp.tuition === 0 ? 'Funded' : formatCurrency(sp.tuition)}</td>
                <td className="px-3 py-2 text-foreground tabular-nums">{fmtDuration(sp.duration_months)}</td>
                <td className="px-3 py-2 text-foreground tabular-nums">{fmtDeadline(sp.application_deadline)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
