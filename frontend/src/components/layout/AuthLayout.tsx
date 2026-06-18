import Wordmark from '../ui/Wordmark'
import { isDark, useThemeStore } from '../../stores/theme-store'

interface Props { children: React.ReactNode }

export default function AuthLayout({ children }: Props) {
  // Drive the wordmark's color variant from the active theme so the logo stays
  // legible in dark mode (cream lowercase) rather than always rendering cobalt.
  const dark = isDark(useThemeStore(s => s.theme))
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* stagger-list: the logo+tagline lockup settles first, then the card rises behind it (reduce-motion safe). */}
      <div className="w-full max-w-md stagger-list">
        <div className="flex flex-col items-center mb-7">
          {/* UP monogram tile — brand-forward; the self-contained yellow tile reads on
              both cream and navy, so it isn't theme-switched. Decorative: the wordmark
              + sr-only h1 already announce the name. */}
          <img src="/favicon.svg" alt="" aria-hidden="true" className="h-14 w-14 mb-3 drop-shadow-sm" />
          <Wordmark className="h-14 w-auto" variant={dark ? 'dark' : 'light'} />
          <h1 className="sr-only">UniPaith — Everyone&rsquo;s Private College Counselor</h1>
          <p className="mt-3 text-center text-sm tracking-tight text-balance text-foreground/80">
            Everyone&rsquo;s Private College Counselor
          </p>
        </div>
        <div className="bg-card rounded-xl shadow-md border border-border p-7 sm:p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
