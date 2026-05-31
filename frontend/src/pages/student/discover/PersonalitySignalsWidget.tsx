/**
 * Discover → Personality signals (rail widget for the Profile/Personality
 * layer, spec 19 §6 + §15).
 *
 * Personality facets aren't stored in a typed table, so the backend
 * reconstructs them from the student's profile-session extractions and
 * serves them at /me/discovery/personality-signals. Each facet renders with
 * confidence dots (0–4) so the student can see how sure the system is.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ExternalLink, UserRound } from 'lucide-react'
import clsx from 'clsx'

import { getPersonalitySignals } from '../../../api/discovery'
import Card from '../../../components/ui/Card'
import type { PersonalitySignal } from '../../../types'

// Map the extractor's facet keys to friendly labels. Unknown facets fall
// back to a title-cased version of the key.
const FACET_LABELS: Record<string, string> = {
  peer_style: 'With friends',
  interests: 'Interests',
  passions: 'Passions',
  career_direction: 'Career direction',
  work_style: 'Working style',
  motivation: 'What drives you',
  connection_pref: 'Connection style',
}

function labelFor(facet: string): string {
  return (
    FACET_LABELS[facet] ??
    facet.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  )
}

/** 0–4 dots from a 0–100 confidence. */
function ConfidenceDots({ confidence }: { confidence: number | null }) {
  const filled = confidence == null ? 0 : Math.max(1, Math.round((confidence / 100) * 4))
  return (
    <span
      className="inline-flex items-center gap-0.5"
      title={confidence == null ? 'Confidence unknown' : `${confidence}% confident`}
    >
      {[0, 1, 2, 3].map(i => (
        <span
          key={i}
          className={clsx('h-1.5 w-1.5 rounded-full', i < filled ? 'bg-student' : 'bg-divider')}
        />
      ))}
    </span>
  )
}

export default function PersonalitySignalsWidget() {
  const { data: signals = [], isLoading } = useQuery<PersonalitySignal[]>({
    queryKey: ['personality-signals'],
    queryFn: () => getPersonalitySignals(),
  })

  if (isLoading) {
    return <Card className="text-sm text-student-text">Loading…</Card>
  }

  if (signals.length === 0) {
    return (
      <Card className="text-sm text-student-text space-y-2">
        <div className="flex items-center gap-2 text-student-ink font-medium">
          <UserRound size={14} className="text-cobalt" />
          Personality signals
        </div>
        <p className="italic">
          As you talk about your interests, passions, and how you work with others, I'll
          capture them here.
        </p>
      </Card>
    )
  }

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-student-ink font-medium text-sm">
          <UserRound size={14} className="text-cobalt" />
          Personality signals · {signals.length}
        </div>
        <Link
          to="/s/profile?tab=overview"
          className="text-xs text-cobalt inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>

      <ul className="space-y-2">
        {signals.slice(0, 8).map((s, i) => (
          <li key={`${s.facet}-${i}`} className="space-y-0.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] uppercase tracking-wide text-student-text">
                {labelFor(s.facet)}
              </span>
              <ConfidenceDots confidence={s.confidence} />
            </div>
            <div className="text-sm text-student-ink line-clamp-2">{s.value}</div>
          </li>
        ))}
        {signals.length > 8 && (
          <li className="text-xs text-student-text">+{signals.length - 8} more</li>
        )}
      </ul>
    </Card>
  )
}
