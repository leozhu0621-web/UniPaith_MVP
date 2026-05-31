import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { useEntitlement } from '../../hooks/useBilling'

// Quiet inline nudge on the Match page (Spec 06 §4.1 — "limited matching" is
// free; expanded matching + reasoning is Plus). Hidden for entitled plans, while
// loading, and when billing is off. The backend also 402s the rationale
// endpoint, so this is the friendly surface for the same boundary.
export default function MatchUpgradeNudge() {
  const { entitled, loading } = useEntitlement('expanded_match')
  if (loading || entitled) return null
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-secondary/5 border border-border text-sm mb-4">
      <Sparkles size={15} className="text-cobalt flex-shrink-0" />
      <span className="text-charcoal">
        You're seeing limited matches. Plus unlocks the full ranked list with reasoning.
      </span>
      <Link
        to="/s/billing"
        className="ml-auto text-cobalt font-semibold hover:underline whitespace-nowrap"
      >
        See plans
      </Link>
    </div>
  )
}
