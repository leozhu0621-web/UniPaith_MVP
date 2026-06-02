import { Link } from 'react-router-dom'
import Wordmark from '../ui/Wordmark'

/** Public chrome — Spec/04 §7.3. Browse · Sign in · Get started (gold CTA). */
export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="h-16 flex items-center justify-between px-4 sm:px-8 bg-background border-b border-border flex-shrink-0">
        <Link to="/browse" className="leading-none" aria-label="UniPaith home">
          <Wordmark className="h-7 w-auto" />
        </Link>
        <nav className="flex items-center gap-3 sm:gap-4" aria-label="Public">
          <Link
            to="/browse"
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Browse
          </Link>
          <Link
            to="/pricing"
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Pricing
          </Link>
          <Link
            to="/about"
            className="hidden sm:inline text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            About
          </Link>
          <Link
            to="/goal"
            className="hidden md:inline text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Transparency
          </Link>
          <Link
            to="/login"
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className="ui-btn inline-flex items-center justify-center h-9 px-4 text-sm font-semibold rounded-lg bg-primary text-on-primary hover:brightness-95 transition-colors"
          >
            Get started
          </Link>
        </nav>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border px-4 sm:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-1 text-xs text-muted-foreground">
        <span>Apply once, go anywhere.</span>
        <span>Bias-avoidance is a practice, not a checkbox.</span>
      </footer>
    </div>
  )
}
