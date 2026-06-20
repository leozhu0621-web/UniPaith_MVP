/**
 * Profile-refinement v2 (Ship 2) — the per-tab "Enrich with Uni" panel.
 *
 * A compact card that sits at the top of each non-Basic-info profile tab. It
 * surfaces THAT section's next Prompt-Library signal (scoped via the
 * `section` param) as a guided `EnrichWidget` card, plus a "Talk to Uni" link
 * that opens Uni focused on the section (reuses the `/s?prefill=…` opener path).
 *
 * The panel hides itself when the section has no pending signal — it runs the
 * same section-scoped query the widget uses to decide visibility, so an
 * already-complete section shows nothing rather than an empty card.
 */
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, ArrowRight } from 'lucide-react'

import EnrichWidget from './EnrichWidget'
import { getEnrichNext } from '../../api/enrichment'

/** The Talk-to-Uni opener, one per section. */
const PREFILLS: Record<string, string> = {
  identity:
    "Help me capture who I am — my values, worldview, and what I've noticed about myself.",
  academics:
    "Help me round out my academics and experience — ask me what's missing.",
  goals: 'Help me set and sharpen my goals.',
  needs: 'Help me figure out what I need from a school.',
  preferences:
    'Help me set my preferences — cost, location, and what matters most.',
  strategy: 'Help me develop my strategy.',
}

/** A muted one-liner under the header, per section. */
const BLURBS: Record<string, string> = {
  identity: 'Answer one quick question to deepen your personality profile.',
  academics: 'Answer one quick question to round out your record.',
  goals: 'Answer one quick question to sharpen your goals.',
  needs: 'Answer one quick question to map what you need.',
  preferences: 'Answer one quick question to set what matters most.',
  strategy: 'Answer one quick question to shape your strategy.',
}

export default function EnrichPanel({ section }: { section: string }) {
  const navigate = useNavigate()
  // Same section-scoped query the widget reads — drives visibility so a
  // complete section renders nothing.
  const { data } = useQuery({
    queryKey: ['enrichment', 'next', section],
    queryFn: () => getEnrichNext(1, section),
  })

  if (!data?.items?.length) return null // no pending signal — hide the panel

  const prefill = PREFILLS[section] ?? 'Help me enrich my profile.'
  const blurb = BLURBS[section] ?? 'Answer one quick question to enrich your profile.'

  return (
    <div className="mb-8 rounded-lg border border-border bg-secondary/5 p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="flex items-center gap-1.5 text-sm font-semibold text-secondary">
          <Sparkles size={15} />
          Enrich with Uni
        </span>
        <button
          type="button"
          onClick={() => navigate(`/s?prefill=${encodeURIComponent(prefill)}`)}
          className="flex shrink-0 items-center gap-1 text-sm font-medium text-secondary hover:underline"
        >
          Talk to Uni
          <ArrowRight size={14} />
        </button>
      </div>
      <p className="mb-3 text-sm text-muted-foreground">{blurb}</p>
      <EnrichWidget section={section} />
    </div>
  )
}
