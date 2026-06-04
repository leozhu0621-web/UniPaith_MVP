// Lightweight recently-viewed program history (localStorage), surfaced in the
// global command palette so re-finding a program is one keystroke away.

export interface RecentProgram {
  id: string
  program_name: string
  institution_name?: string | null
  institution_city?: string | null
  degree_type?: string | null
}

const KEY = 'unipaith_recent_programs'
const MAX = 6

export function getRecentPrograms(): RecentProgram[] {
  try {
    const arr = JSON.parse(localStorage.getItem(KEY) || '[]')
    return Array.isArray(arr) ? arr.filter((x) => x?.id && x?.program_name).slice(0, MAX) : []
  } catch {
    return []
  }
}

export function pushRecentProgram(p: Partial<RecentProgram> | null | undefined): void {
  if (!p?.id || !p.program_name) return
  try {
    const next: RecentProgram[] = [
      {
        id: p.id,
        program_name: p.program_name,
        institution_name: p.institution_name ?? null,
        institution_city: p.institution_city ?? null,
        degree_type: p.degree_type ?? null,
      },
      ...getRecentPrograms().filter((x) => x.id !== p.id),
    ].slice(0, MAX)
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    // storage unavailable (private mode / quota) — recents are best-effort.
  }
}
