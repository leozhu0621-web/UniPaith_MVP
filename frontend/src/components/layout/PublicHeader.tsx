// PublicHeader — used by /browse, /school/:id, /program/:id.
// Spec/02 §7 — wordmark + Log in (tertiary) + Sign up (secondary).

import { Link } from 'react-router-dom'
import Wordmark from '../ui/Wordmark'

export default function PublicHeader() {
  return (
    <header className="bg-card border-b border-border px-4 lg:px-6 py-4 flex items-center justify-between">
      <Link to="/" className="leading-none" aria-label="UniPaith home">
        <Wordmark className="h-7 w-auto" />
      </Link>
      <div className="flex items-center gap-2">
        <Link
          to="/login"
          className="text-[13px] font-bold text-muted-foreground hover:text-foreground motion-fast transition-colors px-3 py-2 rounded-md hover:bg-muted"
        >
          Log in
        </Link>
        <Link
          to="/signup"
          className="text-[13px] font-bold bg-[#2A6BD4] text-[#FCFAF2] hover:bg-[#1F58B5] motion-fast transition-colors px-4 py-2 rounded-[12px] dark:bg-[#6FA0E8] dark:text-[#0A1428] dark:hover:bg-[#9CC0F0]"
        >
          Sign up
        </Link>
      </div>
    </header>
  )
}
