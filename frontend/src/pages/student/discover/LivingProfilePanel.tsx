/**
 * The living profile ("what Uni knows") — narrative + three editable sections +
 * gap invitations + a link to the full profile. Rendered inline in the Uni rail
 * (desktop) and inside the ProfileDrawer sheet (mobile). One component, two
 * homes. Read-composed from goal/need/identity; no new backend.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'

import { getLivingProfile } from '../../../api/livingProfile'
import type { LivingProfile, LivingProfileItem } from '../../../api/livingProfile'
import { EditableChip } from './NoticedCard'

function Section({
  title,
  children,
  empty,
}: {
  title: string
  children: React.ReactNode
  empty?: boolean
}) {
  return (
    <section>
      <h3 className="text-eyebrow text-muted-foreground mb-2">{title}</h3>
      {empty ? (
        <p className="text-sm text-muted-foreground italic">Nothing here yet.</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">{children}</div>
      )}
    </section>
  )
}

export default function LivingProfilePanel({
  enabled = true,
  onAsk,
  onNavigate,
}: {
  /** Gate the underlying query (the drawer enables it only when open). */
  enabled?: boolean
  /** Drop a gap-invitation prompt into the conversation. */
  onAsk?: (prompt: string) => void
  /** Called when a link/gap navigates away (e.g. to close the drawer). */
  onNavigate?: () => void
}) {
  const { data, isPending } = useQuery<LivingProfile>({
    queryKey: ['discovery', 'livingProfile'],
    queryFn: getLivingProfile,
    enabled,
  })

  const toItem = (i: LivingProfileItem) => ({ label: i.label, ref: { kind: i.kind, id: i.id } })

  if (isPending || !data) {
    return <p className="text-sm text-muted-foreground">Gathering what Uni has learned…</p>
  }

  return (
    <div className="space-y-5">
      {data.narrative ? (
        <p className="text-sm leading-relaxed text-foreground">{data.narrative}</p>
      ) : (
        <p className="text-sm text-muted-foreground">
          Keep talking with Uni and a picture of you will take shape here.
        </p>
      )}

      <Section title="What lights you up" empty={data.lightsUp.length === 0}>
        {data.lightsUp.map(v => (
          <span
            key={v}
            className="rounded-full bg-card border border-border px-2.5 py-0.5 text-xs text-foreground"
          >
            {v}
          </span>
        ))}
      </Section>

      <Section title="Where you're headed" empty={data.goals.length === 0}>
        {data.goals.map(g => (
          <EditableChip key={g.id} item={toItem(g)} />
        ))}
      </Section>

      <Section title="What you need to thrive" empty={data.needs.length === 0}>
        {data.needs.map(n => (
          <EditableChip key={n.id} item={toItem(n)} />
        ))}
      </Section>

      {data.gaps.length > 0 && (
        <section className="border-t border-border pt-4 space-y-2">
          {data.gaps.map(gap => (
            <button
              key={gap.key}
              type="button"
              onClick={() => {
                onAsk?.(gap.prompt)
                onNavigate?.()
              }}
              className="flex w-full items-center gap-2 text-left text-sm text-secondary hover:underline"
            >
              <Sparkles size={13} className="shrink-0" />
              <span>Uni could understand you better if we talk about {gap.invitation}</span>
              <ArrowRight size={13} className="shrink-0 ml-auto" />
            </button>
          ))}
        </section>
      )}

      <Link
        to="/s/profile"
        onClick={onNavigate}
        className="flex w-full items-center gap-2 border-t border-border pt-4 text-sm text-secondary hover:underline"
      >
        <span>Open your full profile</span>
        <ArrowRight size={13} className="shrink-0 ml-auto" />
      </Link>
    </div>
  )
}
