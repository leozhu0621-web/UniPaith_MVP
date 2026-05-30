import { Link, NavLink, useLocation } from 'react-router-dom'
import Wordmark from '../ui/Wordmark'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

// Public top nav — Spec/04 §7.3.
// [Wordmark]  Browse        Sign in  [ Get started ]   ← Get started is the gold primary CTA.
// Shared across the anonymous browse / program / school pages (§6).
export default function PublicNav() {
  const p = useLocation().pathname
  useDocumentTitle(p.startsWith('/program/') ? 'Program' : p.startsWith('/school/') ? 'School' : 'Browse')
  return (
    <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-divider sticky top-0 z-30">
      <Link to="/browse" className="leading-none" aria-label="UniPaith — Browse">
        <Wordmark className="h-7 w-auto" />
      </Link>
      <nav className="flex items-center gap-5">
        <NavLink
          to="/browse"
          className={({ isActive }) =>
            `text-sm transition-colors ${isActive ? 'text-student-ink font-semibold' : 'text-slate hover:text-student-ink'}`
          }
        >
          Browse
        </NavLink>
        <Link to="/login" className="text-sm text-slate hover:text-student-ink transition-colors">
          Sign in
        </Link>
        <Link
          to="/signup"
          className="px-4 py-2 rounded-lg bg-student text-student-ink text-sm font-semibold hover:bg-student-hover transition-colors"
        >
          Get started
        </Link>
      </nav>
    </header>
  )
}
