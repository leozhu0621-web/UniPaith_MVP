/**
 * Discover → Artifact rail.
 *
 * Right-side panel that switches widget by active track + active layer.
 * On the Profile track the layer drives the widget so the student sees
 * the captures relevant to the question they're being asked right now:
 *   - basic       → BasicSignalsWidget   (GPA, location, education stage)
 *   - personality → IdentitySignalsWidget (placeholder until B-widget lands)
 *   - identity    → IdentitySignalsWidget (values, worldview, self-awareness)
 */
import BasicSignalsWidget from './BasicSignalsWidget'
import GoalStackWidget from './GoalStackWidget'
import IdentitySignalsWidget from './IdentitySignalsWidget'
import NeedsMapWidget from './NeedsMapWidget'
import type { DiscoveryLayer, DiscoveryTrack } from '../../../types'

interface Props {
  track: DiscoveryTrack
  layer?: DiscoveryLayer | null
}

export default function ArtifactRail({ track, layer }: Props) {
  const profileWidget =
    layer === 'basic' ? <BasicSignalsWidget /> : <IdentitySignalsWidget />

  return (
    <aside className="space-y-3">
      {track === 'profile' && profileWidget}
      {track === 'goals' && <GoalStackWidget />}
      {track === 'needs' && <NeedsMapWidget />}
    </aside>
  )
}
