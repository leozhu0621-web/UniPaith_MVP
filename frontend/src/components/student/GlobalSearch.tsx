import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Search, GraduationCap, Building2, Compass, Target, FolderKanban, Newspaper,
  User, Bookmark, Settings, CornerDownLeft, ArrowRight, Backpack, PenLine,
} from 'lucide-react'
import { searchPrograms, getProgram } from '../../api/programs'
import { searchInstitutions } from '../../api/institutions'
import { useCommandPalette } from '../../stores/command-palette-store'
import { getRecentPrograms, type RecentProgram } from '../../lib/recentPrograms'

// ─── Global command palette (⌘K) ────────────────────────────────────────────
// One omnipresent way to reach any program, school, or surface — the "accessibility
// to features" backbone. A single shared modal, opened from triggers in the nav
// or the ⌘K shortcut. Keyboard-first + ARIA combobox/listbox for accessibility.

interface ProgramResult {
  id: string
  program_name: string
  degree_type?: string | null
  institution_name?: string | null
  institution_city?: string | null
}

interface SchoolResult {
  id: string
  name: string
  city?: string | null
  country?: string | null
  program_count?: number | null
}

const DEGREE_LABEL: Record<string, string> = {
  masters: "Master's", bachelors: "Bachelor's", doctoral: 'Doctorate',
  certificate: 'Certificate', professional: 'Professional',
}

const QUICK_NAV = [
  { label: 'Uni', sub: 'Build your profile with Uni', to: '/s', icon: Compass },
  { label: 'Discover', sub: 'Programs & schools for you', to: '/s/explore', icon: Target },
  { label: 'Connectors', sub: 'Updates from schools you follow', to: '/s/posts', icon: Newspaper },
  { label: 'My Space', sub: 'Your home — what to do next', to: '/s/space', icon: Backpack },
  { label: 'Applications', sub: 'Your portfolio & deadlines', to: '/s/applications', icon: FolderKanban },
  { label: 'Prep', sub: 'Workshops & prompt library', to: '/s/prep', icon: PenLine },
  { label: 'My Profile', sub: 'Your durable record', to: '/s/profile', icon: User },
  { label: 'Saved', sub: 'Programs you bookmarked', to: '/s/saved', icon: Bookmark },
  { label: 'Settings', sub: 'Account & preferences', to: '/s/settings', icon: Settings },
]

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

/** One program row — shared by live search results + "Recently viewed". */
function ProgramRow({ p }: { p: ProgramResult }) {
  return (
    <>
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-secondary">
        <GraduationCap size={16} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-foreground">{p.program_name}</span>
        <span className="block truncate text-xs text-muted-foreground">
          {[p.institution_name, p.institution_city].filter(Boolean).join(' · ')}
          {p.degree_type ? ` · ${DEGREE_LABEL[p.degree_type] ?? p.degree_type}` : ''}
        </span>
      </span>
    </>
  )
}

/** One school row — shared by institution search results. */
function SchoolRow({ s }: { s: SchoolResult }) {
  return (
    <>
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-secondary">
        <Building2 size={16} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-foreground">{s.name}</span>
        <span className="block truncate text-xs text-muted-foreground">
          {[s.city, s.country].filter(Boolean).join(' · ')}
          {s.program_count ? ` · ${s.program_count} program${s.program_count === 1 ? '' : 's'}` : ''}
        </span>
      </span>
    </>
  )
}

/** A trigger placed in the nav — opens the shared palette. */
export function SearchTrigger({ variant = 'bar' }: { variant?: 'bar' | 'icon' }) {
  const setOpen = useCommandPalette((s) => s.setOpen)
  if (variant === 'icon') {
    return (
      <button
        onClick={() => setOpen(true)}
        aria-label="Search programs and schools"
        aria-keyshortcuts={isMac ? 'Meta+K' : 'Control+K'}
        className="ui-btn p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
      >
        <Search size={20} strokeWidth={1.75} />
      </button>
    )
  }
  return (
    <button
      onClick={() => setOpen(true)}
      aria-label="Search programs and schools"
      aria-keyshortcuts={isMac ? 'Meta+K' : 'Control+K'}
      className="ui-btn group hidden lg:flex items-center gap-2 w-64 h-9 pl-3 pr-2 rounded-lg border border-border bg-muted/40 text-muted-foreground text-sm hover:bg-muted hover:border-secondary/40 transition-colors"
    >
      <Search size={16} className="shrink-0" />
      <span className="flex-1 text-left truncate">Search programs, schools…</span>
      <kbd className="shrink-0 hidden xl:inline-flex items-center gap-0.5 px-1.5 h-5 rounded border border-border bg-card text-[10px] font-medium text-muted-foreground">
        {isMac ? '⌘' : 'Ctrl'}K
      </kbd>
    </button>
  )
}

/** The shared palette modal — mount once near the layout root. */
export function CommandPalette() {
  const { open, setOpen, toggle } = useCommandPalette()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [recents, setRecents] = useState<RecentProgram[]>([])
  const debounced = useDebounced(query.trim(), 220)
  const searching = debounced.length >= 2

  // ⌘K / Ctrl+K toggles the palette from anywhere.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        toggle()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [toggle])

  const { data, isFetching: progFetching, isError: progError, refetch: refetchProg } = useQuery({
    queryKey: ['global-search', debounced],
    queryFn: () => searchPrograms({ q: debounced, page_size: 6 }),
    enabled: open && searching,
    staleTime: 60_000,
  })
  const { data: instData, isFetching: instFetching, isError: instError, refetch: refetchInst } = useQuery({
    queryKey: ['global-search-schools', debounced],
    queryFn: () => searchInstitutions({ q: debounced, page_size: 4 }),
    enabled: open && searching,
    staleTime: 60_000,
  })
  const isFetching = progFetching || instFetching
  const isError = progError || instError
  // Flatten everything into one keyboard-navigable command list.
  type Cmd = { key: string; section?: string; run: () => void; render: React.ReactNode; prefetch?: () => void }
  const commands = useMemo<Cmd[]>(() => {
    const items: ProgramResult[] = data?.items ?? []
    const go = (to: string) => () => { setOpen(false); navigate(to) }
    // Warm the program-detail cache on hover/arrow so opening is instant.
    const prefetchProgram = (id: string) => () =>
      qc.prefetchQuery({ queryKey: ['program', id], queryFn: () => getProgram(id), staleTime: 60_000 })
    if (!searching) {
      const recentCmds: Cmd[] = recents.map((p) => ({
        key: `recent-${p.id}`,
        section: 'Recently viewed',
        run: go(`/s/programs/${p.id}`),
        prefetch: prefetchProgram(p.id),
        render: <ProgramRow p={p} />,
      }))
      const navCmds: Cmd[] = QUICK_NAV.map((q) => ({
        key: `nav-${q.to}`,
        section: 'Jump to',
        run: go(q.to),
        render: (
          <>
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-secondary">
              <q.icon size={16} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-foreground">{q.label}</span>
              <span className="block truncate text-xs text-muted-foreground">{q.sub}</span>
            </span>
          </>
        ),
      }))
      return [...recentCmds, ...navCmds]
    }
    const schoolCmds: Cmd[] = ((instData?.items ?? []) as SchoolResult[]).slice(0, 3).map((s) => ({
      key: `school-${s.id}`,
      section: 'Schools',
      run: go(`/s/institutions/${s.id}`),
      render: <SchoolRow s={s} />,
    }))
    const progCmds: Cmd[] = items.map((p) => ({
      key: `prog-${p.id}`,
      section: 'Programs',
      run: go(`/s/programs/${p.id}`),
      prefetch: prefetchProgram(p.id),
      render: <ProgramRow p={p} />,
    }))
    // Escape hatch — always offer a full search on Match.
    progCmds.push({
      key: 'search-all',
      run: go(`/s/explore?q=${encodeURIComponent(debounced)}`),
      render: (
        <>
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-secondary">
            <ArrowRight size={16} />
          </span>
          <span className="min-w-0 flex-1 text-sm font-medium text-foreground">
            Search all programs for “{debounced}”
          </span>
        </>
      ),
    })
    return [...schoolCmds, ...progCmds]
  }, [searching, data, instData, debounced, navigate, setOpen, recents, qc])

  // Reset on open; lock scroll; restore focus on close.
  useEffect(() => {
    if (!open) return
    previouslyFocused.current = document.activeElement as HTMLElement
    document.body.style.overflow = 'hidden'
    setQuery('')
    setActive(0)
    setRecents(getRecentPrograms())
    const t = setTimeout(() => inputRef.current?.focus(), 0)
    return () => {
      clearTimeout(t)
      document.body.style.overflow = ''
      previouslyFocused.current?.focus?.()
    }
  }, [open])

  useEffect(() => { setActive(0) }, [debounced, searching])

  // Prefetch the active result's detail (hover or arrow) so opening feels instant.
  useEffect(() => { commands[active]?.prefetch?.() }, [active, commands])

  if (!open) return null

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { e.preventDefault(); setOpen(false); return }
    if (!commands.length) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => (a + 1) % commands.length) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => (a - 1 + commands.length) % commands.length) }
    else if (e.key === 'Enter') { e.preventDefault(); commands[active]?.run() }
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Search and quick navigation"
    >
      <div className="fixed inset-0 bg-scrim" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-[600px] bg-card text-foreground rounded-xl elev-raised animate-scale-in flex flex-col max-h-[70vh] overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 h-14 border-b border-border shrink-0">
          <Search size={18} className="shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search programs and schools, or jump to a page…"
            aria-label="Search programs and schools"
            role="combobox"
            aria-expanded
            aria-controls="cmd-list"
            aria-activedescendant={commands[active] ? `cmd-${active}` : undefined}
            autoComplete="off"
            spellCheck={false}
            className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground"
          />
          {isFetching && <span className="shrink-0 h-4 w-4 rounded-full border-2 border-border border-t-secondary animate-spin" aria-hidden />}
        </div>

        {/* Results */}
        <ul id="cmd-list" role="listbox" aria-label="Results" className="flex-1 overflow-y-auto p-2">
          {commands.map((cmd, i) => {
            const showHeader = cmd.section && (i === 0 || commands[i - 1].section !== cmd.section)
            return (
              <Fragment key={cmd.key}>
                {showHeader && (
                  <li role="presentation" className="px-2 pt-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {cmd.section}
                  </li>
                )}
                <li
                  id={`cmd-${i}`}
                  role="option"
                  aria-selected={i === active}
                  onClick={() => cmd.run()}
                  onMouseMove={() => setActive(i)}
                  className={`flex items-center gap-3 px-2 py-2 rounded-lg cursor-pointer ${
                    i === active ? 'bg-muted' : ''
                  }`}
                >
                  {cmd.render}
                  {i === active && <CornerDownLeft size={14} className="shrink-0 text-muted-foreground" aria-hidden />}
                </li>
              </Fragment>
            )
          })}
          {searching && isError && (
            <li className="px-3 py-6 text-center text-sm">
              <span className="text-muted-foreground">Couldn&apos;t search right now. </span>
              <button
                type="button"
                onClick={() => { refetchProg(); refetchInst() }}
                className="font-medium text-secondary hover:underline"
              >
                Try again
              </button>
            </li>
          )}
          {searching && !isError && !isFetching && commands.length === 1 && (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              No programs or schools match “{debounced}”. Press Enter to search all.
            </li>
          )}
        </ul>

        {/* Footer hint */}
        <div className="flex items-center gap-4 px-4 h-9 border-t border-border shrink-0 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1"><kbd className="px-1 rounded border border-border bg-muted">↑</kbd><kbd className="px-1 rounded border border-border bg-muted">↓</kbd> navigate</span>
          <span className="flex items-center gap-1"><kbd className="px-1 rounded border border-border bg-muted">↵</kbd> open</span>
          <span className="flex items-center gap-1"><kbd className="px-1 rounded border border-border bg-muted">esc</kbd> close</span>
        </div>
      </div>
    </div>
  )
}
